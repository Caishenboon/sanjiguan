import importlib
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from apps.api.app.core.security import token_hash

DSN = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(DSN, "real PostgreSQL HTTP E2E requires TEST_DATABASE_URL")
class PostgreSQLHttpE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.update(
            APP_ENV="test", STORAGE_BACKEND="postgres", KEY_PROVIDER="test-only",
            DATABASE_URL=DSN or "", TEST_ENCRYPTION_KEY_HEX="11" * 32,
        )
        module = importlib.import_module("apps.api.app.postgres_app")
        cls.app_module = module
        cls.client = TestClient(module.app, base_url="https://testserver")
        cls.admin = psycopg.connect(DSN, autocommit=True)

    @classmethod
    def tearDownClass(cls):
        cls.admin.execute("TRUNCATE users CASCADE")
        cls.admin.close()
        cls.app_module.pool.close()

    def setUp(self):
        self.admin.execute("TRUNCATE users CASCADE")

    def invitation(self):
        issuer, invitation, token = uuid4(), uuid4(), "test-invitation-" + uuid4().hex
        self.admin.execute("INSERT INTO users(id,email_ciphertext,role) VALUES(%s,%s,'owner')",
                           (issuer, b"issuer"))
        self.admin.execute(
            """INSERT INTO invitations(id,token_hash,role,issued_by,expires_at)
               VALUES(%s,%s,'member',%s,%s)""",
            (invitation, token_hash(token), issuer, datetime.now(timezone.utc) + timedelta(hours=1)))
        return token

    def payload(self, name="E2E"):
        return {"display_name": name, "consent_version": "1.0", "birth": {
            "calendar_type": "gregorian", "local_date": "1990-01-15",
            "local_time": "08:30:00", "timezone_id": "Asia/Shanghai",
            "timezone_database": "IANA", "timezone_database_version": "2025b",
            "time_precision": "minute", "place": {"label": "Shanghai", "latitude": 31.23,
            "longitude": 121.47, "coordinate_source": "user_confirmed"},
            "user_confirmed": True, "captured_at": datetime.now(timezone.utc).isoformat()}}

    def login(self, client=None):
        client = client or self.client
        response = client.post("/api/v1/auth/invitations/accept", json={"token": self.invitation()})
        self.assertEqual(200, response.status_code, response.text)
        return response

    def test_auth_crud_isolation_idempotency_logout_and_soft_delete(self):
        self.login()
        payload = self.payload()
        headers = {"Idempotency-Key": "e2e-create-key-0001"}
        first = self.client.post("/api/v1/profiles", json=payload, headers=headers)
        self.assertEqual(201, first.status_code, first.text)
        replay = self.client.post("/api/v1/profiles", json=payload, headers=headers)
        self.assertEqual(first.json()["id"], replay.json()["id"])
        conflict = self.client.post("/api/v1/profiles", json=self.payload("other"), headers=headers)
        self.assertEqual(409, conflict.status_code)
        pid = first.json()["id"]
        self.assertEqual(200, self.client.get(f"/api/v1/profiles/{pid}").status_code)
        patch = self.client.patch(f"/api/v1/profiles/{pid}", json={"display_name": "updated"},
                                  headers={"Idempotency-Key": "e2e-patch-key-00001"})
        self.assertEqual(200, patch.status_code, patch.text)

        other = TestClient(self.app_module.app, base_url="https://testserver")
        self.login(other)
        self.assertEqual(404, other.get(f"/api/v1/profiles/{pid}").status_code)

        deleted = self.client.delete(f"/api/v1/profiles/{pid}",
            headers={"Idempotency-Key": "e2e-delete-key-0001"})
        self.assertEqual(202, deleted.status_code)
        self.assertEqual(404, self.client.get(f"/api/v1/profiles/{pid}").status_code)
        self.assertEqual(204, self.client.post("/api/v1/auth/logout").status_code)
        self.assertEqual(401, self.client.get(f"/api/v1/profiles/{pid}").status_code)

        count = self.admin.execute(
            "SELECT count(*) FROM profiles WHERE id=%s AND deleted_at IS NOT NULL", (pid,)
        ).fetchone()[0]
        self.assertEqual(1, count)

    def test_onboarding_evidence_completeness_and_physical_coin_recording(self):
        self.login()
        created = self.client.post("/api/v1/profiles", json=self.payload(),
            headers={"Idempotency-Key": "e2e-evidence-profile-0001"})
        self.assertEqual(201, created.status_code, created.text)
        pid = created.json()["id"]
        onboarding = self.client.put(f"/api/v1/profiles/{pid}/onboarding", json={
            "current_step": 3, "step_states": {"sensation": "explicit_none"},
            "draft": {"dream": {"answer_state": "unknown"}},
        }, headers={"Idempotency-Key": "e2e-onboarding-0001"})
        self.assertEqual(200, onboarding.status_code, onboarding.text)
        evidence = self.client.post(f"/api/v1/profiles/{pid}/evidence", json={
            "domain": "dream", "type": "repeated_dream", "title": "test-only encrypted title",
            "raw_narrative": "test-only encrypted narrative", "structured_payload": {},
            "frequency": 4, "intensity": 6, "vividness": 7, "duration_years": 1,
            "source_type": "self_memory", "user_confidence": .6,
            "independent_corroboration": False, "possible_ordinary_explanations": ["stress"],
            "counterevidence": [],
        }, headers={"Idempotency-Key": "e2e-evidence-create-0001"})
        self.assertEqual(201, evidence.status_code, evidence.text)
        self.assertIn("not_past_life_evidence", evidence.json()["meaning"])
        completeness = self.client.get(f"/api/v1/profiles/{pid}/completeness")
        self.assertEqual("explicit_none", completeness.json()["dimensions"]["sensation"])
        tosses = [{"line_no": n, "coin_faces": ["heads", "tails", "tails"],
                   "was_retossed": False} for n in range(1, 7)]
        divination = self.client.post(f"/api/v1/profiles/{pid}/divinations/three-coin", json={
            "question": "test question", "purpose": "test purpose",
            "divination_at": datetime.now(timezone.utc).isoformat(), "timezone": "Asia/Shanghai",
            "location_precision": "none", "method_id": "YIJING.THREE_COIN.PHYSICAL.V1",
            "method_version": "1.0.0",
            "coin_face_mapping_id": "COIN_FACES.HEADS_3_TAILS_2.V1",
            "coin_face_mapping_version": "1.0.0", "tosses": tosses,
        }, headers={"Idempotency-Key": "e2e-three-coin-0001"})
        self.assertEqual(201, divination.status_code, divination.text)
        self.assertIsNone(divination.json()["interpretation"])
        self.assertIsNone(divination.json()["scoring"])
        self.assertEqual("research_active", divination.json()["research_status"])
        self.assertEqual(
            "bottom_to_top",
            divination.json()["engine_result"]["input_order"],
        )

    def test_knowledge_admin_is_owner_only_and_sealed_is_metadata_only(self):
        self.login()
        self.assertEqual(403, self.client.get("/api/v1/admin/knowledge/documents").status_code)
        owner_id, session_id, session_token = uuid4(), uuid4(), "owner-session-" + uuid4().hex
        self.admin.execute("INSERT INTO users(id,email_ciphertext,role) VALUES(%s,%s,'owner')",
                           (owner_id,b"owner"))
        self.admin.execute("""INSERT INTO sessions(id,user_id,token_hash,expires_at)
          VALUES(%s,%s,%s,%s)""",(session_id,owner_id,token_hash(session_token),
          datetime.now(timezone.utc)+timedelta(hours=1)))
        owner_client=TestClient(self.app_module.app,base_url="https://testserver")
        owner_client.cookies.set("__Host-session",session_token)
        sealed=owner_client.post("/api/v1/admin/knowledge/documents",json={
          "title":"restricted metadata test","traditions":["nyingma"],
          "knowledge_layer":"lineage_teaching","access_class":"sealed",
          "license":{},"notes":"must be rejected"},
          headers={"Idempotency-Key":"knowledge-sealed-reject-01"})
        self.assertEqual(422,sealed.status_code,sealed.text)
        created=owner_client.post("/api/v1/admin/knowledge/documents",json={
          "title":"metadata-only test","traditions":["engineering"],
          "knowledge_layer":"engineering_fact","access_class":"citation_only",
          "license":{}},
          headers={"Idempotency-Key":"knowledge-document-create-01"})
        self.assertEqual(201,created.status_code,created.text)
        self.assertFalse(created.json()["production_use"])

    def test_owner_only_research_preview_pipeline_is_replayable(self):
        self.login()
        self.assertEqual(403,self.client.get("/api/v1/admin/research/analyses").status_code)
        owner_id,session_id,profile_id,ruleset_id=uuid4(),uuid4(),uuid4(),uuid4()
        session_token="research-owner-"+uuid4().hex
        self.admin.execute("INSERT INTO users(id,email_ciphertext,role) VALUES(%s,%s,'owner')",(owner_id,b"owner"))
        self.admin.execute("INSERT INTO sessions(id,user_id,token_hash,expires_at) VALUES(%s,%s,%s,%s)",
          (session_id,owner_id,token_hash(session_token),datetime.now(timezone.utc)+timedelta(hours=1)))
        self.admin.execute("""INSERT INTO profiles(id,owner_id,timezone,calendar_type,birth_date_ciphertext,
          birth_time_precision,consent_version,research_profile) VALUES(%s,%s,'UTC','gregorian',%s,
          'unknown','research-fixture',true)""",(profile_id,owner_id,b"synthetic"))
        self.admin.execute("""INSERT INTO rulesets(id,name,version,status,checksum,manifest_json)
          VALUES(%s,%s,'0.1.0-research','draft',%s,%s)""",
          (ruleset_id,"research-fixture-"+uuid4().hex,"1"*64,
           json.dumps({"enabled":False,"production_activatable":False})))
        client=TestClient(self.app_module.app,base_url="https://testserver")
        client.cookies.set("__Host-session",session_token)
        payload={"profile_id":str(profile_id),"ruleset_id":str(ruleset_id),"mode":"research_preview",
          "synthetic_or_research":True,"is_synthetic":True,"random_seed":42,"completeness":.9,
          "ruleset_snapshot":{"version":"0.1.0-research"},"claim_snapshot":[],"signals":[
            {"id":str(uuid4()),"domain":domain,"tag":"caregiving","direction":"support","strength":.8,
             "source_reliability":.8,"relevance":.8,"independence_group":f"care-{domain}",
             "source_evidence_ids":[],"time_scope":{},"ordinary_explanation_present":False}
            for domain in ("karma","vow","dream")]}
        created=client.post("/api/v1/admin/research/analyses",json=payload,
          headers={"Idempotency-Key":"research-create-fixture-01"})
        self.assertEqual(201,created.status_code,created.text)
        analysis_id=created.json()["id"]
        run=client.post(f"/api/v1/admin/research/analyses/{analysis_id}/run",
          headers={"Idempotency-Key":"research-run-fixture-0001"})
        self.assertEqual(200,run.status_code,run.text)
        replay=client.post(f"/api/v1/admin/research/analyses/{analysis_id}/run",
          headers={"Idempotency-Key":"research-run-fixture-0001"})
        self.assertEqual(run.json()["locked_hash"],replay.json()["locked_hash"])
        report=client.get(f"/api/v1/admin/research/analyses/{analysis_id}/report")
        self.assertEqual("研究预览 · 非生产命盘",report.json()["banner"])
        retry=client.post(f"/api/v1/admin/research/analyses/{analysis_id}/retry-prose",
          headers={"Idempotency-Key":"research-retry-prose-01"})
        self.assertEqual(200,retry.status_code,retry.text)
        self.assertEqual("template",retry.json()["prose_source"])
        self.assertTrue(retry.json()["locked_verdict_unchanged"])

    def test_owner_bazi_four_pillars_is_engine_backed_encrypted_and_idempotent(self):
        self.login()
        owner_id, session_id, profile_id = uuid4(), uuid4(), uuid4()
        token = "bazi-owner-" + uuid4().hex
        self.admin.execute(
            "INSERT INTO users(id,email_ciphertext,role) VALUES(%s,%s,'owner')",
            (owner_id, b"owner"),
        )
        self.admin.execute(
            "INSERT INTO sessions(id,user_id,token_hash,expires_at) VALUES(%s,%s,%s,%s)",
            (session_id, owner_id, token_hash(token),
             datetime.now(timezone.utc) + timedelta(hours=1)),
        )
        self.admin.execute(
            """INSERT INTO profiles(id,owner_id,timezone,calendar_type,birth_date_ciphertext,
              birth_time_precision,consent_version,research_profile)
              VALUES(%s,%s,'Asia/Shanghai','gregorian',%s,'minute','research-fixture',true)""",
            (profile_id, owner_id, b"synthetic"),
        )
        client = TestClient(self.app_module.app, base_url="https://testserver")
        client.cookies.set("__Host-session", token)
        payload = {
            "profile_record_id": str(profile_id),
            "profile_id": "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
            "profile_version": "1.0.0",
            "birth_record": {
                "local_date": "2024-01-01", "local_time": "12:00:00",
                "calendar_type": "gregorian", "time_precision": "second",
                "timezone_id": "Asia/Shanghai",
                "place": {"latitude": "31.230400", "longitude": "121.473700",
                          "name": "Synthetic", "precision": "exact_test_coordinate"},
                "user_confirmed": True,
            },
            "input_provenance": {"all_fields": "synthetic_e2e"},
        }
        compare_payload = {
            "profiles": [{
                "profile_id": payload["profile_id"],
                "profile_version": payload["profile_version"],
            }],
            "birth_record": payload["birth_record"],
            "input_provenance": payload["input_provenance"],
        }
        blocked = self.client.post(
            "/api/v1/admin/research/bazi-four-pillars/compare",
            json=compare_payload,
        )
        self.assertEqual(403, blocked.status_code)
        headers = {"Idempotency-Key": "bazi-four-pillars-e2e-0001"}
        first = client.post(
            "/api/v1/admin/research/bazi-four-pillars/execute",
            json=payload, headers=headers,
        )
        self.assertEqual(201, first.status_code, first.text)
        body = first.json()
        self.assertEqual("研究预览 · 方法未审校 · 非生产命盘", body["banner"])
        bazi = body["result"]["module_results"]["bazi"]["result"]
        self.assertEqual("UNCONFIRMED", bazi["review_status"])
        self.assertFalse(bazi["production_activatable"])
        self.assertIsNone(bazi["interpretation"])
        replayed = client.post(
            "/api/v1/admin/research/bazi-four-pillars/execute",
            json=payload, headers=headers,
        )
        self.assertEqual(body["id"], replayed.json()["id"])
        row = self.admin.execute(
            """SELECT count(*),min(octet_length(input_snapshot_encrypted)),
              min(octet_length(engine_result_encrypted))
              FROM bazi_research_runs WHERE owner_id=%s""",
            (owner_id,),
        ).fetchone()
        self.assertEqual(1, row[0])
        self.assertGreater(row[1], 0)
        self.assertGreater(row[2], 0)
        comparison = client.post(
            "/api/v1/admin/research/bazi-four-pillars/compare",
            json={
                "profiles": [
                    {"profile_id": item, "profile_version": "1.0.0"}
                    for item in (
                        "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
                        "BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1",
                        "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
                    )
                ],
                "birth_record": payload["birth_record"],
                "input_provenance": payload["input_provenance"],
            },
        )
        self.assertEqual(200, comparison.status_code, comparison.text)
        self.assertEqual(3, len(comparison.json()["results"]))
