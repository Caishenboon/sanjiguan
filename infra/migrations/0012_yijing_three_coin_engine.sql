-- Native sanji-engine result foundation for new physical three-coin runs.
-- Existing rows remain legacy: NULL mapping/result/manifest fields are never
-- backfilled or represented as replayable.
ALTER TABLE divination_sessions
  ADD COLUMN IF NOT EXISTS coin_face_mapping_id text,
  ADD COLUMN IF NOT EXISTS coin_face_mapping_version text,
  ADD COLUMN IF NOT EXISTS engine_result jsonb,
  ADD COLUMN IF NOT EXISTS engine_result_hash text,
  ADD COLUMN IF NOT EXISTS replay_manifest jsonb,
  ADD COLUMN IF NOT EXISTS replay_manifest_hash text,
  ADD COLUMN IF NOT EXISTS trace_hash text,
  ADD COLUMN IF NOT EXISTS ruleset_bundle_id text,
  ADD COLUMN IF NOT EXISTS ruleset_bundle_hash text,
  ADD COLUMN IF NOT EXISTS mapping_asset_version text,
  ADD COLUMN IF NOT EXISTS research_status text;

ALTER TABLE coin_tosses
  ADD COLUMN IF NOT EXISTS coin_values smallint[];

ALTER TABLE coin_tosses
  ADD CONSTRAINT coin_tosses_coin_values_shape
  CHECK (
    coin_values IS NULL OR
    (cardinality(coin_values)=3 AND coin_values <@ ARRAY[2,3]::smallint[])
  );

ALTER TABLE divination_sessions
  ADD CONSTRAINT divination_engine_result_hash_format
    CHECK (engine_result_hash IS NULL OR engine_result_hash ~ '^sha256:[a-f0-9]{64}$'),
  ADD CONSTRAINT divination_replay_manifest_hash_format
    CHECK (replay_manifest_hash IS NULL OR replay_manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  ADD CONSTRAINT divination_trace_hash_format
    CHECK (trace_hash IS NULL OR trace_hash ~ '^sha256:[a-f0-9]{64}$'),
  ADD CONSTRAINT divination_research_status_allowed
    CHECK (research_status IS NULL OR research_status IN ('research_active','legacy_method_unknown'));

COMMENT ON COLUMN divination_sessions.engine_result IS
  'Native deterministic sanji-engine result for new runs; NULL means legacy/unavailable.';
COMMENT ON COLUMN coin_tosses.coin_values IS
  'Explicit numeric physical coin values in recorded order; NULL means legacy mapping unavailable.';
