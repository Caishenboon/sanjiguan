import importlib
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
            "method_version": "1.0.0", "tosses": tosses,
        }, headers={"Idempotency-Key": "e2e-three-coin-0001"})
        self.assertEqual(201, divination.status_code, divination.text)
        self.assertIsNone(divination.json()["interpretation"])
        self.assertIsNone(divination.json()["scoring"])
