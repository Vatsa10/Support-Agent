import Link from "next/link";
import { Nav } from "@/components/marketing/Nav";
import { Footer } from "@/components/marketing/Footer";

const sections = [
  {
    id: "quickstart",
    title: "Quickstart",
    body:
      "1) Sign up at /signup → tenant + first API key created.\n2) Connect at least one integration (Stripe/Shopify/Zendesk/webhook).\n3) Author a policy per tool — caps + approval thresholds.\n4) Upload your KB on /kb (markdown / text).\n5) Generate a publishable key on /onboarding and embed the widget.\n6) First customer message → ReACT thinks → calls the connector → audit + billing recorded."
  },
  {
    id: "auth",
    title: "Authentication",
    body:
      "Three keys you'll touch:\n• X-API-Key (tenant key): server-to-server only. Manages integrations, policies, KB, etc.\n• rsv_pub_* (publishable key): browser-safe. POSTs /public/chat. Created via /tenant/publishable-keys.\n• X-End-User-JWT (HS256): signs the end-user id with your tenant JWT secret. Optional but recommended."
  },
  {
    id: "chat-api",
    title: "Chat API",
    body:
      "POST /api/chat\n  Headers: X-API-Key, optional X-End-User-JWT\n  Body: { message, user_id, thread_id? }\n  Returns: { thread_id, response, status, ticket_id, metadata{category,intent,sentiment}, action_run_id? }\n\nPOST /public/chat (CORS-open)\n  Body: { message, publishable_key, user_id?, thread_id?, end_user_jwt? }\n  Same return shape."
  },
  {
    id: "tools",
    title: "Action tools",
    body:
      "Surfaced to the agent only if the matching connector is enabled for the tenant:\n• issue_refund (Stripe) — charge_id, amount, currency, reason\n• cancel_subscription (Stripe) — subscription_id, reason\n• replace_order (Shopify) — order_id, reason\n• cancel_order (Shopify) — order_id, reason, refund?\n• close_zendesk_ticket / comment_zendesk_ticket\n• generic_webhook_call — action_name, payload (allowed actions from config)\n\nEvery action runs through: idempotency → policy → connector → action_runs row → webhook reconcile."
  },
  {
    id: "policy",
    title: "Policy",
    body:
      "POST /tenant/policies\n  { tool_name, allow, max_amount?, requires_approval_above?, frequency_per_user_per_day?, blocked_categories?[] }\n\nDefault-deny: any action tool without a row returns 'no policy; denied'.\n\nSentiment gate: 'frustrated' sentiment forces approval on non-comment tools, no matter the cap."
  },
  {
    id: "webhooks",
    title: "Inbound webhooks (reconciliation)",
    body:
      "POST /webhooks/{tenant_id}/{stripe|shopify|zendesk}\n\nSignature verified per vendor. webhook_events persisted (idempotent). action_runs status reconciled when an external_id matches.\n\nConfigure the vendor's webhook URL to point here; set the matching webhook_secret in your integration creds."
  },
  {
    id: "security",
    title: "Security model",
    body:
      "• Tenant isolation: Postgres RLS on every multi-tenant table; app role cannot bypass.\n• Encryption at rest: Fernet (AES-128 + HMAC) for connector creds + JWT secrets. Master key in ENCRYPTION_KEY.\n• Idempotency: every side-effecting tool keyed by (tenant, args). Replays return cached results.\n• Rate limit: per (tenant, end_user) in Valkey.\n• Prompt-injection guard: KB context scrubbed before LLM ingestion.\n• Hard budget cap: chat returns 402 once month token cap is hit."
  },
  {
    id: "byo-llm",
    title: "Bring your own LLM",
    body:
      "POST /tenant/llm\n  { provider: 'google'|'anthropic'|'openai', model, temperature, api_key? }\n\nProviders supported: Google Gemini (default), Anthropic Claude, OpenAI GPT. Per-tenant config overrides env defaults. API keys stored encrypted at rest."
  }
];

export default function Docs() {
  return (
    <main>
      <Nav />
      <section className="border-b border-line">
        <div className="mx-auto max-w-7xl px-6 py-16 grid lg:grid-cols-12 gap-12">
          <aside className="lg:col-span-3 lg:sticky lg:top-20 self-start">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-3">Docs · v3.0</div>
            <h1 className="font-display text-[40px] leading-[1] tracking-tightest mb-6">
              Resolve <span className="italic text-blue">handbook.</span>
            </h1>
            <nav className="space-y-2 text-[13.5px]">
              {sections.map((s) => (
                <Link key={s.id} href={`#${s.id}`} className="block text-ink-2 hover:text-blue">
                  {s.title}
                </Link>
              ))}
              <hr className="border-line my-3" />
              <Link href="/install" className="block text-ink-2 hover:text-blue">Install snippets →</Link>
              <Link href="/signup" className="block text-ink-2 hover:text-blue">Start free →</Link>
            </nav>
          </aside>

          <div className="lg:col-span-9 space-y-14">
            {sections.map((s) => (
              <article key={s.id} id={s.id} className="scroll-mt-24">
                <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">§ {s.id}</div>
                <h2 className="font-display text-[34px] leading-[1.1] tracking-tightest mb-5">{s.title}</h2>
                <pre className="font-mono text-[13px] leading-[1.7] text-ink whitespace-pre-wrap break-words border-l-2 border-line pl-5">
{s.body}
                </pre>
              </article>
            ))}
          </div>
        </div>
      </section>
      <Footer />
    </main>
  );
}
