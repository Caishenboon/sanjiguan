-- Sprint 18: deterministic life trend, K-line and controlled report storage.
-- Private snapshots and prose remain encrypted; hashes are over canonical plaintext.
BEGIN;

CREATE TABLE life_trend_ruleset_versions (
  id uuid PRIMARY KEY,
  ruleset_id text NOT NULL,
  version text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[a-f0-9]{64}$'),
  tradition_scope text NOT NULL CHECK (tradition_scope = 'sanji_original'),
  activation text NOT NULL CHECK (activation = 'research_active'),
  review_status text NOT NULL CHECK (review_status = 'UNCONFIRMED'),
  production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(ruleset_id, version)
);

INSERT INTO life_trend_ruleset_versions(
  id,ruleset_id,version,content_hash,tradition_scope,activation,
  review_status,production_activatable
) VALUES (
  '019fa02b-a48f-7bb0-8a18-000000000018',
  'life-trend-rules','1.0.0',
  'sha256:b3dbfc721afc398524c52bad2429b6f85a2e9515f8537411b63e37315f433e3a',
  'sanji_original','research_active','UNCONFIRMED',false
) ON CONFLICT(ruleset_id,version) DO NOTHING;

CREATE TABLE life_trend_executions (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  parent_execution_id uuid REFERENCES life_trend_executions(id) ON DELETE SET NULL,
  execution_kind text NOT NULL CHECK (execution_kind IN ('initial','reanalysis')),
  input_snapshot_encrypted bytea,
  core_result_encrypted bytea NOT NULL,
  deterministic_report_encrypted bytea NOT NULL,
  ai_narrative_encrypted bytea,
  engine_version text NOT NULL,
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id = 'life-trend-research-v1.0.0'),
  life_trend_ruleset_version text NOT NULL,
  evidence_policy_version text NOT NULL,
  report_template_version text NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  core_output_hash text NOT NULL CHECK (core_output_hash ~ '^sha256:[a-f0-9]{64}$'),
  deterministic_report_hash text NOT NULL CHECK (deterministic_report_hash ~ '^sha256:[a-f0-9]{64}$'),
  narrative_input_hash text CHECK (narrative_input_hash IS NULL OR narrative_input_hash ~ '^sha256:[a-f0-9]{64}$'),
  narrative_output_hash text CHECK (narrative_output_hash IS NULL OR narrative_output_hash ~ '^sha256:[a-f0-9]{64}$'),
  output_hash text NOT NULL CHECK (output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text NOT NULL CHECK (trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_available boolean NOT NULL DEFAULT true,
  replay_unavailable_reason text,
  snapshot_purged_at timestamptz,
  ai_status text NOT NULL DEFAULT 'not_requested'
    CHECK (ai_status IN ('not_requested','accepted','rejected','fallback','provider_failed')),
  ai_provider text,
  ai_model text,
  prompt_version text,
  ai_generated_at timestamptz,
  status text NOT NULL CHECK (status IN ('decisive','provisional','contested','insufficient')),
  research_notice text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (replay_available AND replay_unavailable_reason IS NULL AND snapshot_purged_at IS NULL)
    OR
    (NOT replay_available AND replay_unavailable_reason IS NOT NULL AND snapshot_purged_at IS NOT NULL)
  )
);

CREATE TABLE life_trend_buckets (
  execution_id uuid NOT NULL REFERENCES life_trend_executions(id) ON DELETE CASCADE,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  bucket_id text NOT NULL,
  sequence_no integer NOT NULL CHECK (sequence_no >= 0),
  -- Precision-preserving canonical labels. A year/quarter/month must never be
  -- coerced to an invented calendar day merely to satisfy a DATE column.
  starts_on text NOT NULL,
  ends_on text NOT NULL,
  time_precision text NOT NULL CHECK (
    time_precision IN ('exact_date','month_only','quarter','year_only','phase')
  ),
  segment text NOT NULL CHECK (
    segment IN ('observed_past','current_state','projected_future','insufficient_gap')
  ),
  candle jsonb,
  confidence_bp integer NOT NULL CHECK (confidence_bp BETWEEN 0 AND 10000),
  coverage_bp integer NOT NULL CHECK (coverage_bp BETWEEN 0 AND 10000),
  trace_ref text NOT NULL,
  PRIMARY KEY(execution_id,bucket_id)
);

