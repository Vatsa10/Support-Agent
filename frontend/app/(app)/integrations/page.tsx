import { Topbar } from "@/components/app/Topbar";
import { EmptyState } from "@/components/app/EmptyState";
import { StatusPill } from "@/components/app/StatusPill";
import { backendFetchSafe } from "@/lib/api-server";
import { Plug, Plus } from "lucide-react";

type Integration = { id: string; kind: string; label: string; enabled: boolean; config: any };

const known: Record<string, { name: string; blurb: string; glyph: string }> = {
  stripe:           { name: "Stripe",          blurb: "Refunds + subscription cancellation",         glyph: "S" },
  shopify:          { name: "Shopify",         blurb: "Replacement + order cancellation",            glyph: "Sh" },
  zendesk:          { name: "Zendesk",         blurb: "Ticket close + public comment",               glyph: "Z" },
  generic_webhook:  { name: "Generic webhook", blurb: "Any backend over signed HTTP POST",           glyph: "W" }
};

export default async function IntegrationsPage() {
  const installed = (await backendFetchSafe<Integration[]>("/tenant/integrations")) || [];
  const byKind = new Map(installed.map((i) => [i.kind, i]));

  const cards = Object.entries(known).map(([kind, meta]) => ({
    kind,
    meta,
    inst: byKind.get(kind)
  }));

  const connectedCount = installed.length;

  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Integrations" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">
              {connectedCount} connected · {cards.length - connectedCount} available
            </div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Integrations</h1>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-px bg-line border border-line">
          {cards.map(({ kind, meta, inst }) => (
            <div key={kind} className="bg-paper p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 border border-line flex items-center justify-center font-display text-[22px] text-ink">{meta.glyph}</div>
                  <div>
                    <div className="font-display text-[24px] leading-tight tracking-tightest">{meta.name}</div>
                    <div className="text-ink-2 text-[13px] mt-1">{meta.blurb}</div>
                    {inst && <div className="mt-2 font-mono text-[11.5px] text-ink-3">label: {inst.label}</div>}
                  </div>
                </div>
                <StatusPill status={inst ? (inst.enabled ? "healthy" : "disconnected") : "disconnected"} />
              </div>

              <div className="mt-6 flex items-center gap-2">
                {inst ? (
                  <>
                    <span className="font-mono text-[11px] text-ink-3 mr-auto">id {inst.id.slice(0, 8)}…</span>
                    <button className="h-9 px-3 border border-line text-[13px] hover:border-ink">Configure</button>
                    <button className="h-9 px-3 border border-line text-[13px] text-ink-2 hover:border-danger hover:text-danger">Disconnect</button>
                  </>
                ) : (
                  <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5">
                    <Plug size={13} /> Connect
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
