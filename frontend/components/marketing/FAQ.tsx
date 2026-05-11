"use client";
import { useState } from "react";
import { Plus, Minus } from "lucide-react";

const faqs = [
  {
    q: "How is Resolve different from a chatbot?",
    a: "Chatbots answer. Resolve acts. Every conversation can finish in a real refund, replacement, cancellation, or ticket close — through your Stripe / Shopify / Zendesk — with policy guardrails and an audit trail per attempt."
  },
  {
    q: "What happens if the agent gets something wrong?",
    a: "Policy gates every side-effecting call. Anything over your configured threshold goes to the approval queue. Every attempt is idempotent (replays are safe), every step is in audit_log, and vendor webhooks reconcile state."
  },
  {
    q: "Is my data isolated from other tenants?",
    a: "Yes. Postgres Row-Level Security is on by default. Every query runs under a SET LOCAL tenant_id; the app role cannot bypass it. Valkey keys are namespaced per tenant. Connector credentials are Fernet-encrypted at rest."
  },
  {
    q: "Which LLMs do you use?",
    a: "Gemini 2.0 Flash by default for the ReACT loop and embedding-001 for retrieval. The model layer is swappable; enterprise customers can BYO key on Anthropic, OpenAI, or self-hosted models."
  },
  {
    q: "Can I run Resolve on-prem?",
    a: "Yes — the Enterprise tier ships a deployable bundle (Docker / Helm) that runs against your VPC. State lives in your Postgres + Redis. Get in touch and we'll scope a deployment."
  },
  {
    q: "Where do my customers' messages go?",
    a: "Into your dedicated row partition in our Postgres (or yours, on Enterprise). They never enter shared embeddings, never train any model, and are deletable on request via the GDPR endpoint."
  }
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" className="border-b border-line">
      <div className="mx-auto max-w-7xl px-6 py-24 grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">05 — questions</div>
          <h2 className="font-display text-[44px] md:text-[56px] leading-[1] tracking-tightest">
            Things people <span className="italic text-blue">ask first.</span>
          </h2>
        </div>
        <div className="lg:col-span-8 border-t border-line">
          {faqs.map((f, i) => {
            const active = open === i;
            return (
              <button
                key={f.q}
                onClick={() => setOpen(active ? null : i)}
                className="w-full text-left border-b border-line py-6 group"
              >
                <div className="flex items-start justify-between gap-6">
                  <span className="font-display text-[22px] md:text-[24px] leading-tight tracking-tightest">
                    {f.q}
                  </span>
                  <span className="shrink-0 mt-1 text-ink-2 group-hover:text-blue transition">
                    {active ? <Minus size={18} /> : <Plus size={18} />}
                  </span>
                </div>
                <div
                  className={
                    "grid transition-all duration-300 ease-out " +
                    (active ? "grid-rows-[1fr] opacity-100 mt-4" : "grid-rows-[0fr] opacity-0")
                  }
                >
                  <div className="overflow-hidden">
                    <p className="text-ink-2 text-[14.5px] leading-[1.6] max-w-2xl">{f.a}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
