-- Sprint 16: private Liuxiang evidence executions and authoritative Sanji archive.
-- These tables never contain public research people or unencrypted private prose.
BEGIN;

CREATE TABLE evidence_policy_versions (
  id uuid PRIMARY KEY,
  policy_id text NOT NULL,
  version text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[a-f0-9]{64}$'),
  tradition_scope text NOT NULL CHECK (tradition_scope = 'sanji_original'),
  review_status text NOT NULL CHECK (review_status = 'UNCONFIRMED'),
  activation text NOT NULL CHECK (activation = 'research_active'),
  production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable),
  policy_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(policy_id, version),
  UNIQUE(content_hash)
);

INSERT INTO evidence_policy_versions(
  id,policy_id,version,content_hash,tradition_scope,review_status,
  activation,production_activatable,policy_json
) VALUES(
  '019f9f61-5dc9-79cf-8b92-000000000016',
  'liuxiang-user-evidence-policy','1.0.0',
  'sha256:958908109ed29ab9bdf17f3fe3cb97032c3493380356857484c26a0949d08b36',
  'sanji_original','UNCONFIRMED','research_active',false,
  '{"asset":"liuxiang-evidence-policies-1.0.0.json","authority":"sanji-engine bundled asset"}'::jsonb
) ON CONFLICT(policy_id,version) DO NOTHING;

CREATE TABLE liuxiang_user_executions (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  parent_execution_id uuid REFERENCES liuxiang_user_executions(id) ON DELETE SET NULL,
  execution_kind text NOT NULL CHECK (execution_kind IN ('initial','reanalysis')),
  input_snapshot_encrypted bytea NOT NULL,
  result_encrypted bytea NOT NULL,
  candidate_summary jsonb NOT NULL,
  engine_version text NOT NULL,
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id = 'liuxiang-evidence-research-v1.0.0'),
  ruleset_bundle_hash text NOT NULL CHECK (ruleset_bundle_hash ~ '^sha256:[a-f0-9]{64}$'),
  evidence_policy_id text NOT NULL,
  evidence_policy_version text NOT NULL,
  evidence_policy_hash text NOT NULL CHECK (evidence_policy_hash ~ '^sha256:[a-f0-9]{64}$'),
  profile_version text NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  output_hash text NOT NULL CHECK (output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text NOT NULL CHECK (trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_available boolean NOT NULL DEFAULT true,
  replay_unavailable_reason text,
  snapshot_purged_at timestamptz,
  status text NOT NULL CHECK (status IN ('decisive','provisional','contested','insufficient')),
  research_notice text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (replay_available AND replay_unavailable_reason IS NULL AND snapshot_purged_at IS NULL)
    OR
    (NOT replay_available AND replay_unavailable_reason IS NOT NULL AND snapshot_purged_at IS NOT NULL)
  )
);

CREATE TABLE liuxiang_execution_evidence_refs (
  execution_id uuid NOT NULL REFERENCES liuxiang_user_executions(id) ON DELETE CASCADE,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  record_id uuid NOT NULL,
  record_table text NOT NULL CHECK (record_table IN (
    'profiles','evidence_items','journal_entries','life_events','relationship_subjects',
    'divination_sessions','bazi_research_runs','ziwei_research_runs'
  )),
  dimension_id text NOT NULL CHECK (dimension_id IN (
    'lx_ming','lx_ye','lx_yuan','lx_meng','lx_yuan_relation','lx_shi'
  )),
  fact_kind text NOT NULL CHECK (fact_kind IN ('coverage','structural','evidence')),
  included boolean NOT NULL,
  withdrawn_at_run boolean NOT NULL,
  record_revision text NOT NULL,
  source_fingerprint text NOT NULL CHECK (source_fingerprint ~ '^sha256:[a-f0-9]{64}$'),
  PRIMARY KEY(execution_id, record_table, record_id, dimension_id)
);

