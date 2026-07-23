-- Sprint 1A.5 resource grants, consent lifecycle, and complete RLS.
BEGIN;

ALTER TABLE profile_grants
  ADD COLUMN status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','revoked','expired')),
  ADD COLUMN scope text[] NOT NULL DEFAULT ARRAY['profile:read']::text[],
  ADD COLUMN revoked_by uuid REFERENCES users(id);

ALTER TABLE relationship_consents
  DROP CONSTRAINT IF EXISTS relationship_consents_status_check,
  DROP CONSTRAINT IF EXISTS relationship_consents_proof_type_check,
  DROP CONSTRAINT IF EXISTS relationship_consents_check,
  ALTER COLUMN consented_at DROP NOT NULL,
  ALTER COLUMN record_encrypted DROP NOT NULL,
  ALTER COLUMN record_hash DROP NOT NULL;

ALTER TABLE relationship_consents RENAME COLUMN revoked_at TO withdrawn_at;
ALTER TABLE relationship_consents RENAME COLUMN proof_type TO evidence_type;
ALTER TABLE relationship_consents RENAME COLUMN status TO consent_status;

ALTER TABLE relationship_consents
  ALTER COLUMN consent_status SET DEFAULT 'pending',
  ADD CONSTRAINT relationship_consents_status_check
    CHECK (consent_status IN ('pending','granted','withdrawn','expired','anonymous_event_mode')),
  ADD CONSTRAINT relationship_consents_evidence_check
    CHECK (evidence_type IN ('self_attestation','signed_record','linked_profile_confirmation','none')),
  ADD CONSTRAINT relationship_consents_withdrawal_check
    CHECK ((consent_status = 'withdrawn') = (withdrawn_at IS NOT NULL));

CREATE OR REPLACE FUNCTION app_current_user_role() RETURNS text
LANGUAGE sql STABLE LEAKPROOF
RETURN nullif(current_setting('app.current_user_role', true), '');

DROP POLICY IF EXISTS profiles_member_owner_select ON profiles;
DROP POLICY IF EXISTS profiles_member_owner_modify ON profiles;
CREATE POLICY profiles_select ON profiles FOR SELECT TO app_runtime
USING (
  owner_id = app_current_user_id()
  OR app_current_user_role() = 'owner'
  OR EXISTS (
    SELECT 1 FROM profile_grants g
    WHERE g.profile_id = profiles.id
      AND g.grantee_user_id = app_current_user_id()
      AND g.permission = 'read'
      AND 'profile:read' = ANY(g.scope)
      AND g.status = 'active'
      AND g.revoked_at IS NULL
      AND (g.expires_at IS NULL OR g.expires_at > now())
  )
);
CREATE POLICY profiles_modify ON profiles FOR ALL TO app_runtime
USING (owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
WITH CHECK (owner_id = app_current_user_id() OR app_current_user_role() = 'owner');

DROP POLICY IF EXISTS relation_owner_policy ON relationship_subjects;
CREATE POLICY relationship_visible_profile ON relationship_subjects FOR SELECT TO app_runtime
USING (
  EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
    (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner'))
  OR EXISTS (SELECT 1 FROM profile_grants g WHERE g.profile_id = relationship_subjects.profile_id
    AND g.grantee_user_id = app_current_user_id() AND g.status = 'active'
    AND 'relationship:read' = ANY(g.scope) AND g.revoked_at IS NULL
    AND (g.expires_at IS NULL OR g.expires_at > now()))
);
CREATE POLICY relationship_owner_modify ON relationship_subjects FOR ALL TO app_runtime
USING (EXISTS (
  SELECT 1 FROM profiles p WHERE p.id = profile_id
    AND (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
))
WITH CHECK (EXISTS (
  SELECT 1 FROM profiles p WHERE p.id = profile_id
    AND (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
));

CREATE POLICY consent_visible_subject ON relationship_consents FOR SELECT TO app_runtime
USING (EXISTS (
  SELECT 1 FROM relationship_subjects rs JOIN profiles p ON p.id = rs.profile_id
  WHERE rs.id = subject_id AND
    (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
));
CREATE POLICY consent_owner_modify ON relationship_consents FOR ALL TO app_runtime
USING (EXISTS (
  SELECT 1 FROM relationship_subjects rs JOIN profiles p ON p.id = rs.profile_id
  WHERE rs.id = subject_id
    AND (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
))
WITH CHECK (EXISTS (
  SELECT 1 FROM relationship_subjects rs JOIN profiles p ON p.id = rs.profile_id
  WHERE rs.id = subject_id
    AND (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')
));

DROP POLICY IF EXISTS evidence_owner_modify ON evidence_items;
CREATE POLICY evidence_modify ON evidence_items FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')));

DROP POLICY IF EXISTS charts_owner_modify ON chart_snapshots;
CREATE POLICY charts_modify ON chart_snapshots FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')));

DROP POLICY IF EXISTS runs_owner_modify ON analysis_runs;
CREATE POLICY runs_modify ON analysis_runs FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')));

DROP POLICY IF EXISTS normalization_owner_modify ON birth_time_normalizations;
CREATE POLICY normalization_modify ON birth_time_normalizations FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')));

DROP POLICY IF EXISTS grants_owner_modify ON profile_grants;
CREATE POLICY grants_modify ON profile_grants FOR ALL TO app_runtime
USING (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')))
WITH CHECK (EXISTS (SELECT 1 FROM profiles p WHERE p.id = profile_id AND
  (p.owner_id = app_current_user_id() OR app_current_user_role() = 'owner')));

COMMIT;
