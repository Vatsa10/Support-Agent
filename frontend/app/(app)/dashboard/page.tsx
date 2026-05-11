import Link from "next/link";
import { Topbar } from "@/components/app/Topbar";
import { Kpi } from "@/components/app/Kpi";
import { Sparkline } from "@/components/app/Sparkline";
import { StatusPill } from "@/components/app/StatusPill";
import { DataTable } from "@/components/app/DataTable";
import { EmptyState } from "@/components/app/EmptyState";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtCompact, fmtPct, fmtTimeAgo, shortId } from "@/lib/fmt";

type Stats = {
  tenant_name: string;
  kpis: {
    resolutions_30d: number;
    deflection_rate: number;
    action_success_rate: number;
    approvals_pending: number;
    monthly_tokens: number;
    token_cap: number;
  };
  sparkline: number[];
  recent: { id: string; thread_id: string; user_id: string; last_at: string; last_msg: string; last_action: string }[];
};

export default async function DashboardOverview() {
  const s = await backendFetchSafe<Stats>("/tenant/stats");
  if (!s) {
    return (
      <>
        <Topbar crumb={[{ label: "Workspace" }, { label: "Overview" }]} />
        <div className="px-6 lg:px-10 py-8">
          <EmptyState
            title="Backend not reachable."
            body="Make sure the FastAPI server is running on port 8000 and try again."
          />
        </div>
      </>
    );
  }

  const k = s.kpis;
  const budgetPct = k.token_cap ? Math.min(1, k.monthly_tokens / k.token_cap) : 0;
  const sparkValues = s.sparkline.length ? s.sparkline : [0, 0, 0];
  const noActivity = k.resolutions_30d === 0;

  return (
    <>
      <Topbar crumb={[{ label: s.tenant_name }, { label: "Overview" }]} />

      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-8">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Last 30 days</div>
            <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
              Welcome to <span className="italic text-blue">{s.tenant_name}.</span>
            </h1>
            <p className="text-ink-2 text-[14px] mt-1">
              {noActivity
                ? "No conversations yet. Connect an integration and embed the widget to start resolving."
                : <>Resolve handled <span className="text-ink font-mono">{fmtCompact(k.resolutions_30d)}</span> conversations this month.</>}
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2 font-mono text-[11px] text-ink-3">
            <span className="w-1.5 h-1.5 rounded-full bg-success" /> live · /api/chat
          </div>
        </div>

        {noActivity && (
          <div className="border border-line bg-paper p-6 mb-8 grid md:grid-cols-3 gap-px bg-line">
            <Quickstart num="01" title="Install widget" body="Drop a script tag on your site. 30 seconds." href="/install" cta="Get snippet" />
            <Quickstart num="02" title="Connect Stripe / Shopify" body="Let Resolve act, not just chat." href="/integrations" cta="Connect" />
            <Quickstart num="03" title="Upload knowledge base" body="Policies + FAQs ground every answer." href="/kb" cta="Upload" />
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-px bg-line border border-line">
          <Kpi label="Resolutions" value={fmtCompact(k.resolutions_30d)} hint="last 30d" />
          <Kpi label="Deflection" value={k.resolutions_30d ? fmtPct(k.deflection_rate) : "—"} hint="resolved w/o human" />
          <Kpi label="Action success" value={fmtPct(k.action_success_rate)} hint="non-denied succeeded" />
          <Kpi label="Approvals" value={String(k.approvals_pending)} hint="pending review" />
          <Kpi
            label="Tokens"
            value={fmtCompact(k.monthly_tokens)}
            hint={k.token_cap ? `of ${fmtCompact(k.token_cap)} cap` : "no cap set"}
          />
        </div>

        <div className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Resolutions per day</div>
              <span className="font-mono text-[11px] text-ink-3">last 15d</span>
            </div>
            <div className="p-5">
              <Sparkline values={sparkValues} w={720} h={200} />
            </div>
          </div>

          <div className="border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Token budget</div>
              <span className="font-mono text-[11px] text-ink-3">{new Date().toLocaleString("default", { month: "short" })}</span>
            </div>
            <div className="p-5">
              <div className="font-display text-[40px] leading-none tracking-tightest">{fmtCompact(k.monthly_tokens)}</div>
              <div className="text-[12px] text-ink-2 mt-1">
                {k.token_cap ? `of ${fmtCompact(k.token_cap)} cap · ${(budgetPct * 100).toFixed(1)}% used` : "Set a monthly cap in Billing"}
              </div>
              <div className="mt-5 h-1.5 bg-line-2 relative">
                <div className="absolute left-0 top-0 bottom-0 bg-blue" style={{ width: `${budgetPct * 100}%` }} />
              </div>
              <Link href="/billing" className="mt-5 inline-flex h-9 px-3 border border-line text-[13px] hover:border-ink">
                Configure budget →
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <div className="flex items-end justify-between mb-3">
            <h2 className="font-display text-[24px] leading-tight tracking-tightest">Latest conversations</h2>
            <Link href="/conversations" className="text-[13px] text-ink-2 hover:text-blue">View all →</Link>
          </div>
          {s.recent.length === 0 ? (
            <EmptyState
              title="No conversations yet."
              body="Embed the widget or share your hosted chat URL — your first resolution will land here."
              cta={{ label: "Install widget", href: "/install" }}
            />
          ) : (
            <DataTable
              columns={[
                { key: "id", label: "ID", width: "120px", render: (r) => <span className="font-mono text-ink-2">{shortId(r.id, 8)}</span> },
                { key: "last_msg", label: "Last message" },
                { key: "user_id", label: "Customer", width: "220px", render: (r) => <span className="font-mono text-ink-2">{r.user_id}</span> },
                { key: "last_action", label: "Last action", width: "200px", render: (r) => <span className="font-mono text-ink-2">{r.last_action || "—"}</span> },
                { key: "last_at", label: "Updated", width: "120px", align: "right", render: (r) => <span className="text-ink-3">{r.last_at ? fmtTimeAgo(r.last_at) : "—"}</span> }
              ]}
              rows={s.recent as any}
              rowHref={(r: any) => `/conversations/${r.id}`}
            />
          )}
        </div>
      </div>
    </>
  );
}

function Quickstart({ num, title, body, href, cta }: { num: string; title: string; body: string; href: string; cta: string }) {
  return (
    <div className="bg-paper p-5">
      <div className="flex items-center justify-between">
        <span className="font-display italic text-blue text-[24px] leading-none">{num}</span>
        <span className="font-mono text-[10.5px] uppercase tracking-widest text-ink-3">setup</span>
      </div>
      <div className="mt-4 font-display text-[20px] tracking-tightest">{title}</div>
      <p className="mt-1 text-[13px] text-ink-2 leading-[1.55]">{body}</p>
      <Link href={href} className="mt-4 inline-flex h-9 px-3 border border-ink text-[13px] hover:bg-ink hover:text-paper">
        {cta} →
      </Link>
    </div>
  );
}
