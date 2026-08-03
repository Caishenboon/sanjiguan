-- V1 release closure: owner bootstrap, export audit and deletion lifecycle.
BEGIN;

CREATE TABLE user_export_jobs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  export_format text NOT NULL CHECK (export_format IN ('archive_zip','json','html')),
  manifest_hash text NOT NULL CHECK (manifest_hash ~ '^sha256:[a-f0-9]{64}$'),
  file_count integer NOT NULL CHECK (file_count >= 1),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (expires_at <= created_at + interval '24 hours')
);

CREATE TABLE private_deletion_events (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL,
  resource_type text NOT NULL CHECK (
    resource_type IN ('record','evidence','relationship','profile','ai_narrative','snapshot','account')
  ),
  resource_id uuid,
  deletion_mode text NOT NULL CHECK (deletion_mode IN ('withdraw','soft_delete','purge')),
  replay_impact text NOT NULL CHECK (replay_impact IN ('none','historical_snapshot','replay_unavailable')),
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE user_export_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_export_jobs FORCE ROW LEVEL SECURITY;
ALTER TABLE private_deletion_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE private_deletion_events FORCE ROW LEVEL SECURITY;

CREATE POLICY user_export_owner ON user_export_jobs
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (owner_id = app_current_user_id());
CREATE POLICY deletion_event_owner ON private_deletion_events
  FOR ALL TO app_runtime
  USING (owner_id = app_current_user_id())
  WITH CHECK (owner_id = app_current_user_id());

REVOKE ALL ON user_export_jobs, private_deletion_events FROM app_runtime;
GRANT SELECT,INSERT,UPDATE,DELETE ON user_export_jobs TO app_runtime;
GRANT SELECT,INSERT ON private_deletion_events TO app_runtime;
GRANT SELECT ON schema_migrations TO app_runtime;

CREATE OR REPLACE FUNCTION bootstrap_owner(
  p_user_id uuid,
  p_email_ciphertext bytea,
  p_session_id uuid,
  p_token_hash text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM users WHERE deleted_at IS NULL) THEN
    RAISE EXCEPTION 'owner_already_initialized';
  END IF;
  INSERT INTO users(id,email_ciphertext,role,status)
    VALUES(p_user_id,p_email_ciphertext,'owner','active');
  INSERT INTO sessions(id,user_id,token_hash,expires_at)
    VALUES(p_session_id,p_user_id,p_token_hash,now()+interval '12 hours');
END
$$;

CREATE OR REPLACE FUNCTION authenticate_session(p_token_hash text)
RETURNS TABLE(id uuid, role text)
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public, pg_temp
AS $$
  SELECT u.id,u.role
  FROM sessions s JOIN users u ON u.id=s.user_id
  WHERE s.token_hash=p_token_hash
    AND s.revoked_at IS NULL
    AND s.expires_at>now()
    AND u.deleted_at IS NULL
    AND u.status='active'
  LIMIT 1
$$;

CREATE OR REPLACE FUNCTION accept_invitation_session(
  p_token_hash text,
  p_user_id uuid,
  p_session_id uuid,
  p_session_hash text,
  p_email_ciphertext bytea
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_role text;
BEGIN
  SELECT role INTO v_role FROM invitations
  WHERE token_hash=p_token_hash AND accepted_at IS NULL
    AND revoked_at IS NULL AND expires_at>now()
  FOR UPDATE;
  IF v_role IS NULL THEN
    RAISE EXCEPTION 'invalid_or_expired_invitation';
  END IF;
  INSERT INTO users(id,email_ciphertext,role) VALUES(p_user_id,p_email_ciphertext,v_role);
  INSERT INTO sessions(id,user_id,token_hash,expires_at)
    VALUES(p_session_id,p_user_id,p_session_hash,now()+interval '12 hours');
  UPDATE invitations SET accepted_by=p_user_id,accepted_at=now()
    WHERE token_hash=p_token_hash;
  RETURN v_role;
END
$$;

CREATE OR REPLACE FUNCTION purge_current_account(p_user_id uuid, p_event_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  IF p_user_id IS DISTINCT FROM app_current_user_id() THEN
    RAISE EXCEPTION 'account_scope_mismatch';
  END IF;
  INSERT INTO private_deletion_events(
    id,owner_id,resource_type,resource_id,deletion_mode,replay_impact
  ) VALUES (
    p_event_id,p_user_id,'account',p_user_id,'purge','replay_unavailable'
  );
  DELETE FROM invitations WHERE issued_by=p_user_id OR accepted_by=p_user_id;
  DELETE FROM profiles WHERE owner_id=p_user_id;
  DELETE FROM sessions WHERE user_id=p_user_id;
  DELETE FROM user_export_jobs WHERE owner_id=p_user_id;
  UPDATE users SET email_ciphertext=decode('','hex'),role='viewer',
    status='deleted',deleted_at=now() WHERE id=p_user_id;
END
$$;

REVOKE ALL ON FUNCTION bootstrap_owner(uuid,bytea,uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION authenticate_session(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION accept_invitation_session(text,uuid,uuid,text,bytea) FROM PUBLIC;
REVOKE ALL ON FUNCTION purge_current_account(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION bootstrap_owner(uuid,bytea,uuid,text) TO app_runtime;
GRANT EXECUTE ON FUNCTION authenticate_session(text) TO app_runtime;
GRANT EXECUTE ON FUNCTION accept_invitation_session(text,uuid,uuid,text,bytea) TO app_runtime;
GRANT EXECUTE ON FUNCTION purge_current_account(uuid,uuid) TO app_runtime;

COMMENT ON TABLE user_export_jobs IS
  'Export metadata only. Temporary archive bytes live outside PostgreSQL and expire within 24h.';
COMMENT ON TABLE private_deletion_events IS
  'Minimal deletion audit without retaining deleted private prose.';
COMMIT;
