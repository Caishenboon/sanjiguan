import unittest
import os
from datetime import datetime, timezone

from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("STORAGE_BACKEND", "memory")
from apps.api.app.main import app
from apps.api.app.services.store import store


class ApiTests(unittest.TestCase):
    def setUp(self):
        store.users.clear()
        store.invitations.clear()
        store.sessions.clear()
        store.profiles.clear()
        store.idempotency.clear()
        self.client = TestClient(app, base_url="https://testserver")
        token = store.create_invitation()
        response = self.client.post("/api/v1/auth/invitations/accept", json={"token": token})
        self.assertEqual(200, response.status_code)

    def profile_payload(self, name="observer"):
        return {
            "display_name": name,
            "consent_version": "1.0",
            "birth": {
                "calendar_type": "gregorian",
                "local_date": "1990-01-15",
                "local_time": "08:30:00",
                "timezone_id": "Asia/Shanghai",
                "timezone_database": "IANA",
                "timezone_database_version": "2026c",
                "time_precision": "minute",
                "place": {
                    "label": "Shanghai",
                    "latitude": 31.2304,
                    "longitude": 121.4737,
                    "coordinate_source": "user_confirmed"
                },
                "user_confirmed": True,
                "captured_at": datetime.now(timezone.utc).isoformat()
            }
        }

    def test_invitation_is_single_use_and_cookie_is_secure(self):
        token = store.create_invitation()
        first = self.client.post("/api/v1/auth/invitations/accept", json={"token": token})
        self.assertEqual(200, first.status_code)
        cookie = first.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=strict", cookie)
        second = self.client.post("/api/v1/auth/invitations/accept", json={"token": token})
        self.assertEqual(422, second.status_code)

    def test_profile_crud_and_idempotent_replay(self):
        headers = {"Idempotency-Key": "create-profile-key-0001"}
        payload = self.profile_payload()
        first = self.client.post("/api/v1/profiles", json=payload, headers=headers)
        self.assertEqual(201, first.status_code, first.text)
        replay = self.client.post("/api/v1/profiles", json=payload, headers=headers)
        self.assertEqual(201, replay.status_code)
        self.assertEqual(first.json()["id"], replay.json()["id"])
        profile_id = first.json()["id"]
        fetched = self.client.get(f"/api/v1/profiles/{profile_id}")
        self.assertEqual(200, fetched.status_code)
        patch = self.client.patch(
            f"/api/v1/profiles/{profile_id}",
            json={"display_name": "updated"},
            headers={"Idempotency-Key": "patch-profile-key-0001"},
        )
        self.assertEqual(200, patch.status_code)
        deleted = self.client.delete(
            f"/api/v1/profiles/{profile_id}",
            headers={"Idempotency-Key": "delete-profile-key-01"},
        )
        self.assertEqual(202, deleted.status_code)

    def test_same_key_different_payload_is_409(self):
        headers = {"Idempotency-Key": "conflicting-key-00001"}
        self.assertEqual(201, self.client.post("/api/v1/profiles", json=self.profile_payload("a"), headers=headers).status_code)
        conflict = self.client.post("/api/v1/profiles", json=self.profile_payload("b"), headers=headers)
        self.assertEqual(409, conflict.status_code)

    def test_normalization_endpoint_has_no_chart_conclusion(self):
        created = self.client.post(
            "/api/v1/profiles",
            json=self.profile_payload(),
            headers={"Idempotency-Key": "create-for-normalize"},
        )
        response = self.client.post(
            f"/api/v1/profiles/{created.json()['id']}/birth-time/normalize",
            json={"solar_term_instants_utc": []},
            headers={"Idempotency-Key": "normalize-profile-001"},
        )
        self.assertEqual(200, response.status_code, response.text)
        body = response.json()
        self.assertTrue(all(not item["is_primary_chart"] for item in body["candidates"]))
        self.assertIn("不得据此选择命理主盘", body["prohibited_conclusions"])


if __name__ == "__main__":
    unittest.main()
