"""Owner-only Sprint 1B-2 knowledge workbench; research mode only."""
import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Body, Cookie, Header, HTTPException, Response

from apps.api.app.core.runtime import SESSION_COOKIE_NAME

from apps.api.app.core.ids import uuid7
from packages.knowledge_governance.policy import validate_claim, validate_research_rule

router = APIRouter(prefix="/api/v1/admin")


def pg():
    from apps.api.app import postgres_app
    return postgres_app


def owner(token):
    user = pg().auth(token)
    if user["role"] != "owner":
        raise HTTPException(403, "owner_only")
    return user


def write_context(user, method, route, key, payload):
    module = pg()
    conn = module.pool.connection()
    return module, conn, module.fingerprint(payload)


def audit(conn, user, action, kind, rid, metadata=None):
    conn.execute("""INSERT INTO audit_events(actor_id,action,resource_type,resource_id,metadata_redacted)
                    VALUES(%s,%s,%s,%s,%s)""",
                 (user["id"], action, kind, rid, json.dumps(metadata or {})))


@router.get("/knowledge/documents")
def documents(token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    module, user = pg(), owner(token)
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        rows = conn.execute("""SELECT id,title,author,traditions,knowledge_layer,access_class,
          review_status,updated_at FROM knowledge_documents WHERE deleted_at IS NULL ORDER BY updated_at DESC""").fetchall()
        return {"items": [{**row, "id": str(row["id"])} for row in rows]}


@router.post("/knowledge/documents", status_code=201)
def create_document(payload: dict = Body(...), response: Response = None,
                    key: str = Header(alias="Idempotency-Key"),
                    token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    module, user = pg(), owner(token)
    with module.pool.connection() as conn, conn.transaction():
        module.runtime(conn, user)
        claim = module.idempotency(conn,user["id"],"POST","/api/v1/admin/knowledge/documents",key,module.fingerprint(payload))
        if isinstance(claim,dict):
            if response: response.status_code=201
            return claim
        if payload.get("access_class")=="sealed" and any(payload.get(k) for k in ("notes","content","excerpt")):
            raise HTTPException(422,"sealed_metadata_only")
        did=uuid7()
        conn.execute("""INSERT INTO knowledge_documents(id,title,original_title,author,translator,editor,
          edition,publication_year,traditions,knowledge_layer,access_class,license_json,source_uri,
          catalog_identifier,checksum,language,review_status,reviewer_ids,notes,created_by,status,
          license_status,metadata_json)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s,%s,'pending',%s,'{}')""",
          (did,payload["title"],payload.get("original_title"),payload.get("author"),payload.get("translator"),
           payload.get("editor"),payload.get("edition"),payload.get("publication_year"),payload.get("traditions",[]),
           payload["knowledge_layer"],payload["access_class"],json.dumps(payload.get("license",{})),
           payload.get("source_uri"),payload.get("catalog_identifier"),payload.get("checksum"),
           payload.get("language","zh"),payload.get("reviewer_ids",[]),payload.get("notes"),user["id"],
           payload["access_class"]))
        result={"id":str(did),"review_status":"draft","production_use":False}
        audit(conn,user,"knowledge.document.created","knowledge_document",did)
        module.complete(conn,claim,key,201,result)
        return result


@router.get("/knowledge/documents/{document_id}")
def get_document(document_id: UUID, token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        row=conn.execute("SELECT * FROM knowledge_documents WHERE id=%s AND deleted_at IS NULL",(document_id,)).fetchone()
        if not row: raise HTTPException(404,"document_not_found")
        row=dict(row); row["id"]=str(row["id"]); return row


@router.patch("/knowledge/documents/{document_id}")
def patch_document(document_id:UUID,payload:dict=Body(...),key:str=Header(alias="Idempotency-Key"),
                   token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"PATCH","/api/v1/admin/knowledge/documents/{id}",key,module.fingerprint(payload))
        if isinstance(idem,dict): return idem
        row=conn.execute("SELECT * FROM knowledge_documents WHERE id=%s AND deleted_at IS NULL FOR UPDATE",(document_id,)).fetchone()
        if not row: raise HTTPException(404,"document_not_found")
        version=conn.execute("SELECT coalesce(max(version_no),0)+1 n FROM knowledge_document_versions WHERE document_id=%s",(document_id,)).fetchone()["n"]
        conn.execute("INSERT INTO knowledge_document_versions VALUES(%s,%s,%s,%s,%s,now())",
                     (uuid7(),document_id,version,json.dumps(dict(row),default=str),user["id"]))
        allowed={"title","source_uri","catalog_identifier","notes","review_status"}
        updates={k:v for k,v in payload.items() if k in allowed}
        if not updates: raise HTTPException(422,"no_patchable_fields")
        assignments=",".join(f"{k}=%s" for k in updates)
        conn.execute(f"UPDATE knowledge_documents SET {assignments},updated_at=now() WHERE id=%s",
                     (*updates.values(),document_id))
        result={"id":str(document_id),"version_no":version}
        audit(conn,user,"knowledge.document.updated","knowledge_document",document_id)
        module.complete(conn,idem,key,200,result);return result


@router.post("/knowledge/claims",status_code=201)
def create_claim(payload: dict=Body(...),response:Response=None,key:str=Header(alias="Idempotency-Key"),
                 token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST","/api/v1/admin/knowledge/claims",key,module.fingerprint(payload))
        if isinstance(idem,dict):
            if response: response.status_code=201
            return idem
        doc=conn.execute("SELECT knowledge_layer FROM knowledge_documents WHERE id=%s",(payload["document_id"],)).fetchone()
        if not doc: raise HTTPException(422,"document_not_found")
        errors=validate_claim(payload,doc)
        if errors: raise HTTPException(422,errors)
        cid=uuid7()
        conn.execute("""INSERT INTO knowledge_claims(id,document_id,claim_text,claim_type,traditions,
          locator_json,source_excerpt,paraphrase,access_class,confidence,review_status,allowed_uses,created_by)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s)""",
          (cid,payload["document_id"],payload["claim_text"],payload["claim_type"],payload.get("traditions",[]),
           json.dumps(payload.get("locator",{})),payload.get("source_excerpt"),payload.get("paraphrase"),
           payload["access_class"],payload["confidence"],json.dumps(payload["allowed_uses"]),user["id"]))
        result={"id":str(cid),"review_status":"draft"}
        audit(conn,user,"knowledge.claim.created","knowledge_claim",cid)
        module.complete(conn,idem,key,201,result); return result


@router.get("/knowledge/claims")
def list_claims(include_history:bool=False,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        clause="" if include_history else "AND review_status NOT IN ('rejected','retired')"
        rows=conn.execute(f"""SELECT id,document_id,claim_text,claim_type,traditions,locator_json,
          access_class,confidence,review_status,updated_at FROM knowledge_claims
          WHERE deleted_at IS NULL {clause} ORDER BY updated_at DESC""").fetchall()
        return {"items":[{**r,"id":str(r["id"]),"document_id":str(r["document_id"])} for r in rows]}


@router.patch("/knowledge/claims/{claim_id}")
def patch_claim(claim_id:UUID,payload:dict=Body(...),key:str=Header(alias="Idempotency-Key"),
                token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"PATCH","/api/v1/admin/knowledge/claims/{id}",key,module.fingerprint(payload))
        if isinstance(idem,dict): return idem
        row=conn.execute("SELECT * FROM knowledge_claims WHERE id=%s AND deleted_at IS NULL FOR UPDATE",(claim_id,)).fetchone()
        if not row: raise HTTPException(404,"claim_not_found")
        version=conn.execute("SELECT coalesce(max(version_no),0)+1 n FROM knowledge_claim_versions WHERE claim_id=%s",(claim_id,)).fetchone()["n"]
        conn.execute("INSERT INTO knowledge_claim_versions VALUES(%s,%s,%s,%s,%s,now())",
                     (uuid7(),claim_id,version,json.dumps(dict(row),default=str),user["id"]))
        allowed={"claim_text","paraphrase","confidence","review_status"}
        updates={k:v for k,v in payload.items() if k in allowed}
        if "locator" in payload: updates["locator_json"]=json.dumps(payload["locator"])
        if not updates: raise HTTPException(422,"no_patchable_fields")
        assignments=",".join(f"{k}=%s" for k in updates)
        conn.execute(f"UPDATE knowledge_claims SET {assignments},updated_at=now() WHERE id=%s",
                     (*updates.values(),claim_id))
        result={"id":str(claim_id),"version_no":version,"linked_rules_need_review":True}
        audit(conn,user,"knowledge.claim.updated","knowledge_claim",claim_id)
        module.complete(conn,idem,key,200,result);return result


@router.post("/knowledge/claims/{claim_id}/submit-review")
def submit_claim(claim_id:UUID,key:str=Header(alias="Idempotency-Key"),
                 token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    return _claim_transition(claim_id,"researched","submit-review",key,token)


@router.post("/knowledge/claims/{claim_id}/reject")
def reject_claim(claim_id:UUID,key:str=Header(alias="Idempotency-Key"),
                 token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    return _claim_transition(claim_id,"rejected","reject",key,token)


@router.post("/knowledge/claims/{claim_id}/approve")
def approve_claim(claim_id:UUID,key:str=Header(alias="Idempotency-Key"),
                  token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token); payload={"id":str(claim_id),"status":"approved"}
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST","/api/v1/admin/knowledge/claims/{id}/approve",
                                key,module.fingerprint(payload))
        if isinstance(idem,dict): return idem
        row=conn.execute("SELECT created_by,claim_type,traditions,review_status FROM knowledge_claims WHERE id=%s",
                         (claim_id,)).fetchone()
        if not row: raise HTTPException(404,"claim_not_found")
        if row["created_by"]==user["id"]: raise HTTPException(409,"creator_cannot_self_approve")
        qualification=conn.execute("""SELECT 1 FROM reviewer_profiles p JOIN reviewer_qualifications q
          ON q.reviewer_id=p.id WHERE p.user_id=%s AND q.verification_status='verified'
          AND (q.tradition IS NULL OR q.tradition=ANY(%s)) LIMIT 1""",(user["id"],row["traditions"])).fetchone()
        if not qualification: raise HTTPException(403,"verified_reviewer_qualification_required")
        conn.execute("UPDATE knowledge_claims SET review_status='approved',reviewer_ids=array_append(reviewer_ids,%s),updated_at=now() WHERE id=%s",
                     (user["id"],claim_id))
        audit(conn,user,"knowledge.claim.approved","knowledge_claim",claim_id)
        module.complete(conn,idem,key,200,payload); return payload


@router.post("/knowledge/claims/{claim_id}/retire")
def retire_claim(claim_id:UUID,key:str=Header(alias="Idempotency-Key"),
                 token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    return _claim_transition(claim_id,"retired","retire",key,token)


def _claim_transition(claim_id,status,action,key,token):
    module,user=pg(),owner(token); payload={"id":str(claim_id),"status":status}
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        idem=module.idempotency(conn,user["id"],"POST",f"/api/v1/admin/knowledge/claims/{{id}}/{action}",key,module.fingerprint(payload))
        if isinstance(idem,dict): return idem
        if not conn.execute("UPDATE knowledge_claims SET review_status=%s,updated_at=now() WHERE id=%s",(status,claim_id)).rowcount:
            raise HTTPException(404,"claim_not_found")
        result=payload; audit(conn,user,f"knowledge.claim.{action}","knowledge_claim",claim_id)
        module.complete(conn,idem,key,200,result); return result


@router.get("/knowledge/search")
def search(q:str="",token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        rows=conn.execute("""SELECT c.id,c.claim_text,c.claim_type,c.confidence,c.review_status,
          c.access_class,c.locator_json FROM knowledge_claims c WHERE c.deleted_at IS NULL
          AND c.review_status NOT IN ('rejected','retired') AND c.access_class NOT IN
          ('sealed','practice_restricted','copyright_restricted','unknown') AND c.claim_text ILIKE %s
          ORDER BY c.updated_at DESC LIMIT 50""",(f"%{q}%",)).fetchall()
        return {"items":[{**r,"id":str(r["id"])} for r in rows],"filtered_classes":
                ["sealed","practice_restricted","copyright_restricted","unknown","rejected","retired"]}


@router.get("/knowledge/impact/{claim_id}")
def impact(claim_id:UUID,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        rows=conn.execute("""SELECT r.id,r.name,r.status,r.needs_review,l.basis_type FROM rule_claim_links l
          JOIN rule_drafts r ON r.id=l.rule_id WHERE l.claim_id=%s""",(claim_id,)).fetchall()
        return {"claim_id":str(claim_id),"affected_rules":rows}


@router.post("/rules/{rule_id}/validate")
def validate_rule_endpoint(rule_id:str,token:str|None=Cookie(None,alias=SESSION_COOKIE_NAME)):
    module,user=pg(),owner(token)
    with module.pool.connection() as conn,conn.transaction():
        module.runtime(conn,user)
        rule=conn.execute("SELECT * FROM rule_drafts WHERE id=%s",(rule_id,)).fetchone()
        if not rule: raise HTTPException(404,"rule_not_found")
        claims=conn.execute("""SELECT c.review_status FROM rule_claim_links l JOIN knowledge_claims c
          ON c.id=l.claim_id WHERE l.rule_id=%s""",(rule_id,)).fetchall()
        definition=dict(rule["definition_json"]); definition.update(status=rule["status"],
          production_activatable=rule["production_activatable"],method_id=rule["method_id"])
        errors=validate_research_rule(definition,claims)
        return {"valid":not errors,"errors":errors,"production_activatable":False}
