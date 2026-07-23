-- Sprint 2 research-preview inference pipeline. Production mode remains forbidden.
BEGIN;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS research_profile boolean NOT NULL DEFAULT false;
ALTER TABLE analysis_runs ADD COLUMN IF NOT EXISTS run_mode text NOT NULL DEFAULT 'research_preview'
  CHECK(run_mode='research_preview'),ADD COLUMN IF NOT EXISTS is_synthetic boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS ruleset_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS claim_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS output_hash text,ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
ALTER TABLE hypotheses ADD COLUMN IF NOT EXISTS research_strength smallint CHECK(research_strength BETWEEN 0 AND 100),
  ADD COLUMN IF NOT EXISTS net_effect numeric,ADD COLUMN IF NOT EXISTS ordinary_explanations jsonb DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS hard_conflicts jsonb DEFAULT '[]';
ALTER TABLE past_life_nodes ADD COLUMN IF NOT EXISTS research_node_type text,
  ADD COLUMN IF NOT EXISTS supporting_evidence jsonb DEFAULT '[]',ADD COLUMN IF NOT EXISTS counterevidence jsonb DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS research_strength smallint CHECK(research_strength BETWEEN 0 AND 100);

CREATE TABLE analysis_stage_runs(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 stage_name text NOT NULL,input_hash text NOT NULL CHECK(input_hash~'^[a-f0-9]{64}$'),
 output_hash text CHECK(output_hash~'^[a-f0-9]{64}$'),ruleset_version text NOT NULL,
 claim_versions jsonb NOT NULL,random_seed bigint NOT NULL,started_at timestamptz NOT NULL,
 completed_at timestamptz,status text NOT NULL CHECK(status IN('pending','running','complete','failed')),
 error_code text,UNIQUE(analysis_run_id,stage_name));
CREATE TABLE normalized_signals(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 domain text NOT NULL,source_evidence_ids uuid[] NOT NULL,tag text NOT NULL,
 direction text NOT NULL CHECK(direction IN('support','oppose')),strength numeric(5,4) NOT NULL,
 source_reliability numeric(5,4) NOT NULL,relevance numeric(5,4) NOT NULL,
 independence_group text NOT NULL,time_scope jsonb NOT NULL,ordinary_explanation_present boolean NOT NULL,
 ruleset_version text NOT NULL,UNIQUE(analysis_run_id,independence_group,tag,direction));
CREATE TABLE hypothesis_contributions(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 hypothesis_key text NOT NULL,signal_id uuid REFERENCES normalized_signals(id),component text NOT NULL,
 raw_value numeric NOT NULL,weighted_value numeric NOT NULL,details jsonb NOT NULL);
CREATE TABLE hypothesis_conflicts(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 hypothesis_key text NOT NULL,conflict_type text NOT NULL,severity numeric(5,4) NOT NULL,
 evidence_ids uuid[] NOT NULL,details jsonb NOT NULL,resolved boolean NOT NULL DEFAULT false);
CREATE TABLE bardo_chain_links(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 sequence_no smallint NOT NULL,link_type text NOT NULL,basis_claim_ids uuid[] NOT NULL,
 system_mapping_claim_ids uuid[] NOT NULL,status text NOT NULL CHECK(status IN('candidate','breakpoint','supported')),
 content_encrypted bytea,UNIQUE(analysis_run_id,sequence_no));
CREATE TABLE retrieval_runs(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 query_json jsonb NOT NULL,input_hash text NOT NULL,started_at timestamptz NOT NULL,
 completed_at timestamptz,status text NOT NULL,embedding_mode text NOT NULL DEFAULT 'disabled');
CREATE TABLE retrieval_results(
 id uuid PRIMARY KEY,retrieval_run_id uuid NOT NULL REFERENCES retrieval_runs(id) ON DELETE CASCADE,
 claim_id uuid NOT NULL REFERENCES knowledge_claims(id),claim_version integer NOT NULL,
 rank smallint NOT NULL,match_basis jsonb NOT NULL,UNIQUE(retrieval_run_id,claim_id));
CREATE TABLE prompt_runs(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 pass_no smallint NOT NULL CHECK(pass_no IN(1,2)),provider text NOT NULL,model text,
 prompt_hash text NOT NULL,response_hash text,status text NOT NULL,error_code text,
 token_budget integer,estimated_cost numeric,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(analysis_run_id,pass_no));
CREATE TABLE generated_prose(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
 prose_encrypted bytea NOT NULL,provider text NOT NULL,template_version text NOT NULL,
 locked_verdict_hash text NOT NULL,validated boolean NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE research_reports(
 id uuid PRIMARY KEY,analysis_run_id uuid NOT NULL UNIQUE REFERENCES analysis_runs(id) ON DELETE CASCADE,
 verdict_json jsonb NOT NULL,report_encrypted bytea NOT NULL,ruleset_version text NOT NULL,
 claim_snapshot jsonb NOT NULL,prose_source text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 deleted_at timestamptz);
CREATE TABLE evaluation_cases(
 id text PRIMARY KEY,group_name text NOT NULL,fixture_json jsonb NOT NULL,expected_json jsonb NOT NULL,
 checksum text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE evaluation_results(
 id uuid PRIMARY KEY,evaluation_case_id text NOT NULL REFERENCES evaluation_cases(id),
 engine_version text NOT NULL,result_json jsonb NOT NULL,passed boolean NOT NULL,
 metrics_json jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());

DO $$ DECLARE t text;BEGIN FOREACH t IN ARRAY ARRAY['analysis_stage_runs','normalized_signals',
'hypothesis_contributions','hypothesis_conflicts','bardo_chain_links','retrieval_runs','retrieval_results',
'prompt_runs','generated_prose','research_reports','evaluation_cases','evaluation_results']
LOOP EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
EXECUTE format('CREATE POLICY owner_research_only ON %I FOR ALL TO app_runtime USING (app_current_user_role()=''owner'') WITH CHECK (app_current_user_role()=''owner'')',t);
EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON %I TO app_runtime',t);END LOOP;END$$;
CREATE INDEX stage_run_status_idx ON analysis_stage_runs(analysis_run_id,status);
CREATE INDEX signals_analysis_tag_idx ON normalized_signals(analysis_run_id,tag);
CREATE INDEX retrieval_claim_idx ON retrieval_results(claim_id);
COMMIT;
