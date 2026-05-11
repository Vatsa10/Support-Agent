import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { StatusPill } from "@/components/app/StatusPill";
import { actionRuns } from "@/lib/mock";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

export default function ActionsPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Action runs" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Every side-effect, audited</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Action runs</h1>
          </div>
          <div className="flex items-center gap-2 font-mono text-[11px] text-ink-3">
            <span className="px-2 h-6 border border-line">all tools ⇣</span>
            <span className="px-2 h-6 border border-line">all statuses ⇣</span>
          </div>
        </div>

        <DataTable
          columns={[
            { key: "id", label: "ID", width: "120px", render: (r: any) => <span className="font-mono text-ink-2">{shortId(r.id, 7)}</span> },
            { key: "tool", label: "Tool", width: "220px", render: (r: any) => <span className="font-mono">{r.tool}</span> },
            { key: "external", label: "External ID", width: "180px", render: (r: any) => r.external ? <span className="font-mono text-ink-2">{r.external}</span> : <span className="text-ink-3">—</span> },
            { key: "attempts", label: "Attempts", width: "100px", align: "right", render: (r: any) => <span className="font-mono">{r.attempts}</span> },
            { key: "status", label: "Status", width: "180px", render: (r: any) => <StatusPill status={r.status} /> },
            { key: "at", label: "Time", width: "120px", align: "right", render: (r: any) => <span className="text-ink-3">{fmtTimeAgo(r.at)}</span> }
          ]}
          rows={actionRuns as any}
        />

        <div className="mt-6 border border-line border-dashed bg-paper p-5 grid md:grid-cols-3 gap-6">
          <Hint title="Retry-safe by default" body="Every action is idempotent. Replays are free, double-charges impossible." />
          <Hint title="Webhook reconciliation" body="External vendor events update the row in place. Status reflects truth, not optimism." />
          <Hint title="Failures surface fast" body="Circuit breaker opens after consecutive 5xx and short-circuits future attempts for cooldown." />
        </div>
      </div>
    </>
  );
}

function Hint({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="font-display text-[18px] tracking-tightest">{title}</div>
      <div className="text-ink-2 text-[13px] mt-1 leading-[1.55]">{body}</div>
    </div>
  );
}
