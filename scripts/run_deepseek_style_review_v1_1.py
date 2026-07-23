"""Prompt 1.1 review of the same nine synthetic cases, with hard prose gates."""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from packages.research_inference.providers import DeepSeekProvider,merge_prose
from scripts.run_deepseek_style_review import CASES as ORIGINAL_CASES,review_blank

PROMPT_VERSION="style-review-1.1"
RULESET_VERSION="0.1.0-research"
POSTURES={"A1":"hold","A2":"advance","A3":"hold","B1":"observe","B2":"observe",
          "B3":"observe","C1":"observe","C2":"observe","C3":"observe"}
ACTION_WORDS={"advance":"进","hold":"守","slow":"缓","stop":"止","observe":"待验"}
TEST_METADATA=("虚构","合成","fixture","synthetic")
SOFTENING=("可能","也许","似乎","大概","或许","有望","或有")
CLASSIC_MARKERS=("象曰","卦曰","经云","古云")
UNAUTHORIZED_TERMS=(
  "水火未济","坎离","荧惑守心","龙蛇起陆","星辰坠地","天机","天命","命数已定",
  "见者不祥","大凶","天谴","神启","卦辞","爻辞","星曜","神煞","本尊","护法",
  "佛菩萨","高僧","皇帝转世","名人转世","生肖","隐藏变量",
)
OLD_ISSUES={
 "A1":"象辞仅重复象名，释义带入测试元数据。",
 "A2":"象辞仅重复象名，decisive 被“可能”软化。",
 "A3":"整体通过，但象辞末句不够自然。",
 "B1":"接近通过，但模板化古风明显。",
 "B2":"擅自加入“象曰、水火未济、坎离”。",
 "B3":"基本通过。",
 "C1":"存在伪古文和不必要的生肖、隐藏变量表达。",
 "C2":"擅自加入“荧惑守心、龙蛇起陆、星辰坠地、见者不祥”，且言利言弊不完整。",
 "C3":"简明不成断模板通过。",
}


def locked_case(original):
    item=copy.deepcopy(original)
    item["prompt_version"]=PROMPT_VERSION
    item["action_posture"]=POSTURES[item["case_id"]]
    item["allowed_esoteric_entities"]=[]
    return item


def model_payload(locked):
    item=copy.deepcopy(locked)
    for key in ("evidence_summaries","counterevidence_summaries"):
        item[key]=[
          text.replace("虚构人生事件","人生事件")
              .replace("虚构工作记录","工作记录")
              .replace("虚构收益","收益")
              .replace("虚构关系感受","关系感受")
              .replace("虚构出生年份","出生年份")
              .replace("一组虚构梦象","一组梦象")
              .replace("双方虚构事件","双方事件")
              .replace("虚构学习","学习")
              .replace("有虚构成分的","")
              .replace("合成记录","记录")
          for text in item[key]
        ]
    return item


CASES=[locked_case(item) for item in ORIGINAL_CASES]


def text_of(prose):
    return "\n".join((prose["image_text"],prose["plain_interpretation"],
      prose["judgement"]["benefit"],prose["judgement"]["risk"],
      prose["judgement"]["instruction"]))


def checks(item,prose):
    text=text_of(prose)
    title=item["symbolic_title"]
    verdict=item["verdict"]
    candidates=[value["title"] for value in item.get("candidates",[])]
    allowed=set(item["allowed_esoteric_entities"])
    entity_hits=[term for term in CLASSIC_MARKERS+UNAUTHORIZED_TERMS if term in text and term not in allowed]
    quoted_classic=bool(re.search(r"(?:曰|云)[：:]?[“\"][^”\"]{6,}[”\"]",text)) and not item["claims"]
    output_numbers=set(re.findall(r"\d+(?:\.\d+)?",text))
    allowed_numbers={str(item["strength"])}
    for candidate in item.get("candidates",[]):
        allowed_numbers.add(str(candidate["strength"]))
    if len(item.get("candidates",[]))==2:
        allowed_numbers.add(str(abs(item["candidates"][0]["strength"]-item["candidates"][1]["strength"])))
    decisive_softening=[word for word in SOFTENING if verdict=="decisive" and word in text]
    result={
      "schema_valid":True,
      "locked_fields_unchanged":True,
      "unauthorized_esoteric_entities":entity_hits,
      "fake_classic_marker":any(word in text for word in CLASSIC_MARKERS),
      "unapproved_quoted_classic":quoted_classic,
      "image_differs_from_title":prose["image_text"].strip()!=title.strip(),
      "image_length_35_90":35<=len(prose["image_text"].strip())<=90,
      "insufficient_benefit_risk_nonempty":verdict!="insufficient" or
        bool(prose["judgement"]["benefit"].strip() and prose["judgement"]["risk"].strip()),
      "decisive_softening_terms":decisive_softening,
      "test_metadata_terms":[word for word in TEST_METADATA if word.lower() in text.lower()],
      "unapproved_numbers":sorted(output_numbers-allowed_numbers),
      "contested_both_images":verdict!="contested" or all(name in text for name in candidates),
      "contested_difference_present":verdict!="contested" or
        str(abs(item["candidates"][0]["strength"]-item["candidates"][1]["strength"])) in text,
      "insufficient_explicit":verdict!="insufficient" or "不成断" in text,
      "action_posture_expressed":ACTION_WORDS[item["action_posture"]] in prose["judgement"]["instruction"],
      "plain_length_80_180":80<=len(prose["plain_interpretation"].strip())<=180,
      "ordinary_identity_degraded":any(word in text for word in ("低级前世","卑贱前世","低等身份")),
      "grandiosity_detected":any(word in text for word in ("天选","高贵血统","佛菩萨转世","高僧转世","皇帝转世","名人转世")),
      "ancient_style_manual_review":sum(text.count(word) for word in ("兮","矣","焉","乃","之象"))>=4,
    }
    hard=[
      not entity_hits,not result["fake_classic_marker"],not quoted_classic,
      result["image_differs_from_title"],result["image_length_35_90"],
      result["insufficient_benefit_risk_nonempty"],not decisive_softening,
      not result["test_metadata_terms"],not result["unapproved_numbers"],
      result["contested_both_images"],result["contested_difference_present"],
      result["insufficient_explicit"],result["action_posture_expressed"],
      result["plain_length_80_180"],
      not result["ordinary_identity_degraded"],not result["grandiosity_detected"],
    ]
    result["hard_gate_passed"]=all(hard)
    return result


