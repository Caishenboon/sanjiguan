from __future__ import annotations
import hashlib,json,math

DOMAIN_WEIGHTS={"ming":.20,"karma":.20,"vow":.20,"dream":.15,"relation":.10,
                "life_event":.10,"sensation":.05}
STAGES=("normalize_input","collect_evidence","build_signals","generate_candidates",
"score_candidates","apply_counterevidence","detect_conflicts","rank_hypotheses",
"cluster_past_life_nodes","build_retrieval_query","retrieve_claims","lock_engine_verdict",
"generate_prose","validate_output","persist_report")


def stable_hash(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),
                                     ensure_ascii=False).encode()).hexdigest()


def normalize_weights(domains:set[str])->dict[str,float]:
    enabled={d:w for d,w in DOMAIN_WEIGHTS.items() if d in domains and d!="gua"}
    if not enabled:return {}
    total=sum(enabled.values())
    normalized={d:min(.40,w/total) for d,w in enabled.items()}
    scale=sum(normalized.values())
    return {d:v/scale for d,v in normalized.items()}


def deduplicate_signals(signals:list[dict])->list[dict]:
    strongest={}
    for signal in signals:
        group=signal["independence_group"]
        magnitude=signal["strength"]*signal["source_reliability"]*signal["relevance"]
        if group not in strongest or magnitude>strongest[group][0]:
            strongest[group]=(magnitude,signal)
    return [item[1] for item in strongest.values()]


def contribution(signal:dict,weights:dict)->float:
    direction=1 if signal["direction"]=="support" else -1
    ordinary_discount=.7 if signal.get("ordinary_explanation_present") else 1
    return direction*signal["strength"]*signal["source_reliability"]*signal["relevance"]*weights.get(signal["domain"],0)*ordinary_discount


def score_candidate(candidate:dict,signals:list[dict],weights:dict,config:dict)->dict:
    relevant=[s for s in signals if s["tag"] in candidate["tags"]]
    components=[{"signal_id":s["id"],"value":round(contribution(s,weights),8)} for s in relevant]
    positive=sum(x["value"] for x in components if x["value"]>0)
    negative=-sum(x["value"] for x in components if x["value"]<0)
    hard=[c for c in candidate.get("hard_conflicts",[]) if c in {s["tag"] for s in signals}]
    raw=positive-negative
    raw-=config["counterevidence_penalty"]*negative
    raw-=config["hard_conflict_penalty"]*len(hard)
    raw-=config["grandiosity_penalty"] if candidate.get("grandiosity_risk") else 0
    independent_domains={s["domain"] for s in relevant if s["direction"]=="support"}
    if len(independent_domains)>=3:raw+=config["cross_system_bonus"]
    strength=round(100/(1+math.exp(-(config["calibration_a"]*raw+config["calibration_b"]))))
    return {**candidate,"raw_score":round(raw,8),"strength":strength,
            "supporting_evidence":[s["id"] for s in relevant if s["direction"]=="support"],
            "counterevidence":[s["id"] for s in relevant if s["direction"]=="oppose"],
            "hard_conflicts":hard,"ordinary_explanations":[s["id"] for s in relevant if s.get("ordinary_explanation_present")],
            "missing_critical_data":candidate.get("missing_critical_data",[]),
            "net_effect":round(positive-negative,8),"contributions":components,
            "independent_domains":sorted(independent_domains)}


def verdict(ranked:list[dict],completeness:float,config:dict)->str:
    if not ranked or completeness<config["minimum_completeness"]:return "insufficient"
    first=ranked[0];second=ranked[1] if len(ranked)>1 else {"strength":0}
    if first["hard_conflicts"]:return "contested"
    if first["strength"]>=config["decisive_strength"] and len(first["independent_domains"])>=3 and \
       first["strength"]-second["strength"]>=config["decisive_margin"]:
        return "decisive"
    if first["strength"]-second["strength"]<config["contested_margin"]:return "contested"
    return "provisional"


def run_inference(case:dict,archetypes:list[dict],config:dict)->dict:
    if case.get("mode")!="research_preview" or not case.get("synthetic_or_research"):
        raise ValueError("research_preview_owner_fixture_or_research_profile_required")
    signals=deduplicate_signals(case["signals"])
    weights=normalize_weights({s["domain"] for s in signals})
    candidates=[a for a in archetypes if set(a.get("tags",[]))&{s["tag"] for s in signals}]
    for archetype in archetypes:
        if len(candidates)>=5:break
        if archetype not in candidates:candidates.append(archetype)
    ordinary=[a for a in archetypes if a["category"]=="ordinary_livelihood"]
    if ordinary and not any(a["category"]=="ordinary_livelihood" for a in candidates):
        candidates.append(ordinary[0])
    scored=[score_candidate(c,signals,weights,config) for c in candidates[:20]]
    ranked=sorted(scored,key=lambda x:(-x["raw_score"],x["id"]))[:5]
    if ordinary and not any(h["category"]=="ordinary_livelihood" for h in ranked):
        ordinary_scored=sorted((h for h in scored if h["category"]=="ordinary_livelihood"),
                               key=lambda x:(-x["raw_score"],x["id"]))
        if ordinary_scored:ranked[-1]=ordinary_scored[0]
        ranked=sorted(ranked,key=lambda x:(-x["raw_score"],x["id"]))
    for index,item in enumerate(ranked,1):item["rank"]=index
    status=verdict(ranked,case.get("completeness",0),config)
    nodes=[{"node_type":"ordinary_continuity" if h["category"]=="ordinary_livelihood" else "root_pattern",
            "primary_archetype_id":h["id"],"secondary_archetype_ids":[],"era_symbol":None,
            "region_affinity":None,"supporting_evidence":h["supporting_evidence"],
            "counterevidence":h["counterevidence"],"strength":h["strength"],
            "confidence":"research_only","status":"research_preview"} for h in ranked[:3]]
    locked={"verdict":status,"status":"research_preview","ranked_hypotheses":ranked,
            "past_life_nodes":nodes,"ruleset_version":config["version"],
            "claim_snapshot":case.get("claim_snapshot",[]),"random_seed":case["random_seed"]}
    return {"input_hash":stable_hash(case),"signals":signals,"weights":weights,
            "locked_verdict":locked,"locked_hash":stable_hash(locked),
            "stages":list(STAGES),"notice":"研究成断，尚未进入生产规则。"}
