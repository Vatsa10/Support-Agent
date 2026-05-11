import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { StatusPill } from "@/components/app/StatusPill";
import { conversations } from "@/lib/mock";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

export default function ConversationsPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Conversations" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">12,483 this month</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Conversations</h1>
          </div>
          <div className="flex items-center gap-2">
            <input
              placeholder="Filter by customer, ID, intent…"
              className="h-9 px-3 border border-line bg-paper text-[13px] w-[300px] outline-none focus:border-ink"
            />
            <button className="h-9 px-3 border border-line text-[13px] hover:border-ink">All statuses ⇣</button>
            <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Export</button>
          </div>
        </div>

        <DataTable
          columns={[
            { key: "id", label: "ID", width: "100px", render: (r) => <span className="font-mono text-ink-2">{shortId(r.id, 7)}</span> },
            { key: "subject", label: "Subject" },
            { key: "end_user", label: "Customer", width: "220px", render: (r) => <span className="font-mono text-ink-2">{r.end_user}</span> },
            { key: "action", label: "Last action", width: "200px", render: (r) => <span className="font-mono text-ink-2">{r.action}</span> },
            { key: "status", label: "Status", width: "180px", render: (r) => <StatusPill status={r.status} /> },
            { key: "updated", label: "Updated", width: "120px", align: "right", render: (r) => <span className="text-ink-3">{fmtTimeAgo(r.updated)}</span> }
          ]}
          rows={conversations}
          rowHref={(r) => `/conversations/${r.id}`}
        />
      </div>
    </>
  );
}