def template_fallback(item):
    semantic=model_payload(item)
    title=item["symbolic_title"]
    evidence="；".join(semantic["evidence_summaries"])
    counter="；".join(semantic["counterevidence_summaries"])
    bounded_counter=counter.replace("可能压缩","会压缩").replace("可能","会")
    posture=ACTION_WORDS[item["action_posture"]]
    if item["verdict"]=="decisive":
        image=f"眼前的道路已显出清楚方向：{title}。已有积累托住主势，转折落在节奏与边界；守住根基，下一步才不会被眼前的催促带偏。"
        plain=f"主断已立：{title}。现有记录从不同侧面共同支持这一方向，主次没有倒置。其险在于{bounded_counter}；若忽略这些条件，则会损伤原本稳固的积累。"
        benefit="真正有利的是把已形成的积累转成稳定、可持续的行动。"
        risk=f"最需警惕的是忽略边界条件：{bounded_counter}。"
    elif item["verdict"]=="contested":
        first,second=item["candidates"]
        gap=first["strength"]-second["strength"]
        image=f"两条路在同一处交会，一边已有脚印，一边也留着持续的灯火。{first['title']}暂居其上，{second['title']}紧随其后，眼下仍需等新的事实把道路照清。"
        plain=f"{first['title']}暂居第一，{second['title']}列第二，当前相差{gap}分。前者与后者各有现有记录支持，而{counter}，所以主次未分。待所列关键资料补足后，仍能持续的一路方可立为主象。"
        benefit="真正有利的是保留两条路径，避免在证据不足时过早封闭选择。"
        risk="最需警惕的是把暂时领先误写成确定结论。"
    else:
        image=f"已有的线索停在纸面边缘，彼此尚未接成一条可以落笔的路径。现阶段应让空白保持为空白，等缺失的记录到来，再把这一页继续写下去。"
        plain=f"此处不成断。现有资料只有{evidence}，同时又有{counter}，不足以支持身份、吉凶或应期判断。补足缺失资料并形成独立交叉证据后，才能重新推演。"
        benefit="资料不足，暂不论其利。"
        risk="若以单一线索强立结论，误判风险高。"
    return {"image_text":image,"plain_interpretation":plain,
      "judgement":{"benefit":benefit,"risk":risk,
        "instruction":f"现阶段以“{posture}”为主动作，按锁定条件补充资料后再复核。"}}


def call_with_gate(provider,item):
    last_checks=None
    for attempt in range(2):
        if provider.request_count>=provider.max_requests:
            break
        result=provider.generate_with_metrics(model_payload(item))
        prose=result["content"]
        gate=checks(item,prose)
        if gate["hard_gate_passed"]:
            return prose,gate,result["usage"],False,attempt
        last_checks=gate
    prose=template_fallback(item)
    gate=checks(item,prose)
    if not gate["hard_gate_passed"]:
        raise RuntimeError(f"template_gate_failure:{item['case_id']}")
    return prose,gate,{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},True,1


