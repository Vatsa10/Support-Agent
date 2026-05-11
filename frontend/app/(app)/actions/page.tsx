import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { EmptyState } from "@/components/app/EmptyState";
import { StatusPill } from "@/components/app/StatusPill";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

type Run = {
  id: string;
  tool_name: string;
  status: string;
  external_id: string | null;
  error: string | null;
  at: string;
};

export default async function ActionsPage() {
  const rows = (await backendFetchSafe<Run[]>("/tenant/actions?limit=100")) || [];
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Action runs" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Every side-effect, audited</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Action runs</h1>
          </div>
        </div>

        {rows.length === 0 ? (
          <EmptyState
            title="No actions yet."
            body="Once you connect Stripe / Shopify / Zendesk and the operator runs a refund or close, attempts show here."
            cta={{ label: "Connect an integration", href: "/integrations" }}
          />
        ) : (
          <DataTable
            columns={[
              { key: "id", label: "ID", width: "120px", render: (r: any) => <span className="font-mono text-ink-2">{shortId(r.id, 8)}</span> },
              { key: "tool_name", label: "Tool", width: "240px", render: (r: any) => <span className="font-mono">{r.tool_name}</span> },
              { key: "external_id", label: "External ID", width: "200px", render: (r: any) => r.external_id ? <span className="font-mono text-ink-2">{r.external_id}</span> : <span className="text-ink-3">—</span> },
              { key: "error", label: "Error", render: (r: any) => r.error ? <span className="text-danger text-[12.5px]">{r.error}</span> : <span className="text-ink-3">—</span> },
              { key: "status", label: "Status", width: "180px", render: (r: any) => <StatusPill status={r.status} /> },
              { key: "at", label: "Time", width: "120px", align: "right", render: (r: any) => <span className="text-ink-3">{fmtTimeAgo(r.at)}</span> }
            ]}
            rows={rows as any}
          />
        )}
      </div>
    </>
  );
}
