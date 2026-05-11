import { Topbar } from "@/components/app/Topbar";
import { StatusPill } from "@/components/app/StatusPill";
import { approvals } from "@/lib/mock";
import { fmtTimeAgo, shortId } from "@/lib/fmt";
import { Check, X } from "lucide-react";

export default function ApprovalsPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Approvals" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Human-in-the-loop · {approvals.length} pending</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Approvals queue</h1>
            <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
              Actions over your policy threshold pause here. Approve to re-run with the original arguments — Resolve handles
              idempotency.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {approvals.map((a) => (
            <div key={a.id} className="border border-line bg-paper">
              <div className="px-5 h-10 border-b border-line flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[11px] text-ink-3">{shortId(a.id, 7)}</span>
                  <StatusPill status="pending_approval" />
                </div>
                <span className="text-[12px] text-ink-3">{fmtTimeAgo(a.created_at)} · times out in 22h</span>
              </div>
              <div className="grid md:grid-cols-12 gap-px bg-line">
                <div className="md:col-span-8 bg-paper p-5">
                  <div className="font-display text-[24px] tracking-tightest leading-tight">
                    {humanize(a.tool)} for <span className="font-mono text-ink-2 text-[16px]">{a.end_user}</span>
                  </div>
                  <p className="mt-2 text-ink-2 text-[13.5px]">{a.reason}</p>
                  <pre className="mt-4 font-mono text-[12.5px] bg-cream border border-line p-3 overflow-auto">
{JSON.stringify(a.args, null, 2)}
                  </pre>
                </div>
                <div className="md:col-span-4 bg-cream p-5 flex flex-col justify-between">
                  <ul className="text-[13px] space-y-2">
                    <li className="flex justify-between"><span className="text-ink-2">Tool</span><span className="font-mono">{a.tool}</span></li>
                    <li className="flex justify-between"><span className="text-ink-2">Run</span><span className="font-mono">{shortId(a.run_id, 6)}</span></li>
                    <li className="flex justify-between"><span className="text-ink-2">Auto-reject in</span><span className="font-mono">22h 04m</span></li>
                  </ul>
                  <div className="mt-5 grid grid-cols-2 gap-2">
                    <button className="h-10 inline-flex items-center justify-center gap-1.5 bg-ink text-paper text-[13px] hover:bg-blue transition">
                      <Check size={14} /> Approve
                    </button>
                    <button className="h-10 inline-flex items-center justify-center gap-1.5 border border-line bg-paper text-ink text-[13px] hover:border-danger hover:text-danger transition">
                      <X size={14} /> Reject
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function humanize(tool: string) {
  return tool.replace(/_/g, " ");
}
