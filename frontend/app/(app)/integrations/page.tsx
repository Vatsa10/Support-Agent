import { Topbar } from "@/components/app/Topbar";
import { StatusPill } from "@/components/app/StatusPill";
import { integrations } from "@/lib/mock";
import { Plug, Plus } from "lucide-react";

const known = {
  stripe:           { name: "Stripe",          blurb: "Refunds + subscription cancellation",         glyph: "S" },
  shopify:          { name: "Shopify",         blurb: "Replacement + order cancellation",            glyph: "Sh" },
  zendesk:          { name: "Zendesk",         blurb: "Ticket close + public comment",               glyph: "Z" },
  generic_webhook:  { name: "Generic webhook", blurb: "Any backend over signed HTTP POST",           glyph: "W" }
} as const;

export default function IntegrationsPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Integrations" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{integrations.filter(i=>i.connected).length} connected · {integrations.length - integrations.filter(i=>i.connected).length} available</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Integrations</h1>
          </div>
          <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5">
            <Plus size={14} /> Add integration
          </button>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-px bg-line border border-line">
          {integrations.map((i) => {
            const k = known[i.kind as keyof typeof known];
            return (
              <div key={i.kind} className="bg-paper p-6 group">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 border border-line flex items-center justify-center font-display text-[22px] text-ink">{k.glyph}</div>
                    <div>
                      <div className="font-display text-[24px] leading-tight tracking-tightest">{k.name}</div>
                      <div className="text-ink-2 text-[13px] mt-1">{k.blurb}</div>
                      {i.connected && (
                        <div className="mt-2 font-mono text-[11.5px] text-ink-3">label: {i.label}</div>
                      )}
                    </div>
                  </div>
                  <StatusPill status={i.status} />
                </div>

                <div className="mt-6 grid grid-cols-3 gap-px bg-line border border-line">
                  <Stat label="Tools" value={k.glyph === "S" ? "2" : k.glyph === "Sh" ? "2" : k.glyph === "Z" ? "2" : "1"} />
                  <Stat label="Calls 24h" value={String(i.usage_24h)} />
                  <Stat label="Breaker" value={i.status === "degraded" ? "open" : "closed"} />
                </div>

                <div className="mt-4 flex items-center gap-2">
                  {i.connected ? (
                    <>
                      <button className="h-9 px-3 border border-line text-[13px] hover:border-ink">Configure</button>
                      <button className="h-9 px-3 border border-line text-[13px] hover:border-ink">Rotate keys</button>
                      <button className="h-9 px-3 border border-line text-[13px] text-ink-2 hover:border-danger hover:text-danger ml-auto">Disconnect</button>
                    </>
                  ) : (
                    <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5">
                      <Plug size={13} /> Connect
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-paper px-4 py-3">
      <div className="text-[10.5px] uppercase tracking-[0.18em] text-ink-3">{label}</div>
      <div className="mt-1 font-mono text-[14px]">{value}</div>
    </div>
  );
}
