import Link from "next/link";
import { Topbar } from "@/components/app/Topbar";
import { ReactTimeline } from "@/components/app/ReactTimeline";
import { StatusPill } from "@/components/app/StatusPill";
import { trace } from "@/lib/mock";
import { ChevronLeft } from "lucide-react";

export default function ConversationDetail({ params }: { params: { id: string } }) {
  return (
    <>
      <Topbar
        crumb={[
          { label: "Operate" },
          { label: "Conversations", href: "/conversations" },
          { label: params.id }
        ]}
      />
      <div className="px-6 lg:px-10 py-8">
        <Link href="/conversations" className="inline-flex items-center gap-1 text-[12.5px] text-ink-2 hover:text-blue mb-6">
          <ChevronLeft size={14} /> Back to all
        </Link>

        <div className="grid lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-[11.5px] text-ink-3">{params.id}</span>
              <StatusPill status="resolved" />
            </div>
            <h1 className="font-display text-[36px] leading-[1.05] tracking-tightest">
              Refund for order <span className="italic text-blue">SH-29481</span>
            </h1>
            <p className="mt-3 text-ink-2 text-[14px]">
              Started 14m ago · 6 reasoning steps · 1 side-effect · $48.20 refunded via Stripe
            </p>

            <div className="mt-8 border border-line bg-paper p-6">
              <ReactTimeline trace={trace as any} />
            </div>
          </div>

          <aside className="lg:col-span-4 space-y-6">
            <Card title="Customer">
              <KV k="Email" v="kira@acme.co" mono />
              <KV k="End user ID" v="u_44a02" mono />
              <KV k="Sentiment" v="neutral" />
              <KV k="Tickets / 30d" v="2" />
            </Card>
            <Card title="Action runs">
              <KV k="issue_refund" v="re_3PqW…7c1" mono pill="succeeded" />
            </Card>
            <Card title="Reconciliation">
              <KV k="Webhook event" v="charge.refunded · evt_71…" mono />
              <KV k="Latency" v="4.1s" />
              <KV k="Signature" v="verified" pill="active" />
            </Card>
            <Card title="Tools available">
              <div className="flex flex-wrap gap-1.5">
                {["knowledge_search","classify_intent","issue_refund","cancel_subscription","create_ticket"].map(t => (
                  <span key={t} className="font-mono text-[11px] bg-cream border border-line px-1.5 py-1 text-ink-2">{t}</span>
                ))}
              </div>
            </Card>
          </aside>
        </div>
      </div>
    </>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-line bg-paper">
      <div className="px-4 h-9 border-b border-line flex items-center text-[11px] uppercase tracking-[0.18em] text-ink-3">
        {title}
      </div>
      <div className="p-4 space-y-2.5">{children}</div>
    </div>
  );
}

function KV({ k, v, mono, pill }: { k: string; v: string; mono?: boolean; pill?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-[13px]">
      <span className="text-ink-2">{k}</span>
      <span className="flex items-center gap-2">
        {pill && <StatusPill status={pill} />}
        <span className={mono ? "font-mono text-ink" : "text-ink"}>{v}</span>
      </span>
    </div>
  );
}
