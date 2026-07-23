-- sanji-engine replay-manifest foundation.
-- This is additive only: existing rows remain legacy rows with NULL manifest
-- fields. It neither backfills nor fabricates replay evidence.
ALTER TABLE analysis_runs
  ADD COLUMN IF NOT EXISTS engine_api_version text,
  ADD COLUMN IF NOT EXISTS engine_core_version text,
  ADD COLUMN IF NOT EXISTS engine_schema_versions jsonb,
  ADD COLUMN IF NOT EXISTS ruleset_bundle_id text,
  ADD COLUMN IF NOT EXISTS ruleset_bundle_hash text,
  ADD COLUMN IF NOT EXISTS engine_data_versions jsonb,
  ADD COLUMN IF NOT EXISTS canonicalization_version text,
  ADD COLUMN IF NOT EXISTS trace_hash text,
  ADD COLUMN IF NOT EXISTS replay_manifest jsonb,
  ADD COLUMN IF NOT EXISTS replay_manifest_hash text;

ALTER TABLE analysis_runs
  ADD CONSTRAINT analysis_runs_engine_api_version_format
    CHECK (engine_api_version IS NULL OR engine_api_version ~ '^[0-9]+\.[0-9]+$'),
  ADD CONSTRAINT analysis_runs_ruleset_bundle_hash_format
    CHECK (ruleset_bundle_hash IS NULL OR ruleset_bundle_hash ~ '^sha256:[a-f0-9]{64}$'),
  ADD CONSTRAINT analysis_runs_trace_hash_format
    CHECK (trace_hash IS NULL OR trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  ADD CONSTRAINT analysis_runs_replay_manifest_hash_format
    CHECK (replay_manifest_hash IS NULL OR replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$');

COMMENT ON COLUMN analysis_runs.replay_manifest IS
  'Versioned sanji-engine replay manifest. NULL means unavailable/legacy, never inferred.';
