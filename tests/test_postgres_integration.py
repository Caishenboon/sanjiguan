import hashlib
import os
import threading
import subprocess
import sys
from pathlib import Path
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg

DSN = os.getenv("TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(DSN, "real PostgreSQL integration runs in CI")
class PostgreSQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(DSN, autocommit=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.execute("TRUNCATE users CASCADE")
        cls.conn.close()

    def setUp(self):
        self.conn.execute("TRUNCATE users CASCADE")
        self.member_a, self.member_b, self.viewer, self.owner = (uuid4() for _ in range(4))
        for uid, role in ((self.member_a, "member"), (self.member_b, "member"),
                          (self.viewer, "viewer"), (self.owner, "owner")):
            self.conn.execute(
                "INSERT INTO users(id,email_ciphertext,role) VALUES (%s,%s,%s)",
                (uid, str(uid).encode(), role),
            )
        self.profile_a, self.profile_b = uuid4(), uuid4()
        for pid, uid in ((self.profile_a, self.member_a), (self.profile_b, self.member_b)):
            self.conn.execute(
                """INSERT INTO profiles(id,owner_id,timezone,calendar_type,birth_date_ciphertext,
                   birth_time_precision,consent_version) VALUES(%s,%s,'Asia/Shanghai','gregorian',
                   '\\x31','unknown','1.0')""", (pid, uid)
            )

    def runtime(self, uid, role="member"):
        conn = psycopg.connect(DSN)
        conn.execute("SET ROLE app_runtime")
        conn.execute("SELECT set_config('app.current_user_id', %s, false)", (str(uid),))
        conn.execute("SELECT set_config('app.current_user_role', %s, false)", (role,))
        return conn

    def test_runtime_role_and_force_rls(self):
        row = self.conn.execute(
            "SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname='app_runtime'"
        ).fetchone()
        self.assertEqual((False, False), row)
        owner = self.conn.execute(
            "SELECT tableowner <> 'app_runtime' FROM pg_tables WHERE tablename='profiles'"
        ).fetchone()[0]
        forced = self.conn.execute(
            "SELECT relforcerowsecurity FROM pg_class WHERE relname='profiles'"
        ).fetchone()[0]
        self.assertTrue(owner and forced)
        rank_unique = self.conn.execute(
            """SELECT count(*) FROM pg_constraint
               WHERE conrelid='structured_verdicts'::regclass AND contype='u'"""
        ).fetchone()[0]
        self.assertEqual(1, rank_unique)

    def test_sprint1b1_tables_force_rls_and_isolate_evidence(self):
        tables = ("onboarding_sessions", "evidence_revisions", "life_events",
                  "journal_evidence_links", "divination_sessions", "coin_tosses",
                  "profile_completeness_snapshots")
        rows = self.conn.execute(
            """SELECT relname,relforcerowsecurity FROM pg_class
               WHERE relname=ANY(%s) ORDER BY relname""", (list(tables),)
        ).fetchall()
        self.assertEqual(set(tables), {row[0] for row in rows})
        self.assertTrue(all(row[1] for row in rows))

        evidence_id = uuid4()
        with self.runtime(self.member_a) as member:
            member.execute(
                """INSERT INTO evidence_items(id,profile_id,type,payload_encrypted,
                   source_reliability,domain,title_ciphertext,structured_payload_encrypted,
                   source_type,user_confidence,reliability_score,reliability_level)
                   VALUES(%s,%s,'dream',%s,.5,'dream',%s,%s,'self_memory',.5,.5,'medium')""",
                (evidence_id, self.profile_a, b"encrypted", b"encrypted", b"encrypted"),
            )
            member.commit()
        with self.runtime(self.member_b) as other:
            self.assertIsNone(other.execute(
                "SELECT id FROM evidence_items WHERE id=%s", (evidence_id,)
            ).fetchone())
        with self.runtime(self.member_a) as member:
            self.assertEqual(evidence_id, member.execute(
                "SELECT id FROM evidence_items WHERE id=%s", (evidence_id,)
            ).fetchone()[0])

    def test_migration_drift_is_rejected(self):
        version = "0001_sprint0_baseline.sql"
        checksum = self.conn.execute(
            "SELECT checksum FROM schema_migrations WHERE version=%s", (version,)
        ).fetchone()[0]
        self.conn.execute("UPDATE schema_migrations SET checksum=%s WHERE version=%s",
                          ("0" * 64, version))
        try:
            env = dict(os.environ, DATABASE_URL=DSN)
            result = subprocess.run([sys.executable, "scripts/migrate.py"], cwd=ROOT,
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("migration drift", result.stdout + result.stderr)
        finally:
            self.conn.execute("UPDATE schema_migrations SET checksum=%s WHERE version=%s",
                              (checksum, version))

    def test_member_isolation_owner_and_viewer_revocation(self):
        with self.runtime(self.member_a) as c:
            self.assertEqual([(self.profile_a,)], c.execute("SELECT id FROM profiles").fetchall())
            self.assertIsNone(c.execute("SELECT id FROM profiles WHERE id=%s", (self.profile_b,)).fetchone())
        with self.runtime(self.owner, "owner") as c:
            self.assertEqual(2, c.execute("SELECT count(*) FROM profiles").fetchone()[0])
        grant_id = uuid4()
        self.conn.execute(
            """INSERT INTO profile_grants(id,profile_id,grantee_user_id,permission,granted_by)
               VALUES(%s,%s,%s,'read',%s)""",
            (grant_id, self.profile_a, self.viewer, self.member_a),
        )
        with self.runtime(self.viewer, "viewer") as c:
            self.assertEqual(self.profile_a, c.execute("SELECT id FROM profiles").fetchone()[0])
            self.assertEqual(0, c.execute("SELECT count(*) FROM relationship_subjects").fetchone()[0])
            changed = c.execute(
                "UPDATE profiles SET consent_version='x' WHERE id=%s", (self.profile_a,)
            ).rowcount
            self.assertEqual(0, changed)
        self.conn.execute(
            "UPDATE profile_grants SET status='revoked',revoked_at=now() WHERE id=%s", (grant_id,)
        )
        with self.runtime(self.viewer, "viewer") as c:
            self.assertEqual(0, c.execute("SELECT count(*) FROM profiles").fetchone()[0])

    def test_concurrent_idempotency_single_write_and_user_scope(self):
        key_hash = hashlib.sha256(b"same-key").hexdigest()
        fingerprint = hashlib.sha256(b"same-request").hexdigest()
        barrier = threading.Barrier(2)
        results = []
        def insert():
            with self.runtime(self.member_a) as c:
                barrier.wait()
                row = c.execute(
                    """INSERT INTO idempotency_records
                       (id,owner_id,http_method,route_template,key_hash,request_fingerprint,state,created_at,expires_at)
                       VALUES(%s,%s,'POST','/profiles',%s,%s,'processing',now(),now()+interval '24 hours')
                       ON CONFLICT(owner_id,http_method,route_template,key_hash) DO NOTHING RETURNING id""",
                    (uuid4(), self.member_a, key_hash, fingerprint),
                ).fetchone()
                if row is not None:
                    c.execute(
                        """INSERT INTO evidence_items
                           (id,profile_id,type,payload_encrypted,source_reliability)
                           VALUES(%s,%s,'concurrency_fixture',%s,1)""",
                        (uuid4(), self.profile_a, b"encrypted-fixture"),
                    )
                results.append(row is not None)
        threads = [threading.Thread(target=insert) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual([False, True], sorted(results))
        self.assertEqual(1, self.conn.execute(
            "SELECT count(*) FROM evidence_items WHERE profile_id=%s AND type='concurrency_fixture'",
            (self.profile_a,),
        ).fetchone()[0])
        with self.runtime(self.member_b) as c:
            c.execute(
                """INSERT INTO idempotency_records
                   (id,owner_id,http_method,route_template,key_hash,request_fingerprint,state,created_at,expires_at)
                   VALUES(%s,%s,'POST','/profiles',%s,%s,'processing',now(),now()+interval '24 hours')""",
                (uuid4(), self.member_b, key_hash, fingerprint),
            )

    def test_transaction_rollback_and_consent_withdrawal(self):
        with self.assertRaises(RuntimeError):
            with self.runtime(self.member_a) as c:
                c.execute("UPDATE profiles SET consent_version='changed' WHERE id=%s", (self.profile_a,))
                raise RuntimeError("rollback")
        self.assertEqual("1.0", self.conn.execute(
            "SELECT consent_version FROM profiles WHERE id=%s", (self.profile_a,)
        ).fetchone()[0])
        subject_id, consent_id = uuid4(), uuid4()
        self.conn.execute(
            """INSERT INTO relationship_subjects(id,profile_id,mode)
               VALUES(%s,%s,'anonymous_event')""", (subject_id, self.profile_a)
        )
        self.conn.execute(
            """INSERT INTO relationship_consents
               (id,subject_id,consent_version,consent_status,evidence_type,scope_json,
                consented_at,created_by)
               VALUES(%s,%s,'1.0','granted','self_attestation','["dual_analysis"]',now(),%s)""",
            (consent_id, subject_id, self.member_a),
        )
        with self.runtime(self.member_b) as c:
            self.assertEqual(0, c.execute(
                "SELECT count(*) FROM relationship_subjects WHERE id=%s", (subject_id,)
            ).fetchone()[0])
        with self.runtime(self.member_a) as c:
            changed = c.execute(
                """UPDATE relationship_consents SET consent_status='withdrawn',withdrawn_at=now()
                   WHERE id=%s""", (consent_id,)
            ).rowcount
            self.assertEqual(1, changed)
        self.assertEqual("withdrawn", self.conn.execute(
            "SELECT consent_status FROM relationship_consents WHERE id=%s", (consent_id,)
        ).fetchone()[0])
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conn.execute(
                "INSERT INTO relationship_analysis_requests(id,subject_id,requested_by) VALUES(%s,%s,%s)",
                (uuid4(), subject_id, self.member_a),
            )
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conn.execute(
                """INSERT INTO relationship_subjects(id,profile_id,mode,alias_ciphertext)
                   VALUES(%s,%s,'anonymous_event',%s)""",
                (uuid4(), self.profile_a, b"identifiable-counterparty"),
            )
