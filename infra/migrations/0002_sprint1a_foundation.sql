-- Sprint 1A security, authorization, idempotency, and time audit structures.
-- Must be applied by migration_owner. app_runtime must never own tables.
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime') THEN
    CREATE ROLE app_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
  END IF;
END
$$;

CREATE TABLE invitations (
  id uuid PRIMARY KEY,
  token_hash text NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
  invited_email_ciphertext bytea,
  role text NOT NULL CHECK (role IN ('member','viewer')),
  issued_by uuid NOT NULL REFERENCES users(id),
  expires_at timestamptz NOT NULL,
  accepted_by uuid REFERENCES users(id),
  accepted_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (expires_at > created_at)
);

CREATE TABLE sessions (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash text NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz,
  CHECK (expires_at > created_at)
);

CREATE TABLE profile_grants (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  grantee_user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  permission text NOT NULL CHECK (permission = 'read'),
  granted_by uuid NOT NULL REFERENCES users(id),
  expires_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(profile_id, grantee_user_id)
);

CREATE TABLE idempotency_records (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  http_method text NOT NULL CHECK (http_method IN ('POST','PATCH','DELETE')),
  route_template text NOT NULL,
  key_hash text NOT NULL CHECK (key_hash ~ '^[a-f0-9]{64}$'),
  request_fingerprint text NOT NULL CHECK (request_fingerprint ~ '^[a-f0-9]{64}$'),
  state text NOT NULL CHECK (state IN ('processing','completed','failed')),
  status_code integer,
  response_encrypted bytea,
  resource_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  UNIQUE(owner_id, http_method, route_template, key_hash),
  CHECK (expires_at <= created_at + interval '24 hours')
);

CREATE TABLE birth_time_normalizations (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  method_version text NOT NULL,
  tzdb_version text NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^[a-f0-9]{64}$'),
  original_record_encrypted bytea NOT NULL,
  historical_utc_offset_minutes integer,
  dst_offset_minutes integer,
  longitude_correction_minutes numeric(10,6),
  equation_of_time_minutes numeric(10,6),
  total_apparent_correction_minutes numeric(10,6),
  candidates_json jsonb NOT NULL,
  boundary_difference_json jsonb NOT NULL,
  correction_chain_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(profile_id, method_version, input_hash)
);

CREATE TABLE relationship_consents (
  id uuid PRIMARY KEY,
  subject_id uuid NOT NULL REFERENCES relationship_subjects(id) ON DELETE CASCADE,
  consent_version text NOT NULL,
  status text NOT NULL CHECK (status IN ('active','revoked','expired')),
  proof_type text NOT NULL CHECK (proof_type IN ('self_attestation','signed_record','linked_profile_confirmation')),
  scope_json jsonb NOT NULL,
  consented_at timestamptz NOT NULL,
  expires_at timestamptz,
  revoked_at timestamptz,
  record_encrypted bytea NOT NULL,
  record_hash text NOT NULL CHECK (record_hash ~ '^[a-f0-9]{64}$'),
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((status = 'revoked') = (revoked_at IS NOT NULL))
);

CREATE INDEX invitations_issued_created_idx ON invitations(issued_by, created_at);
CREATE INDEX sessions_user_created_idx ON sessions(user_id, created_at);
CREATE INDEX grants_profile_grantee_idx ON profile_grants(profile_id, grantee_user_id);
CREATE INDEX idempotency_owner_created_idx ON idempotency_records(owner_id, created_at);
CREATE INDEX normalization_profile_created_idx ON birth_time_normalizations(profile_id, created_at);
CREATE INDEX consents_subject_created_idx ON relationship_consents(subject_id, created_at);

ALTER TABLE profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_items FORCE ROW LEVEL SECURITY;
ALTER TABLE chart_snapshots FORCE ROW LEVEL SECURITY;
ALTER TABLE analysis_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE relationship_subjects FORCE ROW LEVEL SECURITY;
ALTER TABLE journal_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE profile_versions FORCE ROW LEVEL SECURITY;

ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations FORCE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE profile_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_grants FORCE ROW LEVEL SECURITY;
ALTER TABLE idempotency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_records FORCE ROW LEVEL SECURITY;
ALTER TABLE birth_time_normalizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE birth_time_normalizations FORCE ROW LEVEL SECURITY;
ALTER TABLE relationship_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE relationship_consents FORCE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION app_current_user_id() RETURNS uuid
LANGUAGE sql STABLE LEAKPROOF
RETURN nullif(current_setting('app.current_user_id', true), '')::uuid;

DROP POLICY IF EXISTS profiles_owner_policy ON profiles;
CREATE POLICY profiles_member_owner_select ON profiles FOR SELECT TO app_runtime
USING (
  owner_id = app_current_user_id()
  OR EXISTS (
    SELECT 1 FROM profile_grants g
    WHERE g.profile_id = profiles.id
      AND g.grantee_user_id = app_current_user_id()
      AND g.permission = 'read'
      AND g.revoked_at IS NULL
      AND (g.expires_at IS NULL OR g.expires_at > now())
  )
);
CREATE POLICY profiles_member_owner_modify ON profiles FOR ALL TO app_runtime
USING (owner_id = app_current_user_id())
WITH CHECK (owner_id = app_current_user_id());

DROP POLICY IF EXISTS evidence_owner_policy ON evidence_items;
CREATE POLICY evidence_visible_profile ON evidence_items FOR SELECT TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id));
CREATE POLICY evidence_owner_modify ON evidence_items FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()));

DROP POLICY IF EXISTS charts_owner_policy ON chart_snapshots;
CREATE POLICY charts_visible_profile ON chart_snapshots FOR SELECT TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id));
CREATE POLICY charts_owner_modify ON chart_snapshots FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()));

DROP POLICY IF EXISTS runs_owner_policy ON analysis_runs;
CREATE POLICY runs_visible_profile ON analysis_runs FOR SELECT TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id));
CREATE POLICY runs_owner_modify ON analysis_runs FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()));

CREATE POLICY sessions_self ON sessions FOR ALL TO app_runtime
USING (user_id = app_current_user_id()) WITH CHECK (user_id = app_current_user_id());
CREATE POLICY grants_visible_owner_or_grantee ON profile_grants FOR SELECT TO app_runtime
USING (
  grantee_user_id = app_current_user_id()
  OR EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id())
);
CREATE POLICY grants_owner_modify ON profile_grants FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()));
CREATE POLICY idempotency_self ON idempotency_records FOR ALL TO app_runtime
USING (owner_id = app_current_user_id()) WITH CHECK (owner_id = app_current_user_id());
CREATE POLICY normalization_visible_profile ON birth_time_normalizations FOR SELECT TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id));
CREATE POLICY normalization_owner_modify ON birth_time_normalizations FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND p.owner_id = app_current_user_id()));

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON
  profiles, evidence_items, chart_snapshots, analysis_runs, relationship_subjects,
  journal_entries, profile_versions, sessions, profile_grants, idempotency_records,
  birth_time_normalizations, relationship_consents
TO app_runtime;

COMMIT;
