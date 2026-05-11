import Link from "next/link";
import { Check } from "lucide-react";

const tiers = [
  {
    name: "Operator",
    price: "$0",
    cadence: "forever",
    note: "Up to 200 resolutions / mo",
    features: [
      "1 connected tool (Stripe or Shopify)",
      "Knowledge base up to 200 chunks",
      "7-day audit retention",
      "Community support"
    ],
    cta: "Start free"
  },
  {
    name: "Scale",
    price: "$0.18",
    cadence: "per resolution",
    note: "Billing on token + per-action; transparent",
    features: [
      "All connectors",
      "Approval queue + JWT auth for end users",
      "90-day audit retention + export",
      "Slack alerts, custom domains",
      "Priority email support"
    ],
    cta: "Start trial",
    featured: true
  },
  {
    name: "Enterprise",
    price: "Custom",
    cadence: "annual",
    note: "VPC peering, SSO, BYO key, SOC2 in-flight",
    features: [
      "Dedicated compute",
      "Custom connectors + SLAs",
      "On-prem KMS for tenant secrets",
      "Named CSM",
      "DPA + procurement"
    ],
    cta: "Talk to us"
  }
];

export function Pricing() {
  return (
    <section id="pricing" className="border-b border-line">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid lg:grid-cols-12 gap-6 mb-14">
          <div className="lg:col-span-5">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">04 — pricing</div>
            <h2 className="font-display text-[44px] md:text-[56px] leading-[1] tracking-tightest">
              You only pay for <span className="italic text-blue">work&nbsp;done</span>.
            </h2>
          </div>
          <div className="lg:col-span-7 lg:pl-10 self-end">
            <p className="text-ink-2 text-[15px] leading-[1.6]">
              Per-resolution pricing with hard budget caps. No seats, no engagement minimums, no escalation
              tax. Tokens metered transparently in the dashboard.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-px bg-line border border-line">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={
                "p-8 flex flex-col gap-6 " +
                (t.featured ? "bg-ink text-paper" : "bg-paper")
              }
            >
              <div className="flex items-center justify-between">
                <span className={"font-display text-[22px] leading-none " + (t.featured ? "text-paper" : "")}>
                  {t.name}
                </span>
                {t.featured && (
                  <span className="font-mono text-[10.5px] uppercase tracking-widest text-blue bg-paper/10 px-2 py-1">
                    most popular
                  </span>
                )}
              </div>
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="font-display text-[64px] leading-none tracking-tightest">{t.price}</span>
                  <span className={"text-[13px] " + (t.featured ? "text-paper/70" : "text-ink-2")}>
                    {t.cadence}
                  </span>
                </div>
                <p className={"mt-2 text-[13px] " + (t.featured ? "text-paper/70" : "text-ink-2")}>
                  {t.note}
                </p>
              </div>
              <ul className="space-y-2.5 mt-2">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-[13.5px]">
                    <Check
                      size={14}
                      strokeWidth={2}
                      className={"mt-1 " + (t.featured ? "text-blue" : "text-blue")}
                    />
                    <span className={t.featured ? "text-paper/90" : "text-ink-2"}>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/signup"
                className={
                  "mt-auto inline-flex items-center justify-center h-11 text-[13.5px] transition " +
                  (t.featured
                    ? "bg-blue text-paper hover:bg-paper hover:text-ink"
                    : "border border-ink text-ink hover:bg-ink hover:text-paper")
                }
              >
                {t.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
