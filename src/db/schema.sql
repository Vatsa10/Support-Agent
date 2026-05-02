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

-- =========================================================================
-- Phase 2: action authority, connectors, policy, billing, JWT
-- =========================================================================

-- tenant_integrations: per-tenant connector credentials + config (creds encrypted)
CREATE TABLE IF NOT EXISTS tenant_integrations (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    kind             text NOT NULL,
    label            text NOT NULL DEFAULT 'default',
    encrypted_creds  bytea NOT NULL,
    config           jsonb NOT NULL DEFAULT '{}'::jsonb,
    enabled          boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, kind, label)
);
CREATE INDEX IF NOT EXISTS tenant_integrations_tenant_idx ON tenant_integrations(tenant_id);
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_integrations TO app_user;

-- tenant_jwt_secrets: per-tenant secret used to verify end-user JWTs
CREATE TABLE IF NOT EXISTS tenant_jwt_secrets (
    tenant_id    uuid PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    secret       bytea NOT NULL,
    alg          text NOT NULL DEFAULT 'HS256',
    updated_at   timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_jwt_secrets TO app_user;

-- action_policies: per (tenant, tool) caps + approval thresholds
CREATE TABLE IF NOT EXISTS action_policies (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    tool_name                   text NOT NULL,
    allow                       boolean NOT NULL DEFAULT false,
    max_amount                  numeric,
    currency                    text,
    requires_approval_above     numeric,
    frequency_per_user_per_day  int,
    blocked_categories          text[],
    extra                       jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at                  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, tool_name)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON action_policies TO app_user;

-- idempotency_keys: replay-safety for side-effecting actions
CREATE TABLE IF NOT EXISTS idempotency_keys (
    tenant_id    uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key          text NOT NULL,
    tool_name    text NOT NULL,
    status       text NOT NULL DEFAULT 'running',
    result       jsonb,
    created_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, key)
);
GRANT SELECT, INSERT, UPDATE ON idempotency_keys TO app_user;

-- action_runs: every attempted side-effecting action
CREATE TABLE IF NOT EXISTS action_runs (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id          uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id            text NOT NULL,
    end_user_id        text,
    thread_id          text,
    tool_name          text NOT NULL,
    args               jsonb NOT NULL DEFAULT '{}'::jsonb,
    status             text NOT NULL,
    result             jsonb,
    error              text,
    idempotency_key    text,
    created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS action_runs_tenant_time_idx ON action_runs(tenant_id, created_at DESC);
GRANT SELECT, INSERT, UPDATE ON action_runs TO app_user;

-- approvals: human-in-the-loop queue
CREATE TABLE IF NOT EXISTS approvals (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    action_run_id   uuid NOT NULL REFERENCES action_runs(id) ON DELETE CASCADE,
    status          text NOT NULL DEFAULT 'pending',
    decided_by      text,
    decision        text,
    reason          text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    decided_at      timestamptz
);
CREATE INDEX IF NOT EXISTS approvals_pending_idx
    ON approvals(tenant_id, created_at DESC) WHERE status = 'pending';
GRANT SELECT, INSERT, UPDATE ON approvals TO app_user;

-- billing_events: token meter
CREATE TABLE IF NOT EXISTS billing_events (
    id           bigserial PRIMARY KEY,
    tenant_id    uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id      text,
    thread_id    text,
    event_type   text NOT NULL,
    units        bigint NOT NULL,
    metadata     jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS billing_events_tenant_time_idx ON billing_events(tenant_id, created_at DESC);
GRANT SELECT, INSERT ON billing_events TO app_user;
GRANT USAGE, SELECT ON SEQUENCE billing_events_id_seq TO app_user;

-- =========================================================================
-- RLS for Phase 1 + Phase 2 tables
-- =========================================================================

ALTER TABLE tenant_settings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations        ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages             ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_documents         ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets              ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log            ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_integrations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_jwt_secrets   ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_policies      ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys     ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_runs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals            ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_events       ENABLE ROW LEVEL SECURITY;

ALTER TABLE tenant_settings      FORCE ROW LEVEL SECURITY;
ALTER TABLE conversations        FORCE ROW LEVEL SECURITY;
ALTER TABLE messages             FORCE ROW LEVEL SECURITY;
ALTER TABLE kb_documents         FORCE ROW LEVEL SECURITY;
ALTER TABLE tickets              FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_log            FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_integrations  FORCE ROW LEVEL SECURITY;
ALTER TABLE tenant_jwt_secrets   FORCE ROW LEVEL SECURITY;
ALTER TABLE action_policies      FORCE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys     FORCE ROW LEVEL SECURITY;
ALTER TABLE action_runs          FORCE ROW LEVEL SECURITY;
ALTER TABLE approvals            FORCE ROW LEVEL SECURITY;
ALTER TABLE billing_events       FORCE ROW LEVEL SECURITY;

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'tenant_settings','conversations','messages','kb_documents','tickets','audit_log',
        'tenant_integrations','tenant_jwt_secrets','action_policies','idempotency_keys',
        'action_runs','approvals','billing_events'
    ]
    LOOP
        EXECUTE format($f$
            DROP POLICY IF EXISTS tenant_isolation ON %I;
            CREATE POLICY tenant_isolation ON %I
                USING (tenant_id::text = current_setting('app.tenant_id', true))
                WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
        $f$, t, t);
    END LOOP;
END$$;
