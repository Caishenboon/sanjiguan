-- V1 RC: ordinary members may persist complete traditional research runs only
-- for their own identity. The legacy /admin route separately enforces owner-only.
DROP POLICY IF EXISTS traditional_complete_runs_owner ON traditional_complete_runs;
CREATE POLICY traditional_complete_runs_owner ON traditional_complete_runs
  FOR ALL TO app_runtime
  USING (
    owner_id = app_current_user_id()
    AND app_current_user_role() IN ('owner', 'member')
  )
  WITH CHECK (
    owner_id = app_current_user_id()
    AND app_current_user_role() IN ('owner', 'member')
  );
