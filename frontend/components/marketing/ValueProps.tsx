import { CircleDollarSign, PackageOpen, X, MessageCircleOff } from "lucide-react";

const items = [
  {
    icon: CircleDollarSign,
    title: "Refunds, issued.",
    body: "Resolve calls your Stripe in real time with idempotent retries. Customers stop waiting; you stop staffing queues."
  },
  {
    icon: PackageOpen,
    title: "Replacements, drafted.",
    body: "Shopify replacement orders created and originals cancelled in one transaction. Audit trail per attempt."
  },
  {
    icon: X,
    title: "Tickets, closed.",
    body: "Zendesk and Intercom tickets resolved with a public comment in seconds — or routed for approval if policy says so."
  },
  {
    icon: MessageCircleOff,
    title: "Less chat, more done.",
    body: "Resolve isn't a chatbot. Every conversation ends in an action, an answer, or a precise hand-off."
  }
];

export function ValueProps() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">01 — what it does</div>
            <h2 className="font-display text-[44px] md:text-[56px] leading-[1] tracking-tightest">
              Not a chatbot.
              <br />
              <span className="italic text-blue">An operator.</span>
            </h2>
            <p className="mt-6 text-ink-2 text-[15.5px] leading-[1.6] max-w-md">
              Conversations finish on Resolve. The agent reasons, calls your real backend, and confirms with the
              customer — all inside a single transaction with a verifiable audit log.
            </p>
          </div>
          <div className="lg:col-span-8 grid sm:grid-cols-2 gap-px bg-line border border-line">
            {items.map(({ icon: Icon, title, body }) => (
              <div key={title} className="bg-paper p-8 group">
                <Icon size={20} className="text-blue mb-6 transition group-hover:-translate-y-0.5" strokeWidth={1.6} />
                <h3 className="font-display text-[26px] leading-tight tracking-tightest">{title}</h3>
                <p className="mt-3 text-ink-2 text-[14px] leading-[1.55]">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