CREATE TABLE life_trend_timing_windows (
  execution_id uuid NOT NULL REFERENCES life_trend_executions(id) ON DELETE CASCADE,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  window_id text NOT NULL,
  starts_on text NOT NULL,
  ends_on text NOT NULL,
  precision text NOT NULL CHECK (
    precision IN ('exact_date','month_only','quarter','year_only','phase')
  ),
  window_type text NOT NULL,
  strength_bp integer NOT NULL CHECK (strength_bp BETWEEN 0 AND 10000),
  confidence_bp integer NOT NULL CHECK (confidence_bp BETWEEN 0 AND 10000),
  status text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY(execution_id,window_id)
);

CREATE TABLE life_trend_replay_records (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  execution_id uuid NOT NULL REFERENCES life_trend_executions(id) ON DELETE CASCADE,
  replay_core_output_hash text NOT NULL CHECK (replay_core_output_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_trace_hash text NOT NULL CHECK (replay_trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  matched boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE life_trend_execution_comparisons (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  left_execution_id uuid NOT NULL REFERENCES life_trend_executions(id) ON DELETE CASCADE,
  right_execution_id uuid NOT NULL REFERENCES life_trend_executions(id) ON DELETE CASCADE,
  difference_summary jsonb NOT NULL,
  comparison_hash text NOT NULL CHECK (comparison_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (left_execution_id <> right_execution_id)
);

ALTER TABLE sanji_archive_entries
  ADD COLUMN life_trend_execution_id uuid REFERENCES life_trend_executions(id) ON DELETE SET NULL;
ALTER TABLE sanji_archive_entries DROP CONSTRAINT sanji_archive_entries_entry_type_check;
ALTER TABLE sanji_archive_entries ADD CONSTRAINT sanji_archive_entries_entry_type_check
  CHECK (entry_type IN (
    'record','mechanical_result','liuxiang_research','topic_research','life_trend_report'
  ));

CREATE INDEX life_trend_profile_idx
  ON life_trend_executions(profile_id,created_at DESC);

ALTER TABLE life_trend_ruleset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_ruleset_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE life_trend_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_executions FORCE ROW LEVEL SECURITY;
ALTER TABLE life_trend_buckets ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_buckets FORCE ROW LEVEL SECURITY;
ALTER TABLE life_trend_timing_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_timing_windows FORCE ROW LEVEL SECURITY;
ALTER TABLE life_trend_replay_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_replay_records FORCE ROW LEVEL SECURITY;
ALTER TABLE life_trend_execution_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_trend_execution_comparisons FORCE ROW LEVEL SECURITY;

CREATE POLICY life_trend_ruleset_read ON life_trend_ruleset_versions
  FOR SELECT TO app_runtime USING (true);
CREATE POLICY life_trend_execution_owner ON life_trend_executions
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = profile_id AND p.owner_id = app_current_user_id() AND p.deleted_at IS NULL
    )
  );
CREATE POLICY life_trend_bucket_owner ON life_trend_buckets
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM life_trend_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY life_trend_window_owner ON life_trend_timing_windows
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM life_trend_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY life_trend_replay_owner ON life_trend_replay_records
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM life_trend_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY life_trend_comparison_owner ON life_trend_execution_comparisons
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM life_trend_executions e
      WHERE e.id IN (left_execution_id,right_execution_id)
      GROUP BY e.owner_id HAVING count(*) = 2 AND e.owner_id = app_current_user_id()
    )
  );

REVOKE ALL ON life_trend_ruleset_versions,life_trend_executions,
  life_trend_buckets,life_trend_timing_windows,life_trend_replay_records,
  life_trend_execution_comparisons FROM app_runtime;
GRANT SELECT ON life_trend_ruleset_versions TO app_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON life_trend_executions,life_trend_buckets,
  life_trend_timing_windows,life_trend_replay_records,
  life_trend_execution_comparisons TO app_runtime;

COMMENT ON TABLE life_trend_executions IS
  'Encrypted deterministic Sanji-original research timelines and reports.';
COMMIT;
