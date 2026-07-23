-- Consent withdrawal and anonymous-event data minimization guards.
BEGIN;

ALTER TABLE relationship_subjects
  ADD CONSTRAINT anonymous_event_no_identifiers CHECK (
    mode <> 'anonymous_event'
    OR (linked_profile_id IS NULL AND alias_ciphertext IS NULL
        AND consent_record_encrypted IS NULL AND consented_at IS NULL)
  );

CREATE TABLE relationship_analysis_requests (
  id uuid PRIMARY KEY,
  subject_id uuid NOT NULL REFERENCES relationship_subjects(id) ON DELETE CASCADE,
  requested_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION require_active_relationship_consent() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM relationship_consents c
    WHERE c.subject_id=NEW.subject_id
      AND c.consent_status='granted'
      AND (c.expires_at IS NULL OR c.expires_at > now())
  ) THEN
    RAISE EXCEPTION 'active_relationship_consent_required' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER relationship_analysis_consent_guard
BEFORE INSERT ON relationship_analysis_requests
FOR EACH ROW EXECUTE FUNCTION require_active_relationship_consent();

ALTER TABLE relationship_analysis_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE relationship_analysis_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY relationship_analysis_owner ON relationship_analysis_requests FOR ALL TO app_runtime
USING (requested_by=app_current_user_id() OR app_current_user_role()='owner')
WITH CHECK (requested_by=app_current_user_id() OR app_current_user_role()='owner');
GRANT SELECT,INSERT,UPDATE,DELETE ON relationship_analysis_requests TO app_runtime;

COMMIT;
