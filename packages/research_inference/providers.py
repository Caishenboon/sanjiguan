from __future__ import annotations
import json,os,time,urllib.error,urllib.request

LOCKED_FIELDS={"verdict","polarity","strength","rank","status","symbolic_title",
"manifestation_period","dominant_side","evidence_ids","counterevidence_ids","rule_ids",
"knowledge_chunk_ids","ruleset_version","action_posture","allowed_esoteric_entities"}

STYLE_REVIEW_1_1_PROMPT = """你是三际观的象辞与释义引擎。三际枢已经完成判断、排序、吉凶、强度、应期与证据锁定。你只能为既定结论赋辞，不得改变、补造或软化结论。
以严密之数定其骨，以玄远之辞显其象，以明确之断落其意。玄意必须生于已定之象，不得生于模型自造的术数符号。象辞可以原创，但不得仿冒经典，不得借不存在的卦、星、神煞、偈颂增添神秘感。
除非 allowed_esoteric_entities 明确列出，否则不得新增卦名、卦辞、爻辞、象曰、卦曰、经云、古云、星曜、神煞、天干地支、五行或四柱判断、中阴类型、本尊、护法、佛菩萨、高僧、历史人物、前世时代地域、灾异或凶兆。
image_text 必须以锁定象名和证据为根，形成可感知的画面，暗含主势与转折；使用现代可读文学中文，35至90个汉字；不得复述标题、写四字标题、廉价古风对联或生硬比喻。
plain_interpretation 使用80至180个汉字，依次写明结论、依据、风险或待验条件；不得逐字复述证据，不得出现测试元数据、隐藏变量、生肖或夸大身份。
decisive：第一句明确重申主断，不得使用可能、也许、似乎、大概、或许、有望、或有；风险改用“若……则……”“其险在于……”等有边界条件句。
contested：依次写第一候选、第二候选、分差、双方依据、不能成断的原因和决定胜负的新证据；不得擅自命卦、制造绝对冲突或给出不可逆决定。
insufficient：明确写“此处不成断”，说明缺失、冲突与补充条件；不写吉凶、具体应期、身份或凶兆；benefit 写资料不足暂不论利，risk 写强断的误判风险。
judgement 的 benefit 回答真正有利之处，risk 回答最需警惕之处，instruction 必须把锁定 action_posture 写成明确动作：advance=进、hold=守、slow=缓、stop=止、observe=待验。不得自行改变动作。
只输出 JSON，顶层只能有 image_text、plain_interpretation、judgement；judgement 只能有 benefit、risk、instruction。不得引用或伪造经典，不得生成宏大身份。
风格方向仅供约束，禁止逐字复制：
成断：旧卷随行多年，所问之事始终如一；卷帙渐成，路由求法转向传法，火候未足时守深不争广。
相争：两路皆有来处尚未分主次；分别说明双方证据与分差，待关键结构稳定后以仍能持续者为主。
不成断：反复意象若与近期接触相合，只能入卷不能独立成证；待更早记录或独立证契后再议。"""


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
        if safe.get("prompt_version")=="style-review-1.1":
            system=STYLE_REVIEW_1_1_PROMPT
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
      "claims","ruleset_version","prompt_version","candidates","missing_reasons",
      "action_posture","allowed_esoteric_entities"}
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
