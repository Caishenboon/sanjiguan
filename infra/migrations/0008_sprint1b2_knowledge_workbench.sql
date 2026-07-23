-- Sprint 1B-2: research-only knowledge governance and rule workbench.
BEGIN;

ALTER TABLE knowledge_documents
  ADD COLUMN original_title text, ADD COLUMN translator text, ADD COLUMN editor text,
  ADD COLUMN publication_year integer, ADD COLUMN traditions text[] NOT NULL DEFAULT '{}',
  ADD COLUMN knowledge_layer text, ADD COLUMN access_class text NOT NULL DEFAULT 'unknown',
  ADD COLUMN license_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN catalog_identifier text, ADD COLUMN language text NOT NULL DEFAULT 'zh',
  ADD COLUMN review_status text NOT NULL DEFAULT 'draft', ADD COLUMN reviewer_ids uuid[] NOT NULL DEFAULT '{}',
  ADD COLUMN notes text, ADD COLUMN created_by uuid REFERENCES users(id),
  ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now(), ADD COLUMN deleted_at timestamptz;
ALTER TABLE knowledge_documents ALTER COLUMN tradition DROP NOT NULL;
ALTER TABLE knowledge_documents ALTER COLUMN checksum DROP NOT NULL;
ALTER TABLE knowledge_documents DROP CONSTRAINT IF EXISTS knowledge_documents_status_check;
ALTER TABLE knowledge_documents ADD CHECK (review_status IN ('draft','researched','reviewed','approved','rejected','retired'));
ALTER TABLE knowledge_documents ADD CHECK (knowledge_layer IN ('canonical_text','traditional_commentary',
  'lineage_teaching','modern_scholarship','historical_source','system_interpretation','engineering_fact','case_pattern'));
ALTER TABLE knowledge_documents ADD CHECK (access_class IN ('public_domain','open_license','licensed_internal',
  'citation_only','copyright_restricted','practice_restricted','sealed','unknown'));

CREATE TABLE knowledge_document_versions(
  id uuid PRIMARY KEY,document_id uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  version_no integer NOT NULL CHECK(version_no>0),snapshot_json jsonb NOT NULL,changed_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(document_id,version_no));
