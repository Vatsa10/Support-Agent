import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function Hero() {
  return (
    <section className="hero-wash relative overflow-hidden border-b border-line">
      <div className="absolute inset-0 bg-grid opacity-60 pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-24 md:pt-28 md:pb-32">
        {/* Eyebrow */}
        <div className="flex items-center gap-2 text-[12px] uppercase tracking-[0.18em] text-ink-2 mb-10 animate-fadein">
          <span className="w-6 h-px bg-ink-2/60" />
          <span>v3 · the operator release</span>
        </div>

        {/* Headline */}
        <h1 className="font-display text-[clamp(44px,7.6vw,108px)] leading-[0.94] tracking-tightest max-w-[14ch]">
          <span className="animate-rise [animation-delay:60ms]">The AI support </span>
          <span className="animate-rise [animation-delay:160ms] inline-block">operator that</span>
          <br />
          <span className="italic text-blue animate-rise [animation-delay:260ms] inline-block">actually&nbsp;resolves.</span>
        </h1>

        <p className="mt-8 max-w-2xl text-[17px] leading-[1.55] text-ink-2 animate-rise [animation-delay:380ms]">
          Refund, replace, cancel, close — without queues, without humans. Resolve runs as an authorized
          operator on top of your existing stack, with audited policy, idempotent actions, and an approval
          queue when a person should weigh in.
        </p>

        <div className="mt-10 flex flex-wrap items-center gap-3 animate-rise [animation-delay:500ms]">
          <Link
            href="/signup"
            className="group inline-flex items-center gap-2 h-11 px-5 bg-ink text-paper text-[14px] hover:bg-blue transition"
          >
            Start free
            <ArrowUpRight size={16} className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
          <Link
            href="#how"
            className="inline-flex items-center gap-2 h-11 px-5 border border-ink text-[14px] hover:bg-ink hover:text-paper transition"
          >
            See how it works
          </Link>
          <span className="ml-2 text-[12.5px] text-ink-3 font-mono">
            $0 forever for &lt; 200 resolutions / mo
          </span>
        </div>

        {/* Operator card preview */}
        <div className="mt-20 grid lg:grid-cols-12 gap-6 animate-rise [animation-delay:640ms]">
          <div className="lg:col-span-7 border border-line bg-paper">
            <div className="flex items-center justify-between border-b border-line px-4 h-9 text-[12px] text-ink-2">
              <div className="flex items-center gap-2 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-success" /> live
                <span className="text-ink-3">/ conversation c_8af31</span>
              </div>
              <span className="font-mono">14s · 6 steps · $48.20 refunded</span>
            </div>
            <div className="p-6 space-y-4 text-[14px] leading-[1.55]">
              <Line role="customer" text="hey i need a refund for order SH-29481, item arrived broken" />
              <Trace step="thought" text="Returns category, neutral sentiment. Order in 30-day window. Policy permits up to $500." />
              <Trace step="action" text="knowledge_search" meta="returns-policy.md, shipping-faq.md" />
              <Trace step="action" text="issue_refund" meta="ch_3PqW…42b · amount=48.20 · stripe" />
              <Trace step="observation" text="Stripe re_3PqW…7c1 succeeded. Reconciled via webhook." />
              <Line role="agent" text="I've issued your $48.20 refund. It'll appear in 3–5 business days. Anything else?" />
            </div>
          </div>

          <div className="lg:col-span-5 grid grid-cols-2 gap-px bg-line border border-line">
            <Kpi label="Mean resolve" value="14s" />
            <Kpi label="Deflection" value="84.2%" />
            <Kpi label="Action success" value="96.7%" />
            <Kpi label="Audit coverage" value="100%" />
          </div>
        </div>
      </div>
    </section>
  );
}

function Line({ role, text }: { role: "customer" | "agent"; text: string }) {
  return (
    <div className="flex gap-3">
      <span
        className={
          "shrink-0 w-[64px] font-mono text-[10.5px] uppercase tracking-widest pt-1 " +
          (role === "customer" ? "text-ink-3" : "text-blue")
        }
      >
        {role === "customer" ? "customer" : "resolve"}
      </span>
      <p className={role === "customer" ? "text-ink-2" : "text-ink"}>{text}</p>
    </div>
  );
}

function Trace({ step, text, meta }: { step: "thought" | "action" | "observation"; text: string; meta?: string }) {
  const color = step === "thought" ? "text-ink-3" : step === "action" ? "text-blue" : "text-ink-2";
  return (
    <div className="flex gap-3 items-start font-mono text-[12.5px]">
      <span className={"shrink-0 w-[64px] uppercase tracking-widest pt-0.5 " + color}>{step}</span>
      <div>
        <span className={step === "action" ? "text-ink" : "text-ink-2"}>{text}</span>
        {meta && <span className="text-ink-3"> &nbsp;· {meta}</span>}
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-paper p-5">
      <div className="text-[11px] uppercase tracking-[0.16em] text-ink-3">{label}</div>
      <div className="mt-2 font-display text-[36px] leading-none tracking-tightest">{value}</div>
    </div>
  );
}
