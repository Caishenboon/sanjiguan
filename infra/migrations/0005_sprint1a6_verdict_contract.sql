-- Enforce rank uniqueness for structured verdicts within one run and subject.
BEGIN;
CREATE TABLE structured_verdicts (
  id uuid PRIMARY KEY,
  analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
  subject text NOT NULL,
  rank integer NOT NULL CHECK (rank > 0),
  verdict_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (analysis_run_id, subject, rank)
);
ALTER TABLE structured_verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE structured_verdicts FORCE ROW LEVEL SECURITY;
CREATE POLICY structured_verdict_visible ON structured_verdicts FOR SELECT TO app_runtime
USING (EXISTS (
  SELECT 1 FROM analysis_runs ar JOIN profiles p ON p.id=ar.profile_id
  WHERE ar.id=analysis_run_id AND
    (p.owner_id=app_current_user_id() OR app_current_user_role()='owner')
));
GRANT SELECT,INSERT,UPDATE,DELETE ON structured_verdicts TO app_runtime;
COMMIT;
