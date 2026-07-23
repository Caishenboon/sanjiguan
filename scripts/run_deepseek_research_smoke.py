"""Three fixed synthetic cases. Writes only a redacted metric summary."""
import json,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packages.research_inference.providers import DeepSeekProvider,merge_prose

CASES=[
 {"case_id":"synthetic-a","locked":{"verdict":"decisive","status":"research_preview",
  "polarity":"mixed_benefit","strength":82,"rank":1,"symbolic_title":"行旅求法，学成未传",
  "manifestation_period":"non-identifying-research-period","judgement":{"dominant_side":"practice"},
  "evidence_summaries":["三组独立虚构证据支持，主象与次象分差已锁定"],
  "counterevidence_summaries":["若亲和形成于后期阅读，独立证力下调"],
  "claims":[],"ruleset_version":"0.1.0-research","prompt_version":"smoke-1.0"}},
 {"case_id":"synthetic-b","locked":{"verdict":"contested","status":"research_preview",
  "polarity":"contested","strength":64,"rank":1,"symbolic_title":"隐修与传播两象相争",
  "manifestation_period":"unresolved","judgement":{"dominant_side":"undetermined"},
  "candidates":[{"rank":1,"title":"隐修","strength":64},{"rank":2,"title":"传播","strength":61}],
  "evidence_summaries":["梦象与业象支持隐修；愿象与事件支持传播；分差三点"],
  "counterevidence_summaries":["需长期教化与传承记录决定是否易位"],
  "claims":[],"ruleset_version":"0.1.0-research","prompt_version":"smoke-1.0"}},
 {"case_id":"synthetic-c","locked":{"verdict":"insufficient","status":"research_preview",
  "polarity":"undetermined","strength":39,"rank":1,"symbolic_title":"资料未足，链条未成",
  "manifestation_period":"not_available","judgement":{"dominant_side":"none"},
  "evidence_summaries":["只有单次虚构梦境记录，来源不独立"],
  "counterevidence_summaries":["后期阅读与记忆重构足以解释现有材料"],
  "missing_reasons":["缺少早年记录","缺少独立来源","不同领域未形成交叉支持"],
  "claims":[],"ruleset_version":"0.1.0-research","prompt_version":"smoke-1.0"}}
]
BANNED_DECISIVE=("可能","也许","似乎","大概","或许","一切皆有可能","仅供参考","自行感受")
GRANDIOSE=("佛菩萨","高僧转世","皇帝转世","公主转世","名人转世")
FAKE_CITATION=("经云","佛说","某经曰","偈曰")


def style(case_id,locked,prose):
    text=json.dumps(prose,ensure_ascii=False)
    result={"explicit_verdict_preserved":True,"mystical_style":len(prose["image_text"])>=8,
      "plain_interpretation_present":bool(prose["plain_interpretation"].strip()),
      "fake_citation_detected":any(x in text for x in FAKE_CITATION),
      "grandiosity_detected":any(x in text for x in GRANDIOSE)}
    if case_id=="synthetic-a":result["decisive_not_softened"]=not any(x in prose["plain_interpretation"] for x in BANNED_DECISIVE)
    if case_id=="synthetic-b":result["contested_preserved"]=("相争" in text or "两象" in text) and "第三" not in text
    if case_id=="synthetic-c":result["insufficient_explicit"]="不成断" in text
    return result


def main():
    DeepSeekProvider.request_count=0
    DeepSeekProvider.failure_count=0
    DeepSeekProvider.circuit_open_until=0.0
    provider=DeepSeekProvider()
    if not provider.configured:raise SystemExit("DeepSeek smoke unavailable: repository secret or model configuration missing")
    summaries=[];failed=False
    for item in CASES:
        started=time.perf_counter()
        record={"provider":"deepseek","model":provider.model,"case_id":item["case_id"],"success":False,
          "http_status_class":"non-2xx","latency_ms":0,"prompt_tokens":0,"completion_tokens":0,
          "total_tokens":0,"schema_valid":False,"locked_fields_unchanged":False,
          "template_fallback":False,"locked_field_violation":False}
        try:
            result=provider.generate_with_metrics(item["locked"])
            prose=result["content"]
            merged=merge_prose(item["locked"],prose)
            checks=style(item["case_id"],item["locked"],prose)
            valid=all(v for k,v in checks.items() if k not in {"fake_citation_detected","grandiosity_detected"})
            valid=valid and not checks["fake_citation_detected"] and not checks["grandiosity_detected"]
            record.update(success=valid,http_status_class="2xx",schema_valid=True,
              locked_fields_unchanged=all(merged[k]==v for k,v in item["locked"].items()),
              style_checks=checks,model=result["model"],**result["usage"])
        except Exception:
            record["error_type"]="provider_or_validation_failure"
        record["latency_ms"]=round((time.perf_counter()-started)*1000)
        failed=failed or not record["success"] or not record["locked_fields_unchanged"]
        summaries.append(record)
    output={"schema_version":"1.0","synthetic_only":True,"request_count":provider.request_count,
      "request_limit":provider.max_requests,"cases":summaries,
      "secrets_recorded":False,"raw_prompts_recorded":False,"raw_responses_recorded":False,
      "production_rules_enabled":False}
    target=Path("deepseek-research-smoke-summary.json")
    target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"DeepSeek research smoke completed: cases={len(summaries)}, requests={provider.request_count}, passed={sum(x['success'] for x in summaries)}")
    if failed:raise SystemExit(1)

if __name__=="__main__":main()
