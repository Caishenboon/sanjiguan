-- Sprint 17: shared private execution substrate for Sushe, Zhongyin and Yuanqi.
-- Topic snapshots contain normalized labels/references only; sensitive prose stays
-- in its source record and all private payloads remain encrypted at rest.
BEGIN;

CREATE TABLE topic_ruleset_versions (
  id uuid PRIMARY KEY,
  ruleset_id text NOT NULL,
  version text NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[a-f0-9]{64}$'),
  naming_ruleset_id text NOT NULL,
  naming_ruleset_version text NOT NULL,
  naming_ruleset_hash text NOT NULL CHECK (naming_ruleset_hash ~ '^sha256:[a-f0-9]{64}$'),
  tradition_scope text NOT NULL CHECK (tradition_scope = 'sanji_original'),
  activation text NOT NULL CHECK (activation = 'research_active'),
  review_status text NOT NULL CHECK (review_status = 'UNCONFIRMED'),
  production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(ruleset_id, version)
);

INSERT INTO topic_ruleset_versions(
  id,ruleset_id,version,content_hash,naming_ruleset_id,naming_ruleset_version,
  naming_ruleset_hash,tradition_scope,activation,review_status,production_activatable
) VALUES (
  '019fa02b-a48f-7bb0-8a17-000000000017',
  'topic-research-rules','1.0.0',
  'sha256:babe7b23065aba4c0ca2ef9f6f0c689846497cd6d836e0fd306ff8c61b63ce55',
  'past-life-name-rules','1.0.0',
  'sha256:25b3d091562fdf58d88ea3c49237d09d8fbde6d8240d086a9c547d39bb67ef80',
  'sanji_original','research_active','UNCONFIRMED',false
) ON CONFLICT(ruleset_id,version) DO NOTHING;

CREATE TABLE topic_executions (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  relationship_id uuid,
  topic_type text NOT NULL CHECK (
    topic_type IN ('sushe','zhongyin_life','zhongyin_deceased','yuanqi')
  ),
  parent_execution_id uuid REFERENCES topic_executions(id) ON DELETE SET NULL,
  execution_kind text NOT NULL CHECK (execution_kind IN ('initial','reanalysis')),
  input_snapshot_encrypted bytea,
  graph_snapshot_encrypted bytea,
  result_encrypted bytea NOT NULL,
  candidate_summary jsonb NOT NULL,
  engine_version text NOT NULL,
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id = 'topic-research-v1.0.0'),
  topic_ruleset_version text NOT NULL,
  topic_ruleset_hash text NOT NULL CHECK (topic_ruleset_hash ~ '^sha256:[a-f0-9]{64}$'),
  naming_ruleset_version text NOT NULL,
  naming_ruleset_hash text NOT NULL CHECK (naming_ruleset_hash ~ '^sha256:[a-f0-9]{64}$'),
  evidence_policy_version text NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  graph_hash text NOT NULL CHECK (graph_hash ~ '^sha256:[a-f0-9]{64}$'),
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

CREATE TABLE topic_execution_evidence_refs (
  execution_id uuid NOT NULL REFERENCES topic_executions(id) ON DELETE CASCADE,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  record_id uuid NOT NULL,
  record_table text NOT NULL,
  node_type text NOT NULL,
  consent_scope text NOT NULL CHECK (
    consent_scope IN ('self','public_fact','single_party','bilateral_analysis')
  ),
  included boolean NOT NULL,
  withdrawn_at_run boolean NOT NULL,
  source_fingerprint text NOT NULL CHECK (source_fingerprint ~ '^sha256:[a-f0-9]{64}$'),
  PRIMARY KEY(execution_id, record_table, record_id, node_type)
);

CREATE TABLE topic_replay_records (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  execution_id uuid NOT NULL REFERENCES topic_executions(id) ON DELETE CASCADE,
  replay_output_hash text NOT NULL CHECK (replay_output_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_trace_hash text NOT NULL CHECK (replay_trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  matched boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE topic_execution_comparisons (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  left_execution_id uuid NOT NULL REFERENCES topic_executions(id) ON DELETE CASCADE,
  right_execution_id uuid NOT NULL REFERENCES topic_executions(id) ON DELETE CASCADE,
  difference_summary jsonb NOT NULL,
  comparison_hash text NOT NULL CHECK (comparison_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (left_execution_id <> right_execution_id)
);

ALTER TABLE sanji_archive_entries
  ADD COLUMN topic_execution_id uuid REFERENCES topic_executions(id) ON DELETE SET NULL;
ALTER TABLE sanji_archive_entries DROP CONSTRAINT sanji_archive_entries_entry_type_check;
ALTER TABLE sanji_archive_entries ADD CONSTRAINT sanji_archive_entries_entry_type_check
  CHECK (entry_type IN ('record','mechanical_result','liuxiang_research','topic_research'));

CREATE INDEX topic_executions_profile_idx ON topic_executions(profile_id, created_at DESC);
CREATE INDEX topic_executions_relationship_idx ON topic_executions(relationship_id, created_at DESC);

ALTER TABLE topic_ruleset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_ruleset_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE topic_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_executions FORCE ROW LEVEL SECURITY;
ALTER TABLE topic_execution_evidence_refs ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_execution_evidence_refs FORCE ROW LEVEL SECURITY;
ALTER TABLE topic_replay_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_replay_records FORCE ROW LEVEL SECURITY;
ALTER TABLE topic_execution_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_execution_comparisons FORCE ROW LEVEL SECURITY;

CREATE POLICY topic_ruleset_read ON topic_ruleset_versions
  FOR SELECT TO app_runtime USING (true);
CREATE POLICY topic_execution_owner ON topic_executions
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = profile_id AND p.owner_id = app_current_user_id() AND p.deleted_at IS NULL
    )
  );
CREATE POLICY topic_evidence_ref_owner ON topic_execution_evidence_refs
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM topic_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY topic_replay_owner ON topic_replay_records
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM topic_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
CREATE POLICY topic_comparison_owner ON topic_execution_comparisons
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (
    owner_id = app_current_user_id()
    AND EXISTS (
      SELECT 1 FROM topic_executions e
      WHERE e.id IN (left_execution_id,right_execution_id)
      GROUP BY e.owner_id HAVING count(*) = 2 AND e.owner_id = app_current_user_id()
    )
  );

REVOKE ALL ON topic_ruleset_versions,topic_executions,
  topic_execution_evidence_refs,topic_replay_records,
  topic_execution_comparisons FROM app_runtime;
GRANT SELECT ON topic_ruleset_versions TO app_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON topic_executions,
  topic_execution_evidence_refs,topic_replay_records,
  topic_execution_comparisons TO app_runtime;

COMMENT ON TABLE topic_executions IS
  'Encrypted, shared deterministic topic executions; Sanji-original research only.';
COMMIT;
