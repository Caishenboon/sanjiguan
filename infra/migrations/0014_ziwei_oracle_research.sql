-- Owner-only Ziwei mechanical research runs and differential Oracle summaries.
-- Additive only: no historical backfill, inferred manifests, default Profile,
-- third-party result promotion, or production activation.
CREATE TABLE IF NOT EXISTS ziwei_research_runs (
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
  domain_hash text NOT NULL CHECK (domain_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_manifest_hash text NOT NULL CHECK (replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  ruleset_bundle_id text NOT NULL,
  ruleset_bundle_hash text NOT NULL CHECK (ruleset_bundle_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  CHECK (method_profile_id LIKE 'ZIWEI.%'),
  CHECK (ruleset_bundle_id = 'ziwei-sanhe-research-1.0.0')
);

CREATE TABLE IF NOT EXISTS oracle_diff_summaries (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  engine_run_kind text NOT NULL CHECK (engine_run_kind IN ('bazi','ziwei','yijing')),
  engine_run_id uuid NOT NULL,
  oracle_id text NOT NULL,
  oracle_version text NOT NULL,
  diff_status text NOT NULL CHECK (diff_status IN (
    'exact_match','normalized_match','profile_difference','unsupported',
    'external_error','engine_suspect','oracle_suspect','manual_review_required'
  )),
  diff_hash text NOT NULL CHECK (diff_hash ~ '^sha256:[a-f0-9]{64}$'),
  oracle_result_hash text NOT NULL CHECK (oracle_result_hash ~ '^sha256:[a-f0-9]{64}$'),
  summary jsonb NOT NULL,
  affects_engine_result boolean NOT NULL DEFAULT false CHECK (NOT affects_engine_result),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ziwei_research_runs_owner_created_idx
  ON ziwei_research_runs(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS oracle_diff_summaries_owner_created_idx
  ON oracle_diff_summaries(owner_id, created_at DESC);

ALTER TABLE ziwei_research_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ziwei_research_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE oracle_diff_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE oracle_diff_summaries FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ziwei_research_runs_owner_policy ON ziwei_research_runs;
CREATE POLICY ziwei_research_runs_owner_policy ON ziwei_research_runs
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (
    owner_id = app_current_user_id() AND app_current_user_role() = 'owner'
    AND (profile_record_id IS NULL OR EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = profile_record_id AND p.owner_id = app_current_user_id()
    ))
  );

DROP POLICY IF EXISTS oracle_diff_summaries_owner_policy ON oracle_diff_summaries;
CREATE POLICY oracle_diff_summaries_owner_policy ON oracle_diff_summaries
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (owner_id = app_current_user_id() AND app_current_user_role() = 'owner');

REVOKE ALL ON ziwei_research_runs, oracle_diff_summaries FROM app_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ziwei_research_runs, oracle_diff_summaries TO app_runtime;

COMMENT ON TABLE ziwei_research_runs IS
  'Owner-only UNCONFIRMED Ziwei research charts; encrypted domain payload and replay evidence.';
COMMENT ON TABLE oracle_diff_summaries IS
  'Differential evidence only; never a Sanji Engine result or source of production truth.';