CREATE TABLE sanji_archive_entries (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  execution_id uuid REFERENCES liuxiang_user_executions(id) ON DELETE SET NULL,
  parent_entry_id uuid REFERENCES sanji_archive_entries(id) ON DELETE SET NULL,
  entry_type text NOT NULL CHECK (entry_type IN ('record','mechanical_result','liuxiang_research')),
  title_ciphertext bytea NOT NULL,
  note_ciphertext bytea,
  original_record_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL CHECK (status IN ('decisive','provisional','contested','insufficient','recorded')),
  candidate_summary jsonb NOT NULL DEFAULT '[]'::jsonb,
  engine_version text,
  ruleset_version text,
  evidence_policy_version text,
  profile_version text,
  output_hash text CHECK (output_hash IS NULL OR output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text CHECK (trace_hash IS NULL OR trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_available boolean NOT NULL DEFAULT false,
  research_notice text,
  created_at timestamptz NOT NULL DEFAULT now(),
  withdrawn_at timestamptz
);

CREATE TABLE liuxiang_replay_records (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  execution_id uuid NOT NULL REFERENCES liuxiang_user_executions(id) ON DELETE CASCADE,
  replay_output_hash text NOT NULL CHECK (replay_output_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_trace_hash text NOT NULL CHECK (replay_trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  matched boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE liuxiang_execution_comparisons (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  left_execution_id uuid NOT NULL REFERENCES liuxiang_user_executions(id) ON DELETE CASCADE,
  right_execution_id uuid NOT NULL REFERENCES liuxiang_user_executions(id) ON DELETE CASCADE,
  difference_summary jsonb NOT NULL,
  comparison_hash text NOT NULL CHECK (comparison_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (left_execution_id <> right_execution_id)
);

CREATE INDEX liuxiang_user_runs_profile_idx ON liuxiang_user_executions(profile_id, created_at DESC);
CREATE INDEX sanji_archive_owner_idx ON sanji_archive_entries(owner_id, created_at DESC);
CREATE INDEX sanji_archive_profile_idx ON sanji_archive_entries(profile_id, created_at DESC);

ALTER TABLE evidence_policy_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_policy_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_user_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_user_executions FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_execution_evidence_refs ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_execution_evidence_refs FORCE ROW LEVEL SECURITY;
ALTER TABLE sanji_archive_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE sanji_archive_entries FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_replay_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_replay_records FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_execution_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_execution_comparisons FORCE ROW LEVEL SECURITY;

CREATE POLICY evidence_policy_read ON evidence_policy_versions
  FOR SELECT TO app_runtime USING (true);
CREATE POLICY liuxiang_user_execution_owner ON liuxiang_user_executions
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = profile_id AND p.owner_id = app_current_user_id() AND p.deleted_at IS NULL
    )
  );
CREATE POLICY liuxiang_execution_ref_owner ON liuxiang_execution_evidence_refs
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM liuxiang_user_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY sanji_archive_owner ON sanji_archive_entries
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = profile_id AND p.owner_id = app_current_user_id() AND p.deleted_at IS NULL
    )
  );
CREATE POLICY liuxiang_replay_owner ON liuxiang_replay_records
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM liuxiang_user_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY liuxiang_comparison_owner ON liuxiang_execution_comparisons
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM liuxiang_user_executions e
      WHERE e.id IN (left_execution_id, right_execution_id)
      GROUP BY e.owner_id HAVING count(*) = 2 AND e.owner_id = app_current_user_id()
    )
  );

REVOKE ALL ON evidence_policy_versions, liuxiang_user_executions,
  liuxiang_execution_evidence_refs, sanji_archive_entries,
  liuxiang_replay_records, liuxiang_execution_comparisons FROM app_runtime;
GRANT SELECT ON evidence_policy_versions TO app_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON liuxiang_user_executions,
  liuxiang_execution_evidence_refs, sanji_archive_entries,
  liuxiang_replay_records, liuxiang_execution_comparisons TO app_runtime;

COMMENT ON TABLE liuxiang_user_executions IS
  'Private, deterministic sanji_original research runs; no LLM or Oracle inputs.';
COMMENT ON TABLE sanji_archive_entries IS
  'Authoritative database-backed Sanji archive; browser storage is never authoritative.';
COMMIT;
