-- Sprint 3 owner-only private research controls. Production rules remain disabled.
BEGIN;
ALTER TABLE analysis_runs
  ADD COLUMN IF NOT EXISTS prose_provider text NOT NULL DEFAULT 'template'
    CHECK(prose_provider IN('template','deepseek')),
  ADD COLUMN IF NOT EXISTS research_consent_at timestamptz,
  ADD COLUMN IF NOT EXISTS external_model_consent_at timestamptz;
CREATE TABLE IF NOT EXISTS model_usage_records(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 provider text NOT NULL,model text,prompt_tokens integer NOT NULL DEFAULT 0,
 completion_tokens integer NOT NULL DEFAULT 0,total_tokens integer NOT NULL DEFAULT 0,
 estimated_cost numeric(12,6) NOT NULL DEFAULT 0,currency text NOT NULL DEFAULT 'USD',
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(prompt_tokens>=0 AND completion_tokens>=0 AND total_tokens>=0 AND estimated_cost>=0));
ALTER TABLE model_usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_usage_records FORCE ROW LEVEL SECURITY;
CREATE POLICY owner_model_usage_only ON model_usage_records FOR ALL TO app_runtime
  USING(app_current_user_role()='owner') WITH CHECK(app_current_user_role()='owner');
GRANT SELECT,INSERT,DELETE ON model_usage_records TO app_runtime;
CREATE INDEX IF NOT EXISTS model_usage_analysis_idx ON model_usage_records(analysis_run_id,created_at);
COMMIT;