CREATE TABLE source_licenses(
  id uuid PRIMARY KEY,document_id uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  access_class text NOT NULL,license_name text,license_version text,license_url text,
  attribution_required boolean NOT NULL DEFAULT true,scope text,expires_at timestamptz,
  verification_status text NOT NULL DEFAULT 'unverified',verified_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE access_policies(
  id uuid PRIMARY KEY,access_class text NOT NULL UNIQUE,fulltext_allowed boolean NOT NULL,
  embedding_allowed boolean NOT NULL,rag_allowed boolean NOT NULL,direct_quote_allowed boolean NOT NULL,
  production_allowed boolean NOT NULL,notes text NOT NULL);

CREATE OR REPLACE FUNCTION knowledge_layer_guard(target uuid,expected text) RETURNS boolean LANGUAGE sql STABLE AS
$$ SELECT EXISTS(SELECT 1 FROM knowledge_documents WHERE id=target AND knowledge_layer=expected) $$;

CREATE TABLE knowledge_claims(
  id uuid PRIMARY KEY,document_id uuid NOT NULL REFERENCES knowledge_documents(id),
  claim_text text NOT NULL,claim_type text NOT NULL CHECK(claim_type IN ('traditional_statement','system_mapping',
    'historical_rule','engineering_fact','scholarly_interpretation')),
  traditions text[] NOT NULL DEFAULT '{}',locator_json jsonb NOT NULL,source_excerpt text,paraphrase text,
  access_class text NOT NULL,confidence text NOT NULL CHECK(confidence IN ('verified','probable','uncertain','disputed')),
  review_status text NOT NULL DEFAULT 'draft' CHECK(review_status IN ('draft','researched','reviewed','approved','rejected','retired')),
  reviewer_ids uuid[] NOT NULL DEFAULT '{}',allowed_uses jsonb NOT NULL,
  created_by uuid NOT NULL REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,
  CHECK(confidence<>'verified' OR locator_json<>'{}'::jsonb),
  CHECK(claim_type<>'system_mapping' OR knowledge_layer_guard(document_id,'system_interpretation')));
CREATE TABLE knowledge_claim_versions(
  id uuid PRIMARY KEY,claim_id uuid NOT NULL REFERENCES knowledge_claims(id) ON DELETE CASCADE,
  version_no integer NOT NULL CHECK(version_no>0),snapshot_json jsonb NOT NULL,changed_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(claim_id,version_no));
CREATE TABLE knowledge_claim_relations(
  source_claim_id uuid NOT NULL REFERENCES knowledge_claims(id) ON DELETE CASCADE,
  target_claim_id uuid NOT NULL REFERENCES knowledge_claims(id) ON DELETE CASCADE,
  relation text NOT NULL CHECK(relation IN ('supports','contradicts','supersedes')),
  created_by uuid NOT NULL REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(source_claim_id,target_claim_id,relation),CHECK(source_claim_id<>target_claim_id));
CREATE TABLE knowledge_topics(id uuid PRIMARY KEY,slug text NOT NULL UNIQUE,label text NOT NULL);
CREATE TABLE knowledge_claim_topics(claim_id uuid REFERENCES knowledge_claims(id) ON DELETE CASCADE,
  topic_id uuid REFERENCES knowledge_topics(id) ON DELETE CASCADE,PRIMARY KEY(claim_id,topic_id));
CREATE TABLE reviewer_profiles(id uuid PRIMARY KEY,user_id uuid NOT NULL UNIQUE REFERENCES users(id),
  public_label text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE reviewer_qualifications(id uuid PRIMARY KEY,reviewer_id uuid NOT NULL REFERENCES reviewer_profiles(id),
  domain text NOT NULL,tradition text,qualification_claim text NOT NULL,verification_status text NOT NULL,
  verified_by uuid REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE knowledge_reviews(id uuid PRIMARY KEY,claim_id uuid NOT NULL REFERENCES knowledge_claims(id),
  reviewer_id uuid NOT NULL REFERENCES reviewer_profiles(id),review_type text NOT NULL,
  decision text NOT NULL CHECK(decision IN ('approved','rejected','changes_requested')),
  notes text,created_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE rule_drafts(
  id text PRIMARY KEY,name text NOT NULL,domain text NOT NULL,status text NOT NULL DEFAULT 'draft',
  production_activatable boolean NOT NULL DEFAULT false,method_id text NOT NULL DEFAULT 'UNCONFIRMED',
  definition_json jsonb NOT NULL,needs_review boolean NOT NULL DEFAULT false,golden_examples_passed boolean NOT NULL DEFAULT false,
  created_by uuid NOT NULL REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz,
  CHECK(status<>'active'));
CREATE TABLE rule_versions(id uuid PRIMARY KEY,rule_id text NOT NULL REFERENCES rule_drafts(id),
  version text NOT NULL,snapshot_json jsonb NOT NULL,changed_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(rule_id,version));
CREATE TABLE rule_claim_links(rule_id text REFERENCES rule_drafts(id) ON DELETE CASCADE,
  claim_id uuid REFERENCES knowledge_claims(id),basis_type text NOT NULL CHECK(basis_type IN ('traditional','system','engineering')),
  PRIMARY KEY(rule_id,claim_id,basis_type));
CREATE TABLE archetype_research_records(
  id uuid PRIMARY KEY,name text NOT NULL,category text NOT NULL,status text NOT NULL DEFAULT 'research',
  research_json jsonb NOT NULL,created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),deleted_at timestamptz);
CREATE TABLE archetype_claim_links(archetype_id uuid REFERENCES archetype_research_records(id) ON DELETE CASCADE,
  claim_id uuid REFERENCES knowledge_claims(id),relation text NOT NULL,PRIMARY KEY(archetype_id,claim_id,relation));

CREATE OR REPLACE FUNCTION mark_linked_rules_for_review() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.claim_text IS DISTINCT FROM NEW.claim_text OR OLD.locator_json IS DISTINCT FROM NEW.locator_json
     OR OLD.review_status IS DISTINCT FROM NEW.review_status THEN
    UPDATE rule_drafts SET needs_review=true,updated_at=now()
      WHERE id IN (SELECT rule_id FROM rule_claim_links WHERE claim_id=NEW.id);
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER claim_change_rule_review AFTER UPDATE ON knowledge_claims
FOR EACH ROW EXECUTE FUNCTION mark_linked_rules_for_review();

INSERT INTO access_policies VALUES
 ('018f0000-0000-7000-8000-000000000001','public_domain',true,true,true,true,true,'retain attribution'),
 ('018f0000-0000-7000-8000-000000000002','open_license',true,true,true,true,true,'follow license'),
 ('018f0000-0000-7000-8000-000000000003','licensed_internal',true,false,false,false,false,'scope-bound'),
 ('018f0000-0000-7000-8000-000000000004','citation_only',false,false,false,true,false,'bibliography and short quote only'),
 ('018f0000-0000-7000-8000-000000000005','copyright_restricted',false,false,false,false,false,'no full text'),
 ('018f0000-0000-7000-8000-000000000006','practice_restricted',false,false,false,false,false,'no practice steps'),
 ('018f0000-0000-7000-8000-000000000007','sealed',false,false,false,false,false,'metadata minimum only'),
 ('018f0000-0000-7000-8000-000000000008','unknown',false,false,false,false,false,'deny by default');

GRANT INSERT ON audit_events TO app_runtime;
GRANT USAGE,SELECT ON SEQUENCE audit_events_id_seq TO app_runtime;

DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['knowledge_documents','knowledge_document_versions',
'source_licenses','access_policies','knowledge_claims','knowledge_claim_versions','knowledge_claim_relations',
'knowledge_topics','knowledge_claim_topics','reviewer_profiles','reviewer_qualifications','knowledge_reviews',
'rule_drafts','rule_versions','rule_claim_links','archetype_research_records','archetype_claim_links']
LOOP EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
EXECUTE format('CREATE POLICY owner_only ON %I FOR ALL TO app_runtime USING (app_current_user_role()=''owner'') WITH CHECK (app_current_user_role()=''owner'')',t);
EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON %I TO app_runtime',t); END LOOP; END $$;
COMMIT;
