export function HowItWorks() {
  const steps = [
    {
      n: "01",
      title: "Connect",
      body:
        "Drop in your Stripe / Shopify / Zendesk keys. Resolve encrypts them per tenant and lights up the matching action tools — automatically.",
      code: `POST /tenant/integrations
{ "kind": "stripe",
  "creds": { "api_key": "sk_live_…" } }`
    },
    {
      n: "02",
      title: "Author policy",
      body:
        "Declare what the operator can do, up to what amount, and when a human should approve. Resolve enforces it before every call.",
      code: `POST /tenant/policies
{ "tool_name": "issue_refund",
  "allow": true,
  "max_amount": 500,
  "requires_approval_above": 200 }`
    },
    {
      n: "03",
      title: "Let it operate",
      body:
        "Send a chat. Resolve thinks, calls real backends with idempotent retries, audits every step, and replies — usually in under 15 seconds.",
      code: `POST /api/chat
X-API-Key: rsv_live_…
{ "message": "i need a refund",
  "user_id": "u_42" }`
    }
  ];

  return (
    <section id="how" className="border-b border-line bg-cream">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">03 — how it works</div>
        <h2 className="font-display text-[44px] md:text-[56px] leading-[1] tracking-tightest max-w-[14ch] mb-14">
          Three moves to a working operator.
        </h2>
        <div className="grid lg:grid-cols-3 gap-px bg-line border border-line">
          {steps.map((s) => (
            <div key={s.n} className="bg-paper p-8 flex flex-col gap-8">
              <div className="flex items-center justify-between">
                <span className="font-display italic text-blue text-[34px] leading-none">{s.n}</span>
                <span className="font-mono text-[11px] uppercase tracking-widest text-ink-3">step</span>
              </div>
              <div>
                <h3 className="font-display text-[28px] leading-tight tracking-tightest">{s.title}</h3>
                <p className="mt-3 text-ink-2 text-[14px] leading-[1.55]">{s.body}</p>
              </div>
              <pre className="mt-auto font-mono text-[12px] leading-[1.55] bg-ink text-paper p-4 overflow-auto">
                <code>{s.code}</code>
              </pre>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
