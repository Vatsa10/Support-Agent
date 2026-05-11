import { Topbar } from "@/components/app/Topbar";
import { Kpi } from "@/components/app/Kpi";
import { Sparkline } from "@/components/app/Sparkline";
import { StatusPill } from "@/components/app/StatusPill";
import { DataTable } from "@/components/app/DataTable";
import { kpis, sparkline, conversations } from "@/lib/mock";
import { fmtCompact, fmtPct, fmtTimeAgo, shortId } from "@/lib/fmt";

export default function DashboardOverview() {
  const budgetPct = kpis.monthly_tokens / kpis.token_cap;
  return (
    <>
      <Topbar crumb={[{ label: "Workspace" }, { label: "Overview" }]} />

      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-8">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Last 30 days</div>
            <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
              Good morning, <span className="italic text-blue">Kira.</span>
            </h1>
            <p className="text-ink-2 text-[14px] mt-1">
              Resolve handled <span className="text-ink font-mono">{fmtCompact(kpis.resolutions_30d)}</span> conversations this month.
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2 font-mono text-[11px] text-ink-3">
            <span className="w-1.5 h-1.5 rounded-full bg-success" /> live · streaming from /api/chat
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-px bg-line border border-line">
          <Kpi label="Resolutions" value={fmtCompact(kpis.resolutions_30d)} delta="+18.4%" hint="vs prior 30d" />
          <Kpi label="Deflection rate" value={fmtPct(kpis.deflection_rate)} delta="+2.1%" hint="resolved without human" />
          <Kpi label="Action success" value={fmtPct(kpis.action_success_rate)} delta="+0.3%" hint="non-denied, succeeded" />
          <Kpi label="Avg resolve" value={`${kpis.avg_resolve_seconds}s`} delta="-2s" hint="think → confirmation" />
          <Kpi label="Approvals" value={String(kpis.approvals_pending)} delta="+3" hint="pending review" />
        </div>

        <div className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Resolutions per day</div>
              <div className="flex items-center gap-2 font-mono text-[11px] text-ink-3">
                <button className="px-2 h-6 border border-line">7d</button>
                <button className="px-2 h-6 border border-ink text-ink">30d</button>
                <button className="px-2 h-6 border border-line">90d</button>
              </div>
            </div>
            <div className="p-5">
              <Sparkline values={sparkline} w={720} h={200} />
              <div className="mt-3 grid grid-cols-3 gap-px bg-line border border-line">
                <Mini label="Stripe refunds" value="$8,420" />
                <Mini label="Shopify cancellations" value="62" />
                <Mini label="Zendesk closures" value="284" />
              </div>
            </div>
          </div>

          <div className="border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Token budget</div>
              <span className="font-mono text-[11px] text-ink-3">May</span>
            </div>
            <div className="p-5">
              <div className="font-display text-[44px] leading-none tracking-tightest">
                {fmtCompact(kpis.monthly_tokens)}
              </div>
              <div className="text-[12px] text-ink-2 mt-1">
                of {fmtCompact(kpis.token_cap)} cap · {(budgetPct * 100).toFixed(1)}% used
              </div>
              <div className="mt-5 h-1.5 bg-line-2 relative">
                <div className="absolute left-0 top-0 bottom-0 bg-blue" style={{ width: `${budgetPct * 100}%` }} />
              </div>
              <ul className="mt-6 space-y-2 text-[13px]">
                <li className="flex items-center justify-between">
                  <span className="text-ink-2">Input</span>
                  <span className="font-mono">2.9M</span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-ink-2">Output</span>
                  <span className="font-mono">1.3M</span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-ink-2">Projected month-end</span>
                  <span className="font-mono text-blue">5.4M</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <div className="flex items-end justify-between mb-3">
            <h2 className="font-display text-[24px] leading-tight tracking-tightest">Latest conversations</h2>
            <a href="/conversations" className="text-[13px] text-ink-2 hover:text-blue">View all →</a>
          </div>
          <DataTable
            columns={[
              { key: "id", label: "ID", width: "100px", render: (r) => <span className="font-mono text-ink-2">{shortId(r.id, 7)}</span> },
              { key: "subject", label: "Subject" },
              { key: "end_user", label: "Customer", width: "200px", render: (r) => <span className="font-mono text-ink-2">{r.end_user}</span> },
              { key: "action", label: "Last action", width: "200px", render: (r) => <span className="font-mono text-ink-2">{r.action}</span> },
              { key: "status", label: "Status", width: "180px", render: (r) => <StatusPill status={r.status} /> },
              { key: "updated", label: "Updated", width: "120px", align: "right", render: (r) => <span className="text-ink-3">{fmtTimeAgo(r.updated)}</span> }
            ]}
            rows={conversations}
            rowHref={(r) => `/conversations/${r.id}`}
          />
        </div>
      </div>
    </>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-paper p-4">
      <div className="text-[10.5px] uppercase tracking-[0.18em] text-ink-3">{label}</div>
      <div className="mt-1.5 font-display text-[22px] leading-none tracking-tightest">{value}</div>
    </div>
  );
}
