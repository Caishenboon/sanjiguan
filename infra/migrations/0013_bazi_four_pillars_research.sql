-- Owner-only BaZi mechanical research runs. Additive: no historical backfill,
-- inferred manifest, default method profile, or production activation.
CREATE TABLE IF NOT EXISTS bazi_research_runs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_record_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  method_profile_id text NOT NULL,
  method_profile_version text NOT NULL,
  research_status text NOT NULL CHECK (research_status = 'research_active'),
  review_status text NOT NULL CHECK (review_status = 'UNCONFIRMED'),
  input_snapshot_encrypted bytea NOT NULL,
  engine_result_encrypted bytea NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  output_hash text NOT NULL CHECK (output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text NOT NULL CHECK (trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_manifest_hash text NOT NULL CHECK (replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  ruleset_bundle_id text NOT NULL,
  ruleset_bundle_hash text NOT NULL CHECK (ruleset_bundle_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CHECK (method_profile_id LIKE 'BAZI.PROFILE.%'),
  CHECK (ruleset_bundle_id = 'bazi-four-pillars-research-1.0.0')
);

CREATE INDEX IF NOT EXISTS bazi_research_runs_owner_created_idx
  ON bazi_research_runs(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS bazi_research_runs_profile_created_idx
  ON bazi_research_runs(profile_record_id, created_at DESC);

ALTER TABLE bazi_research_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bazi_research_runs FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS bazi_research_runs_owner_policy ON bazi_research_runs;
CREATE POLICY bazi_research_runs_owner_policy ON bazi_research_runs
  FOR ALL TO app_runtime
  USING (
    owner_id = app_current_user_id()
    AND app_current_user_role() = 'owner'
  )
  WITH CHECK (
    owner_id = app_current_user_id()
    AND app_current_user_role() = 'owner'
    AND (
      profile_record_id IS NULL
      OR EXISTS (
        SELECT 1 FROM profiles p
        WHERE p.id = profile_record_id AND p.owner_id = app_current_user_id()
      )
    )
  );

REVOKE ALL ON bazi_research_runs FROM app_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON bazi_research_runs TO app_runtime;

COMMENT ON TABLE bazi_research_runs IS
  'Owner-only UNCONFIRMED research results; encrypted payloads and explicit replay manifest; never a production chart.';
