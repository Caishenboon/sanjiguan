"""Generate a reviewable prose pack from nine fixed, wholly synthetic cases."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_inference.providers import DeepSeekProvider, merge_prose

PROMPT_VERSION = "style-review-1.0"
RULESET_VERSION = "0.1.0-research"
OUTPUT_JSON = Path("deepseek-style-review.json")
OUTPUT_MD = Path("deepseek-style-review.md")


def case(case_id, verdict, polarity, strength, title, period, dominant, evidence,
         counterevidence, candidates=None, missing=None):
    value = {
        "case_id": case_id,
        "verdict": verdict,
        "status": "research_preview",
        "polarity": polarity,
        "strength": strength,
        "rank": 1,
        "symbolic_title": title,
        "manifestation_period": period,
        "judgement": {"dominant_side": dominant},
        "evidence_summaries": evidence,
        "counterevidence_summaries": counterevidence,
        "claims": [],
        "ruleset_version": RULESET_VERSION,
        "prompt_version": PROMPT_VERSION,
    }
    if candidates:
        value["candidates"] = candidates
    if missing:
        value["missing_reasons"] = missing
    return value


CASES = [
    case("A1", "decisive", "benefit_with_risk", 82, "行旅求法，学成待传",
         "中程积累后进入传播期", "修学传播",
         ["多次异地求学与长期整理知识的合成记录相互印证", "虚构人生事件显示先求学、后承担讲授"],
         ["传播尚缺稳定受众，过早扩张会损害修学深度"]),
    case("A2", "decisive", "steady_benefit", 78, "百工磨器，日积成业",
         "近程守成，中程见效", "工匠积累",
         ["虚构工作记录连续多年聚焦同一门手艺", "收入改善与返工率下降同步出现"],
         ["设备更新与体力负担可能压缩积累速度"]),
    case("A3", "decisive", "mixed_benefit", 75, "愿缘牵引，情执成险",
         "关系承诺形成后的三年内", "共同愿行",
         ["双方虚构事件均显示共同目标能稳定关系", "困难时期仍能维持实际协作"],
         ["控制欲与旧有依恋在压力下反复出现", "若只谈情感而不落实边界，风险上升"]),
    case("B1", "contested", "contested", 64, "隐修与传播，两象相争",
         "待长期教化记录后再定", "未决",
         ["梦象与独处习惯支持隐修", "愿象与公开分享经历支持传播"],
         ["目前分差仅三点，缺少持续传承或长期闭关记录"],
         [{"rank": 1, "title": "隐修", "strength": 64},
          {"rank": 2, "title": "传播", "strength": 61}]),
    case("B2", "contested", "contested", 62, "济人之术与持家之责相争",
         "家庭照护结构稳定后复核", "未决",
         ["虚构学习与志愿服务记录支持医者方向", "多年照护事件支持家庭承担"],
         ["两者时间资源直接冲突，当前分差二点"],
         [{"rank": 1, "title": "家庭承担", "strength": 62},
          {"rank": 2, "title": "医者", "strength": 60}]),
    case("B3", "contested", "contested", 59, "商旅迁徙与守土经营相争",
         "下一轮经营周期结束后复核", "未决",
         ["异地交易的虚构收益支持商旅迁徙", "本地客户复购与土地投入支持守土经营"],
         ["现金流波动使迁徙优势未稳，固定资产又限制转向"],
         [{"rank": 1, "title": "商旅迁徙", "strength": 59},
          {"rank": 2, "title": "守土经营", "strength": 57}]),
    case("C1", "insufficient", "undetermined", 20, "生时阙失，界线未明",
         "不可提供", "无",
         ["仅有虚构出生年份，月份、日期与时刻均缺失"],
         ["缺失范围跨越多个关键边界，任何单一结论都会越过证据"],
         missing=["缺少出生月日", "缺少出生时刻", "缺少地点与历史时区"]),
    case("C2", "insufficient", "undetermined", 34, "梦象一端，接触史相冲",
         "不可提供", "无",
         ["一组虚构梦象反复出现相同场景"],
         ["现实接触史显示相同意象可能来自近期阅读与展览"],
         missing=["缺少早于现实接触的独立记录", "缺少不同领域交叉证据"]),
    case("C3", "insufficient", "undetermined", 28, "一面之辞，久事无征",
         "不可提供", "无",
         ["只有一方提供的虚构关系感受"],
         ["没有对方同意记录，也没有长期共同事件支持"],
         missing=["缺少双方同意的资料", "缺少长期事件", "缺少独立逆证核对"]),
]

ESCAPE = ("可能", "也许", "似乎", "大概", "或许", "仅供参考", "自行感受")
FAKE_CITATION = ("经云", "佛说", "某经曰", "偈曰", "古经有云")
GRANDIOSE = ("天选", "高贵血统", "佛菩萨转世", "高僧转世", "皇帝转世", "名人转世")
OVERMYSTICAL = ("前尘", "宿命", "灵魂", "宇宙")
LOW_STATUS = ("低级前世", "卑贱前世", "低等身份")


def text_of(prose):
    return "\n".join([
        prose["image_text"], prose["plain_interpretation"],
        prose["judgement"]["benefit"], prose["judgement"]["risk"],
        prose["judgement"]["instruction"],
    ])


def automatic_checks(item, prose):
    text = text_of(prose)
    verdict = item["verdict"]
    candidates = [value["title"] for value in item.get("candidates", [])]
    checks = {
        "decisive_main_verdict_preserved": verdict != "decisive" or not any(x in prose["plain_interpretation"] for x in ESCAPE),
        "contested_both_images_present": verdict != "contested" or all(x in text for x in candidates),
        "insufficient_explicit": verdict != "insufficient" or "不成断" in text,
        "escape_terms": [x for x in ESCAPE if x in text],
        "fake_citation_detected": any(x in text for x in FAKE_CITATION),
        "grandiosity_detected": any(x in text for x in GRANDIOSE),
        "modern_interpretation_present": len(prose["plain_interpretation"].strip()) >= 20,
        "overmystical_term_count": sum(text.count(x) for x in OVERMYSTICAL),
        "benefit_risk_priority_present": bool(prose["judgement"]["benefit"].strip() and prose["judgement"]["risk"].strip()),
        "actionable_instruction_present": len(prose["judgement"]["instruction"].strip()) >= 8,
        "insufficient_story_violation": verdict == "insufficient" and any(x in text for x in ("具体身份", "某朝", "某代", "前世是")),
        "ordinary_identity_degraded": any(x in text for x in LOW_STATUS),
    }
    return checks


def review_blank():
    return {
        "断语力度": None, "玄意与画面": None, "现代可读性": None,
        "吉凶清晰度": None, "应期表达": None, "证据忠实度": None,
        "机器味": None, "空话比例": None, "是否通过": None, "修改意见": "",
    }


def git_sha():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def markdown_document(package):
    lines = [
        "# DeepSeek 文风审核包", "",
        "> 全部案例和人物均为虚构，仅用于语言质量审核。", "",
        f"- Provider：`{package['metadata']['provider']}`",
        f"- Model：`{package['metadata']['model']}`",
        f"- Prompt 版本：`{PROMPT_VERSION}`",
        f"- Ruleset 版本：`{RULESET_VERSION}`",
        f"- Commit SHA：`{package['metadata']['commit_sha']}`",
        f"- Workflow Run ID：`{package['metadata']['workflow_run_id']}`",
        f"- 请求数：{package['metadata']['request_count']}",
        f"- Token 数：{package['metadata']['total_tokens']}",
        f"- Schema：{package['metadata']['schema_valid_count']}/9",
        f"- 锁字段：{package['metadata']['locked_fields_unchanged_count']}/9 未变化",
        f"- 模板回退：{package['metadata']['template_fallback_count']}",
        f"- 生成时间：{package['metadata']['generated_at']}", "",
    ]
    labels = [
        ("断语力度", "1–5"), ("玄意与画面", "1–5"), ("现代可读性", "1–5"),
        ("吉凶清晰度", "1–5"), ("应期表达", "1–5"), ("证据忠实度", "1–5"),
        ("机器味", "1–5，分数越高机器味越重"),
        ("空话比例", "1–5，分数越高问题越大"), ("是否通过", "是/否"),
        ("修改意见", ""),
    ]
    for result in package["cases"]:
        source, prose = result["rule_input"], result["deepseek_output"]
        lines += [
            f"# Case {source['case_id']}", "",
            "状态：", source["verdict"], "",
            "锁定断章：", source["symbolic_title"], "",
            "象名：", source["symbolic_title"], "",
            "吉凶：", source["polarity"], "",
            "应期：", source["manifestation_period"], "",
            "证契摘要：", "；".join(source["evidence_summaries"]), "",
            "逆证摘要：", "；".join(source["counterevidence_summaries"]), "",
            "DeepSeek 象辞：", prose["image_text"], "",
            "DeepSeek 释义：", prose["plain_interpretation"], "",
            "DeepSeek 言利：", prose["judgement"]["benefit"], "",
            "DeepSeek 言弊：", prose["judgement"]["risk"], "",
            "DeepSeek 行止：", prose["judgement"]["instruction"], "",
            "自动检查：", "```json",
            json.dumps(result["automatic_checks"], ensure_ascii=False, indent=2),
            "```", "", "人工审核评分（由产品负责人填写）：", "",
        ]
        for label, scale in labels:
            lines.append(f"- {label}：{scale}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main():
    DeepSeekProvider.request_count = 0
    DeepSeekProvider.failure_count = 0
    DeepSeekProvider.circuit_open_until = 0.0
    provider = DeepSeekProvider()
    if not provider.configured:
        raise SystemExit("DeepSeek style review unavailable: server-side configuration missing")

    results = []
    token_total = 0
    for item in CASES:
        result = provider.generate_with_metrics(item)
        prose = result["content"]
        merged = merge_prose(item, prose)
        checks = automatic_checks(item, prose)
        results.append({
            "rule_input": {key: item[key] for key in (
                "case_id", "status", "verdict", "polarity", "strength", "rank",
                "symbolic_title", "manifestation_period", "judgement",
                "evidence_summaries", "counterevidence_summaries"
            )},
            "deepseek_output": prose,
            "automatic_checks": checks,
            "schema_valid": True,
            "locked_fields_unchanged": all(merged[key] == value for key, value in item.items()),
            "template_fallback": False,
            "usage": result["usage"],
            "human_review": review_blank(),
        })
        token_total += result["usage"]["total_tokens"]

    openings = [entry["deepseek_output"]["image_text"][:8] for entry in results]
    repeated = {text: count for text, count in Counter(openings).items() if count > 1}
    for entry, opening in zip(results, openings):
        entry["automatic_checks"]["repeated_opening"] = opening in repeated

    run_id = os.getenv("GITHUB_RUN_ID", "local")
    package = {
        "notice": "全部案例和人物均为虚构，仅用于语言质量审核。",
        "metadata": {
            "provider": "deepseek",
            "model": provider.model,
            "prompt_version": PROMPT_VERSION,
            "ruleset_version": RULESET_VERSION,
            "commit_sha": os.getenv("GITHUB_SHA") or git_sha(),
            "workflow_run_id": run_id,
            "request_count": provider.request_count,
            "request_limit": provider.max_requests,
            "total_tokens": token_total,
            "schema_valid_count": sum(x["schema_valid"] for x in results),
            "locked_fields_unchanged_count": sum(x["locked_fields_unchanged"] for x in results),
            "template_fallback_count": sum(x["template_fallback"] for x in results),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "synthetic_only": True,
            "secret_recorded": False,
            "system_prompt_recorded": False,
            "request_headers_recorded": False,
        },
        "cases": results,
    }
    OUTPUT_JSON.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", "utf-8")
    OUTPUT_MD.write_text(markdown_document(package), "utf-8")
    print(f"Style review pack generated: cases={len(results)}, requests={provider.request_count}")


if __name__ == "__main__":
    main()
