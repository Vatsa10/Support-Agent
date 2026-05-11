import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { EmptyState } from "@/components/app/EmptyState";
import { StatusPill } from "@/components/app/StatusPill";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

type Conv = {
  id: string;
  thread_id: string;
  user_id: string;
  started_at: string;
  last_at: string;
  subject: string;
  last_action: string;
};

export default async function ConversationsPage() {
  const rows = (await backendFetchSafe<Conv[]>("/tenant/conversations?limit=100")) || [];
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Conversations" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{rows.length} this session</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Conversations</h1>
          </div>
        </div>

        {rows.length === 0 ? (
          <EmptyState
            title="No conversations yet."
            body="Install the widget on your site, share the hosted chat URL, or call POST /api/chat directly."
            cta={{ label: "Get install snippet", href: "/install" }}
          />
        ) : (
          <DataTable
            columns={[
              { key: "id", label: "ID", width: "120px", render: (r: any) => <span className="font-mono text-ink-2">{shortId(r.id, 8)}</span> },
              { key: "subject", label: "First message" },
              { key: "user_id", label: "Customer", width: "220px", render: (r: any) => <span className="font-mono text-ink-2">{r.user_id}</span> },
              { key: "last_action", label: "Last action", width: "200px", render: (r: any) => <span className="font-mono text-ink-2">{r.last_action || "—"}</span> },
              { key: "last_at", label: "Updated", width: "120px", align: "right", render: (r: any) => <span className="text-ink-3">{r.last_at ? fmtTimeAgo(r.last_at) : "—"}</span> }
            ]}
            rows={rows as any}
            rowHref={(r: any) => `/conversations/${r.id}`}
          />
        )}
      </div>
    </>
  );
}
