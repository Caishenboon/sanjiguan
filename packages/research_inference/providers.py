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
    def __init__(self):
        self.key=os.getenv("DEEPSEEK_API_KEY","")
        self.base=os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com").rstrip("/")
        self.model=os.getenv("DEEPSEEK_MODEL","")
        self.timeout=int(os.getenv("LLM_TIMEOUT_SECONDS","90"))
        self.retries=int(os.getenv("LLM_MAX_RETRIES","2"))
    @property
    def configured(self):return bool(self.key and self.model)
    def generate(self,payload:dict)->dict:
        if not self.configured:raise RuntimeError("deepseek_not_configured")
        if time.time()<type(self).circuit_open_until:raise RuntimeError("deepseek_circuit_open")
        safe={k:v for k,v in payload.items() if k not in {"name","email","address","latitude","longitude"}}
        body=json.dumps({"model":self.model,"messages":[{"role":"system","content":
          "以严密之数定其骨，以玄远之辞显其象，以明确之断落其意。只输出约定 JSON，不修改锁定字段。"},
          {"role":"user","content":json.dumps(safe,ensure_ascii=False)}],"response_format":{"type":"json_object"}}).encode()
        request=urllib.request.Request(f"{self.base}/chat/completions",body,
          {"Authorization":f"Bearer {self.key}","Content-Type":"application/json"})
        for attempt in range(self.retries+1):
            try:
                with urllib.request.urlopen(request,timeout=self.timeout) as response:
                    parsed=json.loads(response.read())
                    type(self).failure_count=0
                    return json.loads(parsed["choices"][0]["message"]["content"])
            except urllib.error.HTTPError as exc:
                type(self).failure_count+=1
                if type(self).failure_count>=3:type(self).circuit_open_until=time.time()+60
                if exc.code not in (429,500,502,503,504) or attempt==self.retries:raise
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
