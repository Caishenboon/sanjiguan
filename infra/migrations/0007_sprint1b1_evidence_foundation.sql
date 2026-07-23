-- Sprint 1B-1: evidence collection only. No divination interpretation or scoring.
BEGIN;

ALTER TABLE idempotency_records DROP CONSTRAINT IF EXISTS idempotency_records_http_method_check;
ALTER TABLE idempotency_records ADD CONSTRAINT idempotency_records_http_method_check
  CHECK (http_method IN ('POST','PUT','PATCH','DELETE'));

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS archive_name_ciphertext bytea,
  ADD COLUMN IF NOT EXISTS language_code text NOT NULL DEFAULT 'zh-CN',
  ADD COLUMN IF NOT EXISTS long_term_storage_consent boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS future_report_consent boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS location_withdrawn_at timestamptz;

ALTER TABLE evidence_items
  ADD COLUMN domain text CHECK (domain IN ('ming','gua','karma','vow','dream','sensation','relation','life_event')),
  ADD COLUMN title_ciphertext bytea,
  ADD COLUMN structured_payload_encrypted bytea,
  ADD COLUMN first_observed_age numeric(5,2),
  ADD COLUMN intensity smallint CHECK (intensity BETWEEN 0 AND 10),
  ADD COLUMN duration_years numeric(6,2) CHECK (duration_years >= 0),
  ADD COLUMN source_type text CHECK (source_type IN
    ('document','self_memory','family_memory','repeated_observation','single_event')),
  ADD COLUMN user_confidence numeric(4,3) CHECK (user_confidence BETWEEN 0 AND 1),
  ADD COLUMN independent_corroboration boolean NOT NULL DEFAULT false,
  ADD COLUMN reliability_score numeric(4,3) CHECK (reliability_score BETWEEN 0 AND 1),
  ADD COLUMN reliability_level text CHECK (reliability_level IN ('high','medium','low')),
  ADD COLUMN status text NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft','confirmed','disputed','withdrawn')),
  ADD COLUMN event_occurred_at timestamptz,
  ADD COLUMN recorded_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN deleted_at timestamptz;

