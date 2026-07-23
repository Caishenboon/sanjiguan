"""Owner-only deterministic research preview pipeline."""
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter,Body,Cookie,Header,HTTPException,Response
from apps.api.app.core.ids import uuid7
from packages.research_inference.engine import run_inference,stable_hash
from packages.research_inference.providers import DeepSeekProvider,FakeProvider,TemplateProvider,merge_prose

router=APIRouter(prefix="/api/v1/admin/research")
ROOT=Path(__file__).resolve().parents[3]
CONFIG=json.loads((ROOT/"knowledge/research/scoring-config.json").read_text("utf-8"))
ARCHETYPES=json.loads((ROOT/"knowledge/research/inference-archetypes.json").read_text("utf-8"))


def pg():
    from apps.api.app import postgres_app
    return postgres_app


def owner(token):
    user=pg().auth(token)
    if user["role"]!="owner":raise HTTPException(403,"owner_only_research_preview")
    return user


def encrypt(value):
    return pg().provider.encrypt(json.dumps(value,ensure_ascii=False,default=str).encode())


@router.post("/analyses",status_code=201)
def create_analysis(payload:dict=Body(...),response:Response=None,key:str=Header(alias="Idempotency-Key"),
                    token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    if payload.get("mode")!="research_preview" or not payload.get("synthetic_or_research"):
        raise HTTPException(422,"research_preview_fixture_or_research_profile_required")
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST","/api/v1/admin/research/analyses",key,module.fingerprint(payload))
        if isinstance(idem,dict):
            if response:response.status_code=201
            return idem
        profile=conn.execute("SELECT research_profile FROM profiles WHERE id=%s",(payload["profile_id"],)).fetchone()
        if not profile or not (profile["research_profile"] or payload.get("is_synthetic")):
            raise HTTPException(422,"profile_not_marked_for_research")
        rid=uuid7()
        conn.execute("""INSERT INTO analysis_runs(id,profile_id,ruleset_id,status,input_snapshot_encrypted,
          input_hash,random_seed,data_completeness,run_mode,is_synthetic,ruleset_snapshot,claim_snapshot)
          VALUES(%s,%s,%s,'queued',%s,%s,%s,%s,'research_preview',%s,%s,%s)""",
          (rid,payload["profile_id"],payload["ruleset_id"],encrypt(payload),stable_hash(payload),
           payload["random_seed"],payload.get("completeness",0),payload.get("is_synthetic",False),
           json.dumps(payload.get("ruleset_snapshot",{})),json.dumps(payload.get("claim_snapshot",[]))))
        result={"id":str(rid),"mode":"research_preview","status":"queued"}
        module.complete(conn,idem,key,201,result);return result


@router.get("/analyses")
def list_analyses(token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        rows=conn.execute("""SELECT id,status,run_mode,is_synthetic,created_at,completed_at
          FROM analysis_runs WHERE run_mode='research_preview' AND deleted_at IS NULL ORDER BY created_at DESC""").fetchall()
        return {"items":[{**r,"id":str(r["id"])} for r in rows]}


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id:UUID,token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        row=conn.execute("""SELECT id,status,run_mode,is_synthetic,input_hash,output_hash,
          ruleset_snapshot,claim_snapshot,created_at,completed_at FROM analysis_runs WHERE id=%s""",(analysis_id,)).fetchone()
        if not row:raise HTTPException(404,"analysis_not_found")
        return {**row,"id":str(row["id"])}


@router.post("/analyses/{analysis_id}/run")
def run_analysis(analysis_id:UUID,key:str=Header(alias="Idempotency-Key"),
                 token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    request={"analysis_id":str(analysis_id)}
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST","/api/v1/admin/research/analyses/{id}/run",
                                key,module.fingerprint(request))
        if isinstance(idem,dict):return idem
        row=conn.execute("SELECT * FROM analysis_runs WHERE id=%s AND run_mode='research_preview' FOR UPDATE",
                         (analysis_id,)).fetchone()
        if not row:raise HTTPException(404,"analysis_not_found")
        case=json.loads(module.provider.decrypt(row["input_snapshot_encrypted"]).decode())
        deterministic=run_inference(case,ARCHETYPES,CONFIG)
        previous=deterministic["input_hash"]
        now=datetime.now(timezone.utc)
        for stage in deterministic["stages"]:
            output=stable_hash({"stage":stage,"previous":previous,"locked":deterministic["locked_hash"]})
            conn.execute("""INSERT INTO analysis_stage_runs(id,analysis_run_id,stage_name,input_hash,output_hash,
              ruleset_version,claim_versions,random_seed,started_at,completed_at,status)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'complete')""",
              (uuid7(),analysis_id,stage,previous,output,CONFIG["version"],
               json.dumps(case.get("claim_snapshot",[])),row["random_seed"],now,now))
            conn.execute("""INSERT INTO audit_events(actor_id,action,resource_type,resource_id,metadata_redacted)
              VALUES(%s,'research.stage.complete','analysis_run',%s,%s)""",
              (user["id"],analysis_id,json.dumps({"stage":stage,"input_hash":previous,
               "output_hash":output,"ruleset_version":CONFIG["version"]})))
            previous=output
        for signal in deterministic["signals"]:
            conn.execute("""INSERT INTO normalized_signals(id,analysis_run_id,domain,source_evidence_ids,tag,
              direction,strength,source_reliability,relevance,independence_group,time_scope,
              ordinary_explanation_present,ruleset_version) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(analysis_run_id,independence_group,tag,direction) DO NOTHING""",
              (UUID(signal["id"]) if _uuid(signal["id"]) else uuid7(),analysis_id,signal["domain"],
               [UUID(x) for x in signal.get("source_evidence_ids",[])],signal["tag"],signal["direction"],
               signal["strength"],signal["source_reliability"],signal["relevance"],signal["independence_group"],
               json.dumps(signal.get("time_scope",{})),signal.get("ordinary_explanation_present",False),CONFIG["version"]))
        locked=deterministic["locked_verdict"]
        retrieval_id=uuid7()
        query_terms=" ".join(sorted({signal["tag"] for signal in deterministic["signals"]}))
        conn.execute("""INSERT INTO retrieval_runs(id,analysis_run_id,query_json,input_hash,started_at,
          completed_at,status,embedding_mode) VALUES(%s,%s,%s,%s,%s,%s,'complete','disabled')""",
          (retrieval_id,analysis_id,json.dumps({"terms":query_terms}),stable_hash(query_terms),now,now))
        claims=conn.execute("""SELECT c.id,coalesce(max(v.version_no),1) claim_version,
          ts_rank(to_tsvector('simple',c.claim_text),plainto_tsquery('simple',%s)) rank_score
          FROM knowledge_claims c LEFT JOIN knowledge_claim_versions v ON v.claim_id=c.id
          WHERE c.deleted_at IS NULL AND c.review_status IN ('approved','reviewed')
          AND c.access_class NOT IN ('sealed','practice_restricted','copyright_restricted','unknown')
          AND coalesce((c.allowed_uses->>'rag')::boolean,false)=true
          AND to_tsvector('simple',c.claim_text)@@plainto_tsquery('simple',%s)
          GROUP BY c.id ORDER BY rank_score DESC,c.id LIMIT 20""",(query_terms,query_terms)).fetchall()
        for rank_number,claim in enumerate(claims,1):
            conn.execute("""INSERT INTO retrieval_results(id,retrieval_run_id,claim_id,claim_version,rank,match_basis)
              VALUES(%s,%s,%s,%s,%s,%s)""",(uuid7(),retrieval_id,claim["id"],claim["claim_version"],
              rank_number,json.dumps({"fts":float(claim["rank_score"])})))
        for sequence_no,link_type in enumerate(("terminal_consciousness_candidate","bardo_tendency_candidate",
          "attraction_factor","rebirth_environment","present_manifestation"),1):
            conn.execute("""INSERT INTO bardo_chain_links(id,analysis_run_id,sequence_no,link_type,
              basis_claim_ids,system_mapping_claim_ids,status,content_encrypted)
              VALUES(%s,%s,%s,%s,'{}','{}','breakpoint',%s)""",
              (uuid7(),analysis_id,sequence_no,link_type,encrypt({"notice":"链条未成：缺少已审校依据"})))
        provider=FakeProvider()
        prose=provider.generate({"locked_verdict":locked})
        pass1_hash=stable_hash(prose)
        conn.execute("""INSERT INTO prompt_runs(id,analysis_run_id,pass_no,provider,prompt_hash,
          response_hash,status,token_budget) VALUES(%s,%s,1,'fake',%s,%s,'complete',0)""",
          (uuid7(),analysis_id,stable_hash({"pass":1,"locked":locked}),pass1_hash))
        composition={"image_text":prose["image_text"],"plain_interpretation":prose["plain_interpretation"],
                     "judgement":prose["judgement"]}
        conn.execute("""INSERT INTO prompt_runs(id,analysis_run_id,pass_no,provider,prompt_hash,
          response_hash,status,token_budget) VALUES(%s,%s,2,'fake',%s,%s,'complete',0)""",
          (uuid7(),analysis_id,stable_hash({"pass":2,"validated":pass1_hash}),stable_hash(composition)))
        report=merge_prose(locked,composition)
        conn.execute("""INSERT INTO generated_prose(id,analysis_run_id,prose_encrypted,provider,template_version,
          locked_verdict_hash,validated) VALUES(%s,%s,%s,'fake','1.0',%s,true)""",
          (uuid7(),analysis_id,encrypt(prose),deterministic["locked_hash"]))
        conn.execute("""INSERT INTO research_reports(id,analysis_run_id,verdict_json,report_encrypted,
          ruleset_version,claim_snapshot,prose_source) VALUES(%s,%s,%s,%s,%s,%s,'fake')""",
          (uuid7(),analysis_id,json.dumps(locked),encrypt(report),CONFIG["version"],
           json.dumps(case.get("claim_snapshot",[]))))
        conn.execute("UPDATE analysis_runs SET status='complete',result_json=%s,output_hash=%s,completed_at=now() WHERE id=%s",
                     (json.dumps(locked),deterministic["locked_hash"],analysis_id))
        result={"id":str(analysis_id),"status":"complete","verdict":locked["verdict"],
                "locked_hash":deterministic["locked_hash"],"notice":deterministic["notice"]}
        module.complete(conn,idem,key,200,result);return result


@router.post("/analyses/{analysis_id}/retry-prose")
def retry_prose(analysis_id:UUID,key:str=Header(alias="Idempotency-Key"),
                token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token);request={"analysis_id":str(analysis_id),"operation":"retry-prose"}
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST","/api/v1/admin/research/analyses/{id}/retry-prose",
                                key,module.fingerprint(request))
        if isinstance(idem,dict):return idem
        row=conn.execute("SELECT result_json FROM analysis_runs WHERE id=%s AND status='complete'",(analysis_id,)).fetchone()
        if not row:raise HTTPException(404,"completed_analysis_not_found")
        provider=DeepSeekProvider()
        source="deepseek"
        try:prose=provider.generate({"locked_verdict":row["result_json"]})
        except Exception:
            source="template";prose=TemplateProvider().generate({"locked_verdict":row["result_json"]})
        try:report=merge_prose(row["result_json"],prose)
        except ValueError:
            source="template";prose=TemplateProvider().generate({});report=merge_prose(row["result_json"],prose)
        conn.execute("""UPDATE research_reports SET report_encrypted=%s,prose_source=%s WHERE analysis_run_id=%s""",
                     (encrypt(report),source,analysis_id))
        result={"analysis_id":str(analysis_id),"prose_source":source,"locked_verdict_unchanged":True}
        module.complete(conn,idem,key,200,result);return result


def _uuid(value):
    try:UUID(value);return True
    except (ValueError,TypeError):return False


@router.get("/analyses/{analysis_id}/signals")
def signals(analysis_id:UUID,token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user); rows=conn.execute(
          "SELECT * FROM normalized_signals WHERE analysis_run_id=%s ORDER BY independence_group",(analysis_id,)).fetchall()
        return {"items":[{**r,"id":str(r["id"]),"analysis_run_id":str(r["analysis_run_id"])} for r in rows]}


@router.get("/analyses/{analysis_id}/hypotheses")
def hypotheses(analysis_id:UUID,token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user);row=conn.execute("SELECT result_json FROM analysis_runs WHERE id=%s",(analysis_id,)).fetchone()
        if not row:raise HTTPException(404,"analysis_not_found")
        return {"items":(row["result_json"] or {}).get("ranked_hypotheses",[])}


@router.get("/analyses/{analysis_id}/retrieval")
def retrieval(analysis_id:UUID,token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        run=conn.execute("SELECT id,embedding_mode,query_json FROM retrieval_runs WHERE analysis_run_id=%s",(analysis_id,)).fetchone()
        if not run:return {"analysis_id":str(analysis_id),"embedding_mode":"disabled","items":[]}
        rows=conn.execute("""SELECT r.claim_id,r.claim_version,r.rank,r.match_basis FROM retrieval_results r
          WHERE r.retrieval_run_id=%s ORDER BY r.rank""",(run["id"],)).fetchall()
        return {"analysis_id":str(analysis_id),"embedding_mode":run["embedding_mode"],
                "query":run["query_json"],"items":[{**r,"claim_id":str(r["claim_id"])} for r in rows]}


@router.get("/analyses/{analysis_id}/report")
def report(analysis_id:UUID,token:str|None=Cookie(None,alias="__Host-session")):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user);row=conn.execute("SELECT * FROM research_reports WHERE analysis_run_id=%s",(analysis_id,)).fetchone()
        if not row:raise HTTPException(404,"report_not_found")
        return {"analysis_id":str(analysis_id),"mode":"research_preview",
          "banner":"研究预览 · 非生产命盘","report":json.loads(module.provider.decrypt(row["report_encrypted"]).decode()),
          "prose_source":row["prose_source"],"ruleset_version":row["ruleset_version"],
          "claim_snapshot":row["claim_snapshot"]}
