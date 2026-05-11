import { Topbar } from "@/components/app/Topbar";
import { EmptyState } from "@/components/app/EmptyState";
import { StatusPill } from "@/components/app/StatusPill";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

type Approval = {
  id: string;
  action_run_id: string;
  status: string;
  reason: string;
  created_at: string;
  tool_name: string;
  args: any;
};

export default async function ApprovalsPage() {
  const rows = (await backendFetchSafe<Approval[]>("/tenant/approvals?limit=50")) || [];
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Approvals" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Human-in-the-loop · {rows.length} pending</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Approvals queue</h1>
            <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
              Actions over policy threshold pause here. Approving re-runs with the original arguments — idempotent.
            </p>
          </div>
        </div>

        {rows.length === 0 ? (
          <EmptyState
            title="Queue is clear."
            body="When an action exceeds your policy's approval threshold, it'll pause here for review."
            cta={{ label: "Configure policies", href: "/policies" }}
          />
        ) : (
          <div className="space-y-4">
            {rows.map((a) => (
              <div key={a.id} className="border border-line bg-paper">
                <div className="px-5 h-10 border-b border-line flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[11px] text-ink-3">{shortId(a.id, 8)}</span>
                    <StatusPill status="pending_approval" />
                  </div>
                  <span className="text-[12px] text-ink-3">{fmtTimeAgo(a.created_at)}</span>
                </div>
                <div className="grid md:grid-cols-12 gap-px bg-line">
                  <div className="md:col-span-8 bg-paper p-5">
                    <div className="font-display text-[22px] tracking-tightest leading-tight">{a.tool_name.replace(/_/g, " ")}</div>
                    <p className="mt-2 text-ink-2 text-[13.5px]">{a.reason}</p>
                    <pre className="mt-4 font-mono text-[12.5px] bg-cream border border-line p-3 overflow-auto">
{JSON.stringify(a.args, null, 2)}
                    </pre>
                  </div>
                  <div className="md:col-span-4 bg-cream p-5 flex flex-col justify-between">
                    <ul className="text-[13px] space-y-2">
                      <li className="flex justify-between"><span className="text-ink-2">Tool</span><span className="font-mono">{a.tool_name}</span></li>
                      <li className="flex justify-between"><span className="text-ink-2">Run</span><span className="font-mono">{shortId(a.action_run_id, 6)}</span></li>
                    </ul>
                    <div className="mt-5 grid grid-cols-2 gap-2">
                      <form action={`/api/backend/tenant/approvals/${a.id}/decision`} method="post">
                        <button className="w-full h-10 bg-ink text-paper text-[13px] hover:bg-blue transition">Approve</button>
                      </form>
                      <form action={`/api/backend/tenant/approvals/${a.id}/decision`} method="post">
                        <button className="w-full h-10 border border-line bg-paper text-ink text-[13px] hover:border-danger hover:text-danger transition">Reject</button>
                      </form>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