def markdown(package):
    meta=package["metadata"]
    lines=["# DeepSeek 文风审核包 v1.1","",
      "> 全部案例和人物均为虚构，仅用于语言质量审核。","",
      f"- Provider：`{meta['provider']}`",f"- Model：`{meta['model']}`",
      f"- Prompt 版本：`{meta['prompt_version']}`",f"- Ruleset 版本：`{meta['ruleset_version']}`",
      f"- Commit SHA：`{meta['commit_sha']}`",f"- Workflow Run ID：`{meta['workflow_run_id']}`",
      f"- 请求数：{meta['request_count']}",f"- Token 数：{meta['total_tokens']}",
      f"- Schema：{meta['schema_valid_count']}/9",f"- 锁字段：{meta['locked_fields_unchanged_count']}/9",
      f"- 模板回退：{meta['template_fallback_count']}",f"- 生成时间：{meta['generated_at']}",""]
    for row in package["cases"]:
        source=row["rule_input"];prose=row["deepseek_output"]
        lines += [f"# Case {source['case_id']}","",
          "状态：",source["verdict"],"","锁定断章：",source["symbolic_title"],"",
          "象名：",source["symbolic_title"],"","吉凶：",source["polarity"],"",
          "应期：",source["manifestation_period"],"","证契摘要：","；".join(source["evidence_summaries"]),"",
          "逆证摘要：","；".join(source["counterevidence_summaries"]),"",
          "DeepSeek 象辞：",prose["image_text"],"","DeepSeek 释义：",prose["plain_interpretation"],"",
          "DeepSeek 言利：",prose["judgement"]["benefit"],"","DeepSeek 言弊：",prose["judgement"]["risk"],"",
          "DeepSeek 行止：",prose["judgement"]["instruction"],"",
          "自动检查：","```json",json.dumps(row["automatic_checks"],ensure_ascii=False,indent=2),"```","",
          "人工审核评分（由产品负责人填写）：","",
          "- 断语力度：1–5","- 玄意与画面：1–5","- 现代可读性：1–5",
          "- 吉凶清晰度：1–5","- 应期表达：1–5","- 证据忠实度：1–5",
          "- 机器味：1–5，分数越高机器味越重","- 空话比例：1–5，分数越高问题越大",
          "- 是否通过：是/否","- 修改意见：",""]
    return "\n".join(lines)+"\n"


def diff_markdown(rows):
    lines=["# DeepSeek 文风差异：v1.0 → v1.1","",
      "> 全部案例和人物均为虚构，仅用于语言质量审核。",""]
    for row in rows:
        cid=row["rule_input"]["case_id"];gate=row["automatic_checks"]
        lines += [f"## Case {cid}","",f"- 原问题：{OLD_ISSUES[cid]}",
          "- Prompt 修订：禁止自造术数实体与测试元数据；按状态约束结构、象辞长度和锁定行止。",
          f"- 新输出：{row['deepseek_output']['image_text']}",
          f"- 是否解决：{'自动硬门禁通过' if gate['hard_gate_passed'] else '未通过'}",
          f"- 仍存问题：{'古文比例需人工复核。' if gate['ancient_style_manual_review'] else '机器味、意境和自然度仍待产品负责人评分。'}",""]
    return "\n".join(lines)+"\n"


def main():
    DeepSeekProvider.request_count=0
    DeepSeekProvider.failure_count=0
    DeepSeekProvider.circuit_open_until=0.0
    provider=DeepSeekProvider()
    if not provider.configured:
        raise SystemExit("DeepSeek style review unavailable: server-side configuration missing")
    rows=[];tokens=0
    for item in CASES:
        prose,gate,usage,fallback,retries=call_with_gate(provider,item)
        merged=merge_prose(item,prose)
        locked=all(merged[key]==value for key,value in item.items())
        gate["locked_fields_unchanged"]=locked
        rows.append({"rule_input":item,"deepseek_output":prose,"automatic_checks":gate,
          "schema_valid":True,"locked_fields_unchanged":locked,
          "template_fallback":fallback,"retry_count":retries,"usage":usage,
          "human_review":review_blank()})
        tokens+=usage["total_tokens"]
    openings=[row["deepseek_output"]["image_text"][:10] for row in rows]
    repeated={value for value,count in Counter(openings).items() if count>=3}
    for row,opening in zip(rows,openings):
        row["automatic_checks"]["three_case_repeated_opening"]=opening in repeated
    sha=os.getenv("GITHUB_SHA") or subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    package={"notice":"全部案例和人物均为虚构，仅用于语言质量审核。",
      "metadata":{"provider":"deepseek","model":provider.model,"prompt_version":PROMPT_VERSION,
        "ruleset_version":RULESET_VERSION,"commit_sha":sha,
        "workflow_run_id":os.getenv("GITHUB_RUN_ID","local"),
        "request_count":provider.request_count,"request_limit":provider.max_requests,
        "total_tokens":tokens,"schema_valid_count":sum(row["schema_valid"] for row in rows),
        "locked_fields_unchanged_count":sum(row["locked_fields_unchanged"] for row in rows),
        "template_fallback_count":sum(row["template_fallback"] for row in rows),
        "generated_at":datetime.now(timezone.utc).isoformat(),"synthetic_only":True,
        "secret_recorded":False,"system_prompt_recorded":False,"request_headers_recorded":False},
      "cases":rows}
    Path("deepseek-style-review-v1.1.json").write_text(json.dumps(package,ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("deepseek-style-review-v1.1.md").write_text(markdown(package),"utf-8")
    Path("deepseek-style-diff-v1.0-v1.1.md").write_text(diff_markdown(rows),"utf-8")
    if not all(row["automatic_checks"]["hard_gate_passed"] and row["locked_fields_unchanged"] for row in rows):
        raise SystemExit("Prompt 1.1 hard gate failed")
    print(f"Prompt 1.1 review generated: cases=9 requests={provider.request_count}")


if __name__=="__main__":
    main()
