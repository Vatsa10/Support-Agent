# Resolve.

**The AI support operator that actually resolves.**

Resolve is a multi-tenant SaaS that drops into any business's stack and **handles** customer support — refund, replace, cancel, close tickets — through real backends (Stripe, Shopify, Zendesk, custom webhooks), guarded by per-tool policy, idempotent, audited end-to-end.

This repo is the full system: **FastAPI backend** + **Next.js frontend** (marketing + dashboard + embeddable chat widget + hosted chat page).

---

## What's in the box

```
Support-Agent/
├── src/                  # Python backend (FastAPI + LangGraph ReACT)
│   ├── agents/react.py           # ReACT loop (think → act → observe)
│   ├── tools/                    # Read-only tools + action tools + idempotency + registry
│   ├── connectors/               # Stripe / Shopify / Zendesk / generic webhook
│   ├── policy/                   # Caps, approval thresholds, frequency, sentiment gates
│   ├── budget/                   # Per-tenant monthly token caps
│   ├── safety/                   # Prompt-injection guard
│   ├── security/crypto.py        # Fernet encryption for tenant secrets
│   ├── billing/meter.py          # LLM token meter
│   ├── memory/buffer.py          # Postgres-backed, tenant-scoped conversation memory
│   ├── vector_db/                # pgvector + tsvector hybrid retrieval
│   ├── db/{pool,schema.sql}      # asyncpg pool, RLS-enabled schema
│   ├── cache/valkey.py           # Aiven Valkey (Redis-compatible)
│   ├── observability/            # JSON logging + request-id + /metrics
│   ├── scheduler/                # APScheduler — approval timeout sweep
│   └── api/                      # REST surface (chat, admin, tenant, webhooks)
│
├── frontend/             # Next.js 14 (app router) + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx                       # Landing (hero, pricing, FAQ)
│   │   ├── (auth)/signin · signup         # Sign-in / sign-up
│   │   ├── (app)/                         # Dashboard (gated)
│   │   │   ├── dashboard                  # KPIs + spark + recent
│   │   │   ├── conversations[/id]         # ReACT timeline
│   │   │   ├── actions / approvals
│   │   │   ├── integrations / policies
│   │   │   ├── kb / billing / keys
│   │   │   ├── install / settings
│   │   ├── c/[slug]                       # Hosted standalone chat (shareable URL)
│   │   └── embed/[tenant]                 # Iframe chat (widget loads this)
│   ├── public/widget.js                   # Embeddable widget loader
│   └── components/{marketing,app}
│
├── tests/                # pytest scaffold (encryption, prompt-guard, idempotency, webhook sig)
├── Dockerfile + docker-compose.yml
└── aiven.py              # Connectivity smoke test
```

---

## How customers reach the operator (three surfaces, one engine)

| Surface                                          | Install                                       | When to use                                                     |
| ------------------------------------------------ | --------------------------------------------- | --------------------------------------------------------------- |
| **Site widget** (`/widget.js`)           | One `<script>` tag → floating launcher     | Default. Sits on order / account pages where context lives.     |
| **Hosted chat URL** (`/c/<tenant-slug>`) | Just a link. Optional CNAME for custom domain | Email signatures, QR codes, transactional emails, status pages. |
| **Headless API** (`POST /api/chat`)      | HTTP, bring your own UI                       | Apps already shipping a chat surface.                           |

Identity is verified via per-tenant HMAC-SHA256 of the customer's `user_id`, signed server-side. Without it, sessions are anonymous (no action attribution / per-user rate limit).

---

## Stack

| Layer            | Choice                                                 | Why                                                                                  |
| ---------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| LLM              | **Google Gemini 2.0 Flash**                      | Fast, cheap, supports tool routing. Swappable.                                       |
| Embeddings       | **Gemini `embedding-001`**                     | 768-dim, matches pgvector index.                                                     |
| Reasoning        | **LangGraph ReACT**                              | Think → act → observe loop with explicit state.                                    |
| Vectors + memory | **Aiven Postgres + `pgvector` + `tsvector`** | Single store: tenant registry, memory, audit, vectors, BM25. RLS-enforced isolation. |
| Cache            | **Aiven Valkey**                                 | Rate limit, idempotency keys, hot session cache, breaker counters.                   |
| API              | **FastAPI**                                      | async, typed, observability hooks.                                                   |
| Frontend         | **Next.js 14 + Tailwind**                        | App router, server components, JetBrains Mono for IDs.                               |

---

## Quick start (local)

### 0. Prereqs

