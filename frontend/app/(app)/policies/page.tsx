import { Topbar } from "@/components/app/Topbar";
import { EmptyState } from "@/components/app/EmptyState";
import { backendFetchSafe } from "@/lib/api-server";

type Policy = {
  id: string;
  tool_name: string;
  allow: boolean;
  max_amount: number | null;
  currency: string | null;
  requires_approval_above: number | null;
  frequency_per_user_per_day: number | null;
  blocked_categories: string[];
};

const TOOLS = [
  "issue_refund",
  "cancel_subscription",
  "replace_order",
  "cancel_order",
  "close_zendesk_ticket",
  "comment_zendesk_ticket",
  "generic_webhook_call"
];

export default async function PoliciesPage() {
  const policies = (await backendFetchSafe<Policy[]>("/tenant/policies")) || [];
  const byTool = new Map(policies.map((p) => [p.tool_name, p]));

  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Policies" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Default-deny · explicit allow per tool</div>
          <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Policies</h1>
          <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
            Caps, approval thresholds, and frequency windows enforce before every side-effecting call.
          </p>
        </div>

        {policies.length === 0 && (
          <div className="mb-6 border border-line border-dashed bg-paper p-4 text-[13px] text-ink-2">
            No policies yet — action tools are denied until you add one.
          </div>
        )}

        <div className="border border-line bg-paper overflow-hidden">
          <div className="grid border-b border-line bg-cream" style={{ gridTemplateColumns: "260px 100px 140px 200px 140px 1fr" }}>
            {["Tool", "Allow", "Max amount", "Requires approval >", "Freq / user / day", "Blocked categories"].map((h) => (
              <div key={h} className="px-4 h-9 flex items-center text-[11px] uppercase tracking-[0.16em] text-ink-3">{h}</div>
            ))}
          </div>
          {TOOLS.map((tool) => {
            const p = byTool.get(tool);
            return (
              <div key={tool} className="grid border-b border-line last:border-b-0 items-center" style={{ gridTemplateColumns: "260px 100px 140px 200px 140px 1fr" }}>
                <div className="px-4 h-12 flex items-center font-mono text-[13px]">{tool}</div>
                <div className="px-4">
                  <span className={"font-mono text-[11.5px] " + (p?.allow ? "text-success" : "text-ink-3")}>
                    {p?.allow ? "ON" : "—"}
                  </span>
                </div>
                <div className="px-4 font-mono text-[13px]">{p?.max_amount ?? "—"}</div>
                <div className="px-4 font-mono text-[13px]">{p?.requires_approval_above ?? "—"}</div>
                <div className="px-4 font-mono text-[13px]">{p?.frequency_per_user_per_day ?? "—"}</div>
                <div className="px-4 py-2 flex flex-wrap gap-1.5">
                  {(p?.blocked_categories || []).map((c) => (
                    <span key={c} className="font-mono text-[10.5px] bg-cream border border-line px-1.5 py-0.5 text-ink-2">{c}</span>
                  ))}
                  {!p?.blocked_categories?.length && <span className="text-[12px] text-ink-3">—</span>}
                </div>
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-[12.5px] text-ink-3 font-mono">
          Edit via API: POST /tenant/policies (full inline editor coming soon).
        </p>
      </div>
    </>
  );
}
