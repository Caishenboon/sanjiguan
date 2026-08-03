CREATE TABLE IF NOT EXISTS traditional_complete_runs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_record_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  parent_run_id uuid REFERENCES traditional_complete_runs(id) ON DELETE SET NULL,
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id='sanji-traditional-composite-1.0.0'),
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
  created_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz
);
CREATE INDEX IF NOT EXISTS traditional_complete_runs_owner_created_idx ON traditional_complete_runs(owner_id,created_at DESC);
ALTER TABLE traditional_complete_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE traditional_complete_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS traditional_complete_runs_owner ON traditional_complete_runs;
CREATE POLICY traditional_complete_runs_owner ON traditional_complete_runs FOR ALL TO app_runtime
  USING (owner_id=app_current_user_id() AND app_current_user_role()='owner')
  WITH CHECK (owner_id=app_current_user_id() AND app_current_user_role()='owner');
REVOKE ALL ON traditional_complete_runs FROM app_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON traditional_complete_runs TO app_runtime;
COMMENT ON TABLE traditional_complete_runs IS 'Encrypted complete traditional V1 research runs; never production-activatable.';