- Python 3.11+, Node 20+, Docker (for Postgres + Valkey)
- A Google Generative AI key — [aistudio.google.com](https://aistudio.google.com/)

### 1. Backend env

```bash
cp .env.example .env
# Fill GOOGLE_API_KEY, ADMIN_API_KEY, ENCRYPTION_KEY (Fernet).
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Bring up Postgres + Valkey + app

```bash
docker compose up -d postgres valkey
pip install -r requirements.txt
python -m src.db.migrations              # apply schema + RLS
uvicorn api.server:app --reload --port 8000 --app-dir src
```

Health: `GET /healthz` → `{"status":"ok","pg":true,"valkey":true}`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

### 4. Create your first tenant

```bash
# 1. Create tenant (returns api_key once)
curl -X POST http://localhost:8000/admin/tenants \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Goods"}'

# 2. Connect Stripe (test key)
curl -X POST http://localhost:8000/tenant/integrations \
  -H "X-API-Key: $TENANT_KEY" \
  -d '{"kind":"stripe","creds":{"api_key":"sk_test_…","webhook_secret":"whsec_…"}}'

# 3. Author refund policy
curl -X POST http://localhost:8000/tenant/policies \
  -H "X-API-Key: $TENANT_KEY" \
  -d '{"tool_name":"issue_refund","allow":true,"max_amount":500,"requires_approval_above":200}'

# 4. Upload KB
curl -X POST http://localhost:8000/tenant/kb/upload \
  -H "X-API-Key: $TENANT_KEY" \
  -d '{"source":"returns-policy.md","text":"30-day returns. Damaged on arrival: full refund."}'

# 5. Chat
curl -X POST http://localhost:8000/api/chat \
  -H "X-API-Key: $TENANT_KEY" \
  -d '{"message":"refund my last order, it arrived broken","user_id":"u_42"}'
```

---

## Backend surface

### Public

- `POST /api/chat` — `X-API-Key` + optional `X-End-User-JWT` → ReACT runs, returns answer.
- `GET  /api/chat/history/{user_id}/{thread_id}` — replay messages.

### Tenant self-serve (`X-API-Key`)

- `POST/GET/DELETE /tenant/integrations` — manage Stripe / Shopify / Zendesk / webhook creds (encrypted at rest).
- `POST/GET /tenant/policies` — per-tool caps + approval thresholds.
- `POST/GET/DELETE /tenant/kb/{upload,sources}` — KB ingest by HTTP, no filesystem.
- `POST /tenant/jwt-secret` — rotate end-user JWT secret.
- `GET /tenant/approvals` · `POST /tenant/approvals/{id}/decision` — review the queue.
- `GET /tenant/billing` — token usage this cycle.
- `POST /tenant/budget` — set monthly hard cap.
- `POST /tenant/end-users/{id}/delete` · `GET /tenant/end-users/{id}/export` — GDPR.

### Admin (`X-Admin-Key`)

- `POST/GET/DELETE /admin/tenants[/{id}]` — tenant CRUD, `/suspend`, `/activate`.
- Mirrors of the tenant surface for support / impersonation.

### Inbound webhooks

- `POST /webhooks/{tenant_id}/{stripe|shopify|zendesk}` — HMAC verified, persisted to `webhook_events`, reconciles `action_runs` state.

### Operational

- `GET /healthz` — deep check (PG + Valkey).
- `GET /metrics` — Prometheus exposition (HTTP, tool runs, tokens).

---

## Embedding the widget

```html
<!-- paste before </body> -->
<script>
  (function () {
    var s = document.createElement("script");
    s.src = "https://app.resolve.app/widget.js";
    s.async = 1;
    s.dataset.tenant = "acme";
    s.dataset.publishableKey = "rsv_pub_live_…";
    document.head.appendChild(s);
  })();
</script>

<!-- recommended: identify logged-in users -->
<script>
  window.ResolveSettings = {
    user_id:   "u_42",
    email:     "kira@acme.co",
    user_hmac: "{{ server-side HMAC-SHA256(user_id, tenant_secret) }}",
    context:   { order_id: "SH-29481", plan: "pro" }
  };
</script>

<!-- programmatic — e.g. inline "Get help" button next to an order -->
<button onclick="Resolve('open', { context: { order_id: 'SH-29481' } })">
  Get help with this order
</button>
```

API (post-load): `Resolve('boot' | 'open' | 'close' | 'set' | 'shutdown' | 'on', …)`.

---

## How resolution actually works

```
user message
   │
   ▼
ReACT.think  ──── LLM ───►  tokens metered + Prometheus counter
   │ chooses action
   ▼
policy.evaluate  ── action_policies row, caps, sentiment gate, freq
   │      allow / deny / approval
   ▼
idempotency.reserve ── Valkey SETNX + idempotency_keys row
   │      fresh / replay
   ▼
connector.execute  ── Stripe / Shopify / Zendesk / webhook
   │      retry + circuit-breaker per integration
   ▼
action_runs row + audit_log + billing_events
   │
   ▼
vendor webhook (later) ─► reconciles action_runs.status to truth
```

Every leg is recorded. Replays return cached results. Pending approvals time out after `APPROVAL_TIMEOUT_HOURS` and auto-reject.

---

## Security posture

- **Postgres Row-Level Security on every tenant table.** App role cannot bypass.
- **Fernet (AES-128 + HMAC) at rest** for tenant connector credentials and JWT secrets. Key in `ENCRYPTION_KEY`.
- **HMAC verification** on every inbound webhook (Stripe/Shopify/Zendesk).
- **Prompt-injection scrub** on retrieved KB context before LLM ingestion.
- **Idempotency** on every side-effecting tool — replays cannot double-charge.
- **Rate limit** per (tenant, end_user) in Valkey.
- **Hard budget cap** in tokens — chat returns 402 when exceeded.

---

## Roadmap

| Phase                                                                                                       | Status     |
| ----------------------------------------------------------------------------------------------------------- | ---------- |
| 1 — Multi-tenant foundation (PG + Valkey + RLS + auth)                                                     | ✅ Shipped |
| 2 — Action authority (connectors + policy + idempotency + audit + JWT + billing)                           | ✅ Shipped |
| 3 — Production hardening (webhooks in + tenant self-serve + budgets + breaker + GDPR + scheduler + Docker) | ✅ Shipped |
| 4 — Frontend (landing + dashboard + widget + hosted chat)                                                  | ✅ Shipped |
| 5 — Multi-channel (Slack / email / WhatsApp ingestion)                                                     | 🟡 Next    |
| 6 — BYO LLM (Anthropic / OpenAI / self-hosted)                                                             | 🟡 Next    |
| 7 — Admin web UI for staff, SSO, SOC2                                                                      | 🟡 Next    |

---

## License

Source-available under PolyForm-style terms for now. Commercial use requires a license.

Made for operators.
