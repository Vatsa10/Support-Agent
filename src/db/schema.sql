-- Multi-tenant SaaS schema for Support Agent.
-- Apply as superuser (avnadmin on Aiven). App connects as RLS_ROLE (default: app_user).

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- App role (no superuser; RLS enforced)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user NOINHERIT LOGIN PASSWORD 'app_user_pw_change_me';
    END IF;
END$$;

GRANT USAGE ON SCHEMA public TO app_user;

-- =========================================================================
-- tenants (system table — no RLS; resolved by API key hash)
-- =========================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,
    api_key_hash    text NOT NULL UNIQUE,
    status          text NOT NULL DEFAULT 'active',
    plan            text NOT NULL DEFAULT 'free',
    created_at      timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE ON tenants TO app_user;

-- =========================================================================
-- tenant_settings
-- =========================================================================
CREATE TABLE IF NOT EXISTS tenant_settings (
    tenant_id               uuid PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    system_prompt_override  text,
    top_k                   int NOT NULL DEFAULT 5,
    confidence_threshold    real NOT NULL DEFAULT 0.7,
    rate_limit_per_min      int NOT NULL DEFAULT 60,
    updated_at              timestamptz NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_settings TO app_user;

-- =========================================================================
-- conversations
-- =========================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id     text NOT NULL,
    thread_id   text NOT NULL,
    started_at  timestamptz NOT NULL DEFAULT now(),
    last_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id, thread_id)
);

CREATE INDEX IF NOT EXISTS conversations_tenant_idx ON conversations(tenant_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO app_user;

-- =========================================================================
-- messages
-- =========================================================================
CREATE TABLE IF NOT EXISTS messages (
    id              bigserial PRIMARY KEY,
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text NOT NULL CHECK (role IN ('user','assistant','system')),
    content         text NOT NULL,
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_conv_time_idx ON messages(conversation_id, created_at);
GRANT SELECT, INSERT, DELETE ON messages TO app_user;
GRANT USAGE, SELECT ON SEQUENCE messages_id_seq TO app_user;

-- =========================================================================
-- kb_documents (vectors + lexical)
-- =========================================================================
CREATE TABLE IF NOT EXISTS kb_documents (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source       text NOT NULL,
    section      text,
    category     text,
    key_phrases  text[],
    chunk_text   text NOT NULL,
    embedding    vector(768),
    tsv          tsvector,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS kb_documents_tenant_idx ON kb_documents(tenant_id);
CREATE INDEX IF NOT EXISTS kb_documents_tsv_idx    ON kb_documents USING GIN (tsv);
CREATE INDEX IF NOT EXISTS kb_documents_emb_idx    ON kb_documents USING hnsw (embedding vector_cosine_ops);

GRANT SELECT, INSERT, UPDATE, DELETE ON kb_documents TO app_user;

-- =========================================================================
-- tickets
-- =========================================================================
CREATE TABLE IF NOT EXISTS tickets (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id     text NOT NULL,
    thread_id   text,
    category    text,
    intent      text,
    sentiment   text,
    status      text NOT NULL DEFAULT 'open',
    resolution  jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS tickets_tenant_idx ON tickets(tenant_id);
GRANT SELECT, INSERT, UPDATE ON tickets TO app_user;

-- =========================================================================
-- audit_log (Phase 2 fills with action calls)
-- =========================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id          bigserial PRIMARY KEY,
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id     text,
    thread_id   text,
    tool_name   text NOT NULL,
    input       jsonb NOT NULL DEFAULT '{}'::jsonb,
    output      jsonb NOT NULL DEFAULT '{}'::jsonb,
    reasoning   text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_tenant_time_idx ON audit_log(tenant_id, created_at DESC);
GRANT SELECT, INSERT ON audit_log TO app_user;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO app_user;

-- =========================================================================
-- Row-Level Security
-- All tenant-scoped tables: only rows where tenant_id = current_setting('app.tenant_id') visible.
-- =========================================================================

ALTER TABLE tenant_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations   ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages        ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_documents    ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets         ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log       ENABLE ROW LEVEL SECURITY;

ALTER TABLE tenant_settings FORCE ROW LEVEL SECURITY;
ALTER TABLE conversations   FORCE ROW LEVEL SECURITY;
ALTER TABLE messages        FORCE ROW LEVEL SECURITY;
ALTER TABLE kb_documents    FORCE ROW LEVEL SECURITY;
ALTER TABLE tickets         FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_log       FORCE ROW LEVEL SECURITY;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['tenant_settings','conversations','messages','kb_documents','tickets','audit_log']
    LOOP
        EXECUTE format($f$
            DROP POLICY IF EXISTS tenant_isolation ON %I;
            CREATE POLICY tenant_isolation ON %I
                USING (tenant_id::text = current_setting('app.tenant_id', true))
                WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
        $f$, t, t);
    END LOOP;
END$$;
