import { Lock, GitBranch, ShieldCheck, Gauge, Repeat, Globe2, Sparkles, FileSearch } from "lucide-react";

const cells = [
  { i: Lock,        t: "Tenant-isolated by default",  d: "Postgres RLS + per-tenant Valkey namespacing. Zero cross-tenant reads, ever." },
  { i: GitBranch,   t: "Per-tool policy engine",      d: "Caps, approval thresholds, frequency windows, sentiment gates — declared per tool." },
  { i: ShieldCheck, t: "Idempotent everything",       d: "Replays are free. Same Stripe call, same outcome, twice or twenty times." },
  { i: Gauge,       t: "Token + cost budgets",        d: "Hard-cap monthly LLM spend at the tenant level. Soft alerts at any threshold." },
  { i: Repeat,      t: "Retry + circuit-break",       d: "Tenacity exponential retry, then a breaker per integration that fails fast." },
  { i: Globe2,      t: "Inbound webhooks",            d: "Stripe / Shopify / Zendesk events reconcile action_runs state automatically." },
  { i: Sparkles,    t: "Prompt-injection scrubbing",  d: "KB context sanitized before LLM ingestion. Defense-in-depth, no surprises." },
  { i: FileSearch,  t: "Audited from think to act",   d: "Every thought, action, and observation persisted, replayable, exportable." }
];

export function FeatureGrid() {
  return (
    <section id="features" className="border-b border-line">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="flex items-end justify-between gap-6 mb-12">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">02 — what's under the hood</div>
            <h2 className="font-display text-[44px] md:text-[56px] leading-[1] tracking-tightest max-w-[14ch]">
              Built like infrastructure, not a demo.
            </h2>
          </div>
          <p className="text-ink-2 text-[14.5px] max-w-md hidden md:block">
            Every primitive a SaaS support team wishes existed — already in the box. RLS, audit, idempotency,
            policy, budgets, observability. The boring parts done right.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-line border border-line">
          {cells.map(({ i: Icon, t, d }, idx) => (
            <div key={t} className="bg-paper p-7 min-h-[180px] flex flex-col gap-4 hover:bg-cream transition">
              <div className="flex items-center justify-between">
                <Icon size={18} className="text-blue" strokeWidth={1.6} />
                <span className="font-mono text-[11px] text-ink-3">{String(idx + 1).padStart(2, "0")}</span>
              </div>
              <div>
                <h3 className="font-display text-[22px] leading-tight tracking-tightest">{t}</h3>
                <p className="mt-2 text-ink-2 text-[13.5px] leading-[1.55]">{d}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
