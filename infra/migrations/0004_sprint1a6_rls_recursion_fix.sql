-- Remove profiles <-> profile_grants policy recursion using a narrowly scoped
-- SECURITY DEFINER predicate owned by the migration superuser.
BEGIN;

CREATE OR REPLACE FUNCTION has_active_profile_grant(target_profile uuid, required_scope text)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profile_grants g
    WHERE g.profile_id = target_profile
      AND g.grantee_user_id = public.app_current_user_id()
      AND g.permission = 'read'
      AND required_scope = ANY(g.scope)
      AND g.status = 'active'
      AND g.revoked_at IS NULL
      AND (g.expires_at IS NULL OR g.expires_at > now())
  )
$$;
REVOKE ALL ON FUNCTION has_active_profile_grant(uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION has_active_profile_grant(uuid,text) TO app_runtime;

DROP POLICY IF EXISTS profiles_select ON profiles;
CREATE POLICY profiles_select ON profiles FOR SELECT TO app_runtime
USING (
  owner_id = app_current_user_id()
  OR app_current_user_role() = 'owner'
  OR has_active_profile_grant(id, 'profile:read')
);

DROP POLICY IF EXISTS grants_visible_owner_or_grantee ON profile_grants;
CREATE POLICY grants_visible_participant ON profile_grants FOR SELECT TO app_runtime
USING (
  grantee_user_id = app_current_user_id()
  OR granted_by = app_current_user_id()
  OR app_current_user_role() = 'owner'
);

COMMIT;
