"""Thin owner-only API for deterministic traditional V1 profiles."""
from __future__ import annotations

import json
from copy import deepcopy
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sanji_engine import execute, replay
from upstream_adapters import BaziUpstreamAdapter, LiuyaoUpstreamAdapter, ZiweiUpstreamAdapter

from apps.api.app.core.ids import uuid7
from apps.api.app.core.runtime import SESSION_COOKIE_NAME

router = APIRouter(prefix="/api/v1/admin/research/traditional-complete")
RULESET_ID = "sanji-traditional-composite-1.0.0"
DATA_VERSIONS = {"tzdb":"2025.2","ephemeris":"astronomy-engine/2.1.19","calendar_dataset":"traditional-v1-upstream-lock/1.0.0"}


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_record_id: UUID | None = None
    bazi: dict | None = None
    ziwei: dict | None = None
    liuyao: dict | None = None


def _pg():
    from apps.api.app import postgres_app
    return postgres_app


def _owner(token):
    user = _pg().auth(token)
    if user["role"] != "owner":
        raise HTTPException(403, "owner_only_traditional_complete_research")
    return user


def _adapters(payload):
    results=[]
    for name, adapter in (("bazi",BaziUpstreamAdapter()),("ziwei",ZiweiUpstreamAdapter()),("liuyao",LiuyaoUpstreamAdapter())):
        if payload.get(name) is not None:
            results.append(adapter.execute(deepcopy(payload[name])))
    if not results:
        raise HTTPException(422,"at_least_one_traditional_input_required")
    return results


def _request(results, run_id, mode="research_preview"):
    return {"schema_version":"engine-request/1.0.0","engine_api_version":"1.0","run_id":run_id,
      "run_mode":mode,"requested_modules":["traditional-complete"],
      "input_snapshot":{"operation":"compose_traditional_algorithms_complete_v1","adapter_results":results},
      "ruleset_bundle_id":RULESET_ID,"data_versions":deepcopy(DATA_VERSIONS),
      "deterministic_context":{"as_of":"2000-01-01T00:00:00Z","random_method":"none","random_seed":None}}


def _persist(conn,module,user,run_id,profile_id,request,result,parent=None):
    if profile_id is not None and not conn.execute("SELECT 1 FROM profiles WHERE id=%s AND owner_id=%s AND deleted_at IS NULL",(profile_id,user["id"])).fetchone():
        raise HTTPException(404,"profile_not_found")
    manifest=result["replay_manifest"]; domain=result["module_results"]["traditional-complete"]["result"]
    conn.execute("""INSERT INTO traditional_complete_runs(id,owner_id,profile_record_id,parent_run_id,ruleset_bundle_id,research_status,review_status,input_snapshot_encrypted,result_encrypted,input_hash,output_hash,trace_hash,evidence_graph_hash,replay_manifest,replay_manifest_hash) VALUES(%s,%s,%s,%s,%s,'research_active','UNCONFIRMED',%s,%s,%s,%s,%s,%s,%s,%s)""",
      (run_id,user["id"],profile_id,parent,RULESET_ID,module.provider.encrypt(json.dumps(request,ensure_ascii=False).encode()),module.provider.encrypt(json.dumps(result,ensure_ascii=False).encode()),result["input_hash"],result["output_hash"],result["trace_hash"],domain["evidence_graph"]["graph_hash"],json.dumps(manifest),manifest["content_hash"]))


@router.post("/execute",status_code=201)
def create(payload_model:Payload=Body(...),key:str=Header(alias="Idempotency-Key"),token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=_pg(),_owner(token); payload=payload_model.model_dump(mode="json"); run_id=uuid7()
    request=_request(_adapters(payload),str(run_id)); result=execute(request)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user); claim=module.idempotency(conn,user["id"],"POST",router.prefix+"/execute",key,module.fingerprint(payload))
        if isinstance(claim,dict): return claim
        _persist(conn,module,user,run_id,payload.get("profile_record_id"),request,result)
        response={"id":str(run_id),"research_status":"UNCONFIRMED","result":result}; module.complete(conn,claim,key,201,response); return response


@router.get("/{run_id}")
def get(run_id:UUID,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=_pg(),_owner(token)
    with module.pool.connection() as conn:
        module.runtime(conn,user); row=conn.execute("SELECT result_encrypted FROM traditional_complete_runs WHERE id=%s AND deleted_at IS NULL",(run_id,)).fetchone()
        if not row: raise HTTPException(404,"traditional_complete_run_not_found")
        return json.loads(module.provider.decrypt(row["result_encrypted"]))


@router.post("/{run_id}/replay")
def replay_run(run_id:UUID,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=_pg(),_owner(token)
    with module.pool.connection() as conn:
        module.runtime(conn,user); row=conn.execute("SELECT input_snapshot_encrypted,replay_manifest,output_hash FROM traditional_complete_runs WHERE id=%s AND deleted_at IS NULL",(run_id,)).fetchone()
        if not row: raise HTTPException(404,"traditional_complete_run_not_found")
        request=json.loads(module.provider.decrypt(row["input_snapshot_encrypted"])); request["run_id"]=str(uuid7()); request["run_mode"]="replay"
        result=replay(row["replay_manifest"],request); return {"replay_status":"matched","output_hash":result["output_hash"],"expected_output_hash":row["output_hash"]}


@router.post("/{run_id}/reanalyze",status_code=201)
def reanalyze(run_id:UUID,payload_model:Payload|None=Body(None),key:str=Header(alias="Idempotency-Key"),token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=_pg(),_owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user); row=conn.execute("SELECT profile_record_id,input_snapshot_encrypted FROM traditional_complete_runs WHERE id=%s AND deleted_at IS NULL",(run_id,)).fetchone()
        if not row: raise HTTPException(404,"traditional_complete_run_not_found")
        original=json.loads(module.provider.decrypt(row["input_snapshot_encrypted"])); payload=payload_model.model_dump(mode="json") if payload_model else None
        results=_adapters(payload) if payload else original["input_snapshot"]["adapter_results"]; new_id=uuid7(); request=_request(results,str(new_id)); result=execute(request)
        claim=module.idempotency(conn,user["id"],"POST",router.prefix+"/{run_id}/reanalyze",key,module.fingerprint({"run_id":str(run_id),"payload":payload}))
        if isinstance(claim,dict): return claim
        _persist(conn,module,user,new_id,payload.get("profile_record_id") if payload else row["profile_record_id"],request,result,run_id)
        response={"id":str(new_id),"parent_run_id":str(run_id),"result":result}; module.complete(conn,claim,key,201,response); return response


@router.get("/{left_run_id}/compare/{right_run_id}")
def compare(left_run_id:UUID,right_run_id:UUID,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=_pg(),_owner(token)
    with module.pool.connection() as conn:
        module.runtime(conn,user); rows=conn.execute("SELECT id,input_hash,output_hash,trace_hash,evidence_graph_hash FROM traditional_complete_runs WHERE id=ANY(%s) AND deleted_at IS NULL",([left_run_id,right_run_id],)).fetchall()
        if len(rows)!=2: raise HTTPException(404,"traditional_complete_run_not_found")
        values={r["id"]:r for r in rows}; left,right=values[left_run_id],values[right_run_id]
        return {"left_run_id":str(left_run_id),"right_run_id":str(right_run_id),"differences":{field:left[field]!=right[field] for field in ("input_hash","output_hash","trace_hash","evidence_graph_hash")}}
