-- Pinned upstream research executions. Payloads remain encrypted; no result is production truth.
CREATE TABLE IF NOT EXISTS upstream_traditional_runs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_record_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  parent_run_id uuid REFERENCES upstream_traditional_runs(id) ON DELETE SET NULL,
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id='sanji-upstream-composite-1.0.0'),
  research_status text NOT NULL CHECK (research_status='research_active'),
  review_status text NOT NULL CHECK (review_status='UNCONFIRMED'),
  production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable),
  input_snapshot_encrypted bytea NOT NULL,
  result_encrypted bytea NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  output_hash text NOT NULL CHECK (output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text NOT NULL CHECK (trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  evidence_graph_hash text NOT NULL CHECK (evidence_graph_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_manifest_hash text NOT NULL CHECK (replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE INDEX IF NOT EXISTS upstream_traditional_runs_owner_created_idx
  ON upstream_traditional_runs(owner_id,created_at DESC);
ALTER TABLE upstream_traditional_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE upstream_traditional_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS upstream_traditional_runs_owner ON upstream_traditional_runs;
CREATE POLICY upstream_traditional_runs_owner ON upstream_traditional_runs FOR ALL TO app_runtime
  USING (owner_id=app_current_user_id() AND app_current_user_role()='owner')
  WITH CHECK (owner_id=app_current_user_id() AND app_current_user_role()='owner'
    AND (profile_record_id IS NULL OR EXISTS(
      SELECT 1 FROM profiles p WHERE p.id=profile_record_id AND p.owner_id=app_current_user_id()
    )));
REVOKE ALL ON upstream_traditional_runs FROM app_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON upstream_traditional_runs TO app_runtime;
COMMENT ON TABLE upstream_traditional_runs IS
  'Encrypted owner-only pinned-upstream research executions; UNCONFIRMED and never production-activatable.';
