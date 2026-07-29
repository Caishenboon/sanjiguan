-- Deterministic Liuxiang research platform v1.
-- Public research assets are isolated from account profiles. User-associated
-- execution payloads remain encrypted and owner-only.

CREATE TABLE IF NOT EXISTS research_dataset_manifests (
  id uuid PRIMARY KEY,
  dataset_id text NOT NULL,
  pinned_revision text NOT NULL CHECK (pinned_revision ~ '^[a-f0-9]{40}$'),
  manifest_hash text NOT NULL CHECK (manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  license_review_status text NOT NULL CHECK (license_review_status IN (
    'approved','conditional_download_only','license_review_required','rejected'
  )),
  shared_source_group text NOT NULL,
  manifest jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(dataset_id, pinned_revision)
);

CREATE TABLE IF NOT EXISTS research_import_runs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  dataset_manifest_id uuid NOT NULL REFERENCES research_dataset_manifests(id) ON DELETE RESTRICT,
  status text NOT NULL CHECK (status IN ('queued','running','complete','failed','partial_rejected')),
  file_hashes jsonb NOT NULL,
  row_counts jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS research_quality_reports (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  import_run_id uuid NOT NULL REFERENCES research_import_runs(id) ON DELETE CASCADE,
  asset_class text NOT NULL CHECK (asset_class IN (
    'synthetic_conformance','mechanical_reference','external_research_unverified',
    'retrospective_observational','prospective_blind'
  )),
  report jsonb NOT NULL,
  report_hash text NOT NULL CHECK (report_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS normalized_research_people (
  id uuid PRIMARY KEY,
  dataset_manifest_id uuid NOT NULL REFERENCES research_dataset_manifests(id) ON DELETE RESTRICT,
  source_person_id text NOT NULL,
  normalized_record jsonb NOT NULL,
  time_precision text NOT NULL CHECK (time_precision IN (
    'exact_time','approximate_time','date_only','year_only','unknown'
  )),
  sanji_verification_status text NOT NULL CHECK (sanji_verification_status IN (
    'not_verified','unverified_provider_claim','manually_reviewed','rejected'
  )),
  shared_source_group text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(dataset_manifest_id, source_person_id)
);

CREATE TABLE IF NOT EXISTS research_life_events (
  id uuid PRIMARY KEY,
  dataset_manifest_id uuid NOT NULL REFERENCES research_dataset_manifests(id) ON DELETE RESTRICT,
  research_person_id uuid REFERENCES normalized_research_people(id) ON DELETE SET NULL,
  source_event_id text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'marriage','divorce','relationship_ongoing','spouse_death_or_other_end','unknown_outcome'
  )),
  date_precision text NOT NULL CHECK (date_precision IN (
    'exact_date','month_only','year_only','unknown'
  )),
  normalized_record jsonb NOT NULL,
  shared_source_group text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(dataset_manifest_id, source_event_id)
);

CREATE TABLE IF NOT EXISTS research_person_matches (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_event_id text NOT NULL,
  research_person_id uuid REFERENCES normalized_research_people(id) ON DELETE SET NULL,
  match_method text NOT NULL CHECK (match_method IN (
    'stable_source_person_id','exact_normalized_identifier',
    'name_and_birth_year_exact','manual_review','unmatched'
  )),
  match_confidence_bp integer NOT NULL CHECK (match_confidence_bp BETWEEN 0 AND 10000),
  conflicting_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
  manual_review_required boolean NOT NULL,
  provenance jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS liuxiang_research_executions (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_record_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  asset_class text NOT NULL CHECK (asset_class IN (
    'synthetic_conformance','mechanical_reference','external_research_unverified',
    'retrospective_observational','prospective_blind'
  )),
  research_status text NOT NULL CHECK (research_status = 'research_active'),
  review_status text NOT NULL CHECK (review_status = 'UNCONFIRMED'),
  production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable),
  input_snapshot_encrypted bytea NOT NULL,
  engine_result_encrypted bytea NOT NULL,
  input_hash text NOT NULL CHECK (input_hash ~ '^sha256:[a-f0-9]{64}$'),
  output_hash text NOT NULL CHECK (output_hash ~ '^sha256:[a-f0-9]{64}$'),
  trace_hash text NOT NULL CHECK (trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  replay_manifest jsonb NOT NULL,
  replay_manifest_hash text NOT NULL CHECK (replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  ruleset_bundle_id text NOT NULL CHECK (ruleset_bundle_id = 'liuxiang-research-v1.0.0'),
  ruleset_bundle_hash text NOT NULL CHECK (ruleset_bundle_hash ~ '^sha256:[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE IF NOT EXISTS liuxiang_research_signals (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  execution_id uuid NOT NULL REFERENCES liuxiang_research_executions(id) ON DELETE CASCADE,
  signal_id text NOT NULL,
  dimension_id text NOT NULL CHECK (dimension_id IN (
    'lx_ming','lx_ye','lx_yuan','lx_meng','lx_yuan_relation','lx_shi'
  )),
  independence_group text NOT NULL,
  shared_source_group text NOT NULL,
  signal_json jsonb NOT NULL,
  content_hash text NOT NULL CHECK (content_hash ~ '^sha256:[a-f0-9]{64}$'),
  UNIQUE(execution_id, signal_id)
);

CREATE TABLE IF NOT EXISTS liuxiang_research_candidates (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  execution_id uuid NOT NULL REFERENCES liuxiang_research_executions(id) ON DELETE CASCADE,
  candidate_id text NOT NULL,
  dimension_id text NOT NULL,
  strength_bp integer NOT NULL CHECK (strength_bp BETWEEN 0 AND 10000),
  confidence_bp integer NOT NULL CHECK (confidence_bp BETWEEN 0 AND 10000),
  status text NOT NULL CHECK (status IN ('decisive','provisional','contested','insufficient')),
  rank integer NOT NULL CHECK (rank > 0),
  candidate_json jsonb NOT NULL,
  result_hash text NOT NULL CHECK (result_hash ~ '^sha256:[a-f0-9]{64}$'),
  UNIQUE(execution_id, candidate_id),
  UNIQUE(execution_id, rank)
);

CREATE INDEX IF NOT EXISTS research_import_runs_owner_idx ON research_import_runs(owner_id, started_at DESC);
CREATE INDEX IF NOT EXISTS research_people_source_idx ON normalized_research_people(dataset_manifest_id, source_person_id);
CREATE INDEX IF NOT EXISTS research_events_person_idx ON research_life_events(research_person_id);
CREATE INDEX IF NOT EXISTS liuxiang_runs_owner_idx ON liuxiang_research_executions(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS liuxiang_signals_run_idx ON liuxiang_research_signals(execution_id, dimension_id);
CREATE INDEX IF NOT EXISTS liuxiang_candidates_run_idx ON liuxiang_research_candidates(execution_id, rank);

ALTER TABLE research_dataset_manifests ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_dataset_manifests FORCE ROW LEVEL SECURITY;
ALTER TABLE research_import_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_import_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE research_quality_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_quality_reports FORCE ROW LEVEL SECURITY;
ALTER TABLE normalized_research_people ENABLE ROW LEVEL SECURITY;
ALTER TABLE normalized_research_people FORCE ROW LEVEL SECURITY;
ALTER TABLE research_life_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_life_events FORCE ROW LEVEL SECURITY;
ALTER TABLE research_person_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_person_matches FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_executions FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_signals FORCE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE liuxiang_research_candidates FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS research_manifests_owner_read ON research_dataset_manifests;
CREATE POLICY research_manifests_owner_read ON research_dataset_manifests
  FOR SELECT TO app_runtime USING (app_current_user_role() = 'owner');
DROP POLICY IF EXISTS research_people_owner_read ON normalized_research_people;
CREATE POLICY research_people_owner_read ON normalized_research_people
  FOR SELECT TO app_runtime USING (app_current_user_role() = 'owner');
DROP POLICY IF EXISTS research_events_owner_read ON research_life_events;
CREATE POLICY research_events_owner_read ON research_life_events
  FOR SELECT TO app_runtime USING (app_current_user_role() = 'owner');

DROP POLICY IF EXISTS research_import_owner_policy ON research_import_runs;
CREATE POLICY research_import_owner_policy ON research_import_runs FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (owner_id = app_current_user_id() AND app_current_user_role() = 'owner');
DROP POLICY IF EXISTS research_quality_owner_policy ON research_quality_reports;
CREATE POLICY research_quality_owner_policy ON research_quality_reports FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (owner_id = app_current_user_id() AND app_current_user_role() = 'owner');
DROP POLICY IF EXISTS research_matches_owner_policy ON research_person_matches;
CREATE POLICY research_matches_owner_policy ON research_person_matches FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (owner_id = app_current_user_id() AND app_current_user_role() = 'owner');
DROP POLICY IF EXISTS liuxiang_executions_owner_policy ON liuxiang_research_executions;
CREATE POLICY liuxiang_executions_owner_policy ON liuxiang_research_executions FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (
    owner_id = app_current_user_id() AND app_current_user_role() = 'owner'
    AND (profile_record_id IS NULL OR EXISTS (
      SELECT 1 FROM profiles p WHERE p.id = profile_record_id AND p.owner_id = app_current_user_id()
    ))
  );
DROP POLICY IF EXISTS liuxiang_signals_owner_policy ON liuxiang_research_signals;
CREATE POLICY liuxiang_signals_owner_policy ON liuxiang_research_signals FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (
    owner_id = app_current_user_id() AND app_current_user_role() = 'owner'
    AND EXISTS (
      SELECT 1 FROM liuxiang_research_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );
DROP POLICY IF EXISTS liuxiang_candidates_owner_policy ON liuxiang_research_candidates;
CREATE POLICY liuxiang_candidates_owner_policy ON liuxiang_research_candidates FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id() AND app_current_user_role() = 'owner')
  WITH CHECK (
    owner_id = app_current_user_id() AND app_current_user_role() = 'owner'
    AND EXISTS (
      SELECT 1 FROM liuxiang_research_executions e
      WHERE e.id = execution_id AND e.owner_id = app_current_user_id()
    )
  );

REVOKE ALL ON research_dataset_manifests, research_import_runs, research_quality_reports,
  normalized_research_people, research_life_events, research_person_matches,
  liuxiang_research_executions, liuxiang_research_signals,
  liuxiang_research_candidates FROM app_runtime;
GRANT SELECT ON research_dataset_manifests, normalized_research_people,
  research_life_events TO app_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON research_import_runs,
  research_quality_reports, research_person_matches, liuxiang_research_executions,
  liuxiang_research_signals, liuxiang_research_candidates TO app_runtime;

COMMENT ON TABLE research_dataset_manifests IS
  'Pinned public-research metadata only; never a user profile or independent truth claim.';
COMMENT ON TABLE liuxiang_research_executions IS
  'Owner-only sanji_original, UNCONFIRMED, non-production Liuxiang research executions.';