CREATE TABLE onboarding_sessions (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
  current_step smallint NOT NULL DEFAULT 1 CHECK (current_step BETWEEN 1 AND 8),
  step_states jsonb NOT NULL DEFAULT '{}'::jsonb,
  encrypted_draft bytea NOT NULL,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE evidence_revisions (
  id uuid PRIMARY KEY,
  evidence_id uuid NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
  revision_no integer NOT NULL CHECK (revision_no > 0),
  snapshot_encrypted bytea NOT NULL,
  changed_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(evidence_id, revision_no)
);

CREATE TABLE life_events (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  title_ciphertext bytea NOT NULL,
  narrative_encrypted bytea,
  occurred_from date,
  occurred_to date,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

ALTER TABLE journal_entries
  ADD COLUMN IF NOT EXISTS entry_type text NOT NULL DEFAULT 'reflection',
  ADD COLUMN IF NOT EXISTS structured_payload_encrypted bytea,
  ADD COLUMN IF NOT EXISTS candidate_evidence boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

ALTER TABLE relationship_subjects DROP CONSTRAINT IF EXISTS relationship_subjects_mode_check;
ALTER TABLE relationship_subjects DROP CONSTRAINT IF EXISTS relationship_subjects_check;
ALTER TABLE relationship_subjects ADD CONSTRAINT relationship_subjects_mode_check
  CHECK (mode IN ('consented_profile','pending_consent','anonymous_event'));
ALTER TABLE relationship_subjects ADD CONSTRAINT relationship_subjects_integrity_check CHECK (
  (mode='consented_profile' AND linked_profile_id IS NOT NULL AND consent_record_encrypted IS NOT NULL)
  OR (mode='pending_consent' AND linked_profile_id IS NOT NULL)
  OR (mode='anonymous_event' AND linked_profile_id IS NULL)
);

CREATE TABLE journal_evidence_links (
  journal_entry_id uuid NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
  evidence_id uuid NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(journal_entry_id,evidence_id)
);

CREATE TABLE divination_sessions (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  question_encrypted bytea NOT NULL,
  purpose_encrypted bytea NOT NULL,
  divination_at timestamptz NOT NULL,
  timezone text NOT NULL,
  location_precision text NOT NULL CHECK (location_precision IN ('none','region','city')),
  method_id text NOT NULL CHECK (method_id='YIJING.THREE_COIN.PHYSICAL.V1'),
  interrupted_retoss boolean NOT NULL DEFAULT false,
  repeated_due_to_dissatisfaction boolean NOT NULL DEFAULT false,
  method_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE coin_tosses (
  id uuid PRIMARY KEY,
  divination_session_id uuid NOT NULL REFERENCES divination_sessions(id) ON DELETE CASCADE,
  line_no smallint NOT NULL CHECK (line_no BETWEEN 1 AND 6),
  coin_faces text[] NOT NULL CHECK (
    cardinality(coin_faces)=3 AND coin_faces <@ ARRAY['heads','tails']::text[]),
  raw_value smallint NOT NULL CHECK (raw_value BETWEEN 6 AND 9),
  was_retossed boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(divination_session_id,line_no)
);

CREATE TABLE profile_completeness_snapshots (
  id uuid PRIMARY KEY,
  profile_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  dimensions jsonb NOT NULL,
  overall_state text NOT NULL CHECK (overall_state IN
    ('not_filled','not_applicable','unknown','explicit_none','filled_low_reliability','filled_high_reliability')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX evidence_domain_time_idx ON evidence_items(profile_id,domain,event_occurred_at);
CREATE INDEX evidence_recorded_idx ON evidence_items(profile_id,recorded_at);
CREATE INDEX life_events_timeline_idx ON life_events(profile_id,occurred_from);
CREATE INDEX journal_date_type_idx ON journal_entries(profile_id,entry_date,entry_type);
CREATE INDEX divinations_profile_time_idx ON divination_sessions(profile_id,divination_at);

ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE evidence_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_revisions FORCE ROW LEVEL SECURITY;
ALTER TABLE life_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE life_events FORCE ROW LEVEL SECURITY;
ALTER TABLE journal_evidence_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_evidence_links FORCE ROW LEVEL SECURITY;
ALTER TABLE divination_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE divination_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE coin_tosses ENABLE ROW LEVEL SECURITY;
ALTER TABLE coin_tosses FORCE ROW LEVEL SECURITY;
ALTER TABLE profile_completeness_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_completeness_snapshots FORCE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION owns_profile(target uuid) RETURNS boolean
LANGUAGE sql STABLE AS $$
  SELECT EXISTS(SELECT 1 FROM profiles p WHERE p.id=target AND
    (p.owner_id=app_current_user_id() OR app_current_user_role()='owner'))
$$;

CREATE POLICY onboarding_owner ON onboarding_sessions FOR ALL TO app_runtime
USING (owns_profile(profile_id)) WITH CHECK (owns_profile(profile_id));
CREATE POLICY revisions_owner ON evidence_revisions FOR ALL TO app_runtime
USING (EXISTS(SELECT 1 FROM evidence_items e WHERE e.id=evidence_id AND owns_profile(e.profile_id)))
WITH CHECK (EXISTS(SELECT 1 FROM evidence_items e WHERE e.id=evidence_id AND owns_profile(e.profile_id)));
CREATE POLICY life_events_owner ON life_events FOR ALL TO app_runtime
USING (owns_profile(profile_id)) WITH CHECK (owns_profile(profile_id));
CREATE POLICY journal_links_owner ON journal_evidence_links FOR ALL TO app_runtime
USING (EXISTS(SELECT 1 FROM journal_entries j WHERE j.id=journal_entry_id AND owns_profile(j.profile_id)))
WITH CHECK (EXISTS(SELECT 1 FROM journal_entries j WHERE j.id=journal_entry_id AND owns_profile(j.profile_id)));
CREATE POLICY divinations_owner ON divination_sessions FOR ALL TO app_runtime
USING (owns_profile(profile_id)) WITH CHECK (owns_profile(profile_id));
CREATE POLICY coin_tosses_owner ON coin_tosses FOR ALL TO app_runtime
USING (EXISTS(SELECT 1 FROM divination_sessions d WHERE d.id=divination_session_id AND owns_profile(d.profile_id)))
WITH CHECK (EXISTS(SELECT 1 FROM divination_sessions d WHERE d.id=divination_session_id AND owns_profile(d.profile_id)));
CREATE POLICY completeness_owner ON profile_completeness_snapshots FOR ALL TO app_runtime
USING (owns_profile(profile_id)) WITH CHECK (owns_profile(profile_id));

GRANT SELECT,INSERT,UPDATE,DELETE ON onboarding_sessions,evidence_revisions,life_events,
  journal_evidence_links,divination_sessions,coin_tosses,profile_completeness_snapshots TO app_runtime;

COMMIT;
