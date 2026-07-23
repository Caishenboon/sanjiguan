from __future__ import annotations
import json,os,time,urllib.error,urllib.request

LOCKED_FIELDS={"verdict","polarity","strength","rank","status","symbolic_title",
"manifestation_period","dominant_side","evidence_ids","counterevidence_ids","rule_ids",
"knowledge_chunk_ids","ruleset_version"}


class FakeProvider:
    name="fake"
    def generate(self,payload:dict)->dict:
        return {"image_text":"其象可观，其断有据。","plain_interpretation":"此为虚构研究案例的模板解释。",
                "judgement":{"benefit":"保留可核证部分","risk":"避免身份化推断","instruction":"补充逆证后复核"}}


class TemplateProvider(FakeProvider):
    name="template"


class DeepSeekProvider:
    name="deepseek"
    failure_count=0
    circuit_open_until=0.0
    request_count=0
    def __init__(self):
        self.key=os.getenv("DEEPSEEK_API_KEY","")
        self.base=os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com").rstrip("/")
        self.model=os.getenv("DEEPSEEK_MODEL","")
        self.timeout=int(os.getenv("LLM_TIMEOUT_SECONDS","90"))
        self.retries=int(os.getenv("LLM_MAX_RETRIES","2"))
        self.max_tokens=int(os.getenv("LLM_MAX_TOKENS","900"))
        self.max_requests=int(os.getenv("LLM_MAX_REQUESTS","6"))
    @property
    def configured(self):return bool(self.key and self.model)
    def generate(self,payload:dict)->dict:
        return self.generate_with_metrics(payload)["content"]

    def generate_with_metrics(self,payload:dict)->dict:
        if not self.configured:raise RuntimeError("deepseek_not_configured")
        if time.time()<type(self).circuit_open_until:raise RuntimeError("deepseek_circuit_open")
        if type(self).request_count>=self.max_requests:raise RuntimeError("deepseek_request_budget_exhausted")
        safe=sanitize_prose_payload(payload)
        system=("你是三际观的象辞与释义引擎。三际枢已经完成判断、排序、吉凶、强度、应期与证据锁定。"
          "你只能为既定结论赋辞，不得改变、补造或软化结论。"
          "以严密之数定其骨，以玄远之辞显其象，以明确之断落其意。"
          "只输出 JSON，且只能含 image_text、plain_interpretation、judgement；"
          "judgement 只能含 benefit、risk、instruction。不得引用或伪造经典，不得生成宏大身份。"
          "若 verdict=decisive，结论不得使用“可能、或许、倾向、似乎、大概”等模糊词；"
          "若 verdict=contested，必须并列保留第一、第二候选及其差值，不得生成第三结论或改写成确定结论；"
          "若 verdict=insufficient，plain_interpretation 必须明确包含“此处不成断”，说明输入列出的"
          "缺失原因，不得补写身份、年代、地域或时期。")
        body=json.dumps({"model":self.model,"messages":[{"role":"system","content":system},
          {"role":"user","content":json.dumps(safe,ensure_ascii=False)}],
          "response_format":{"type":"json_object"},"max_tokens":self.max_tokens,
          "stream":False,"thinking":{"type":"disabled"}}).encode()
        request=urllib.request.Request(f"{self.base}/chat/completions",body,
          {"Authorization":f"Bearer {self.key}","Content-Type":"application/json"})
        for attempt in range(self.retries+1):
            type(self).request_count+=1
            try:
                with urllib.request.urlopen(request,timeout=self.timeout) as response:
                    parsed=json.loads(response.read())
                    type(self).failure_count=0
                    content=json.loads(parsed["choices"][0]["message"]["content"])
                    validate_prose(content)
                    usage=parsed.get("usage") or {}
                    return {"content":content,"model":parsed.get("model",self.model),
                      "usage":{"prompt_tokens":usage.get("prompt_tokens",0),
                      "completion_tokens":usage.get("completion_tokens",0),
                      "total_tokens":usage.get("total_tokens",0)}}
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,KeyError,json.JSONDecodeError) as exc:
                type(self).failure_count+=1
                if type(self).failure_count>=3:type(self).circuit_open_until=time.time()+60
                retryable=not isinstance(exc,urllib.error.HTTPError) or exc.code in (429,500,502,503,504)
                if not retryable or attempt==self.retries:raise RuntimeError("deepseek_provider_failure") from None
                time.sleep(2**attempt)


class EmbeddingProvider:
    mode="disabled"
    model_id=None
    dimensions=None
    def embed(self,texts:list[str])->list[list[float]]:
        raise RuntimeError("embedding_disabled")


def merge_prose(locked:dict,prose:dict)->dict:
    if LOCKED_FIELDS & set(prose):
        raise ValueError("llm_attempted_locked_field_override")
    allowed={"image_text","plain_interpretation","judgement"}
    if set(prose)-allowed:raise ValueError("llm_output_not_allowlisted")
    return {**locked,"prose":prose}


def sanitize_prose_payload(payload:dict)->dict:
    allowed={"verdict","polarity","strength","rank","status","symbolic_title",
      "manifestation_period","judgement","evidence_summaries","counterevidence_summaries",
      "claims","ruleset_version","prompt_version","candidates","missing_reasons"}
    return {key:payload[key] for key in allowed if key in payload}


def validate_prose(prose:dict):
    allowed={"image_text","plain_interpretation","judgement"}
    if not isinstance(prose,dict) or set(prose)-allowed or not {"image_text","plain_interpretation","judgement"}<=set(prose):
        raise ValueError("invalid_prose_schema")
    judgement=prose["judgement"]
    if not isinstance(judgement,dict) or set(judgement)!={"benefit","risk","instruction"}:
        raise ValueError("invalid_judgement_schema")
    if any(not isinstance(prose[key],str) or not prose[key].strip() for key in ("image_text","plain_interpretation")):
        raise ValueError("empty_prose_field")
