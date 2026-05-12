"use client";
import { useEffect, useState } from "react";
import { Topbar } from "@/components/app/Topbar";
import { StatusPill } from "@/components/app/StatusPill";
import { ConnectIntegrationModal } from "@/components/app/ConnectIntegrationModal";
import { Plug } from "lucide-react";

type Integration = { id: string; kind: string; label: string; enabled: boolean; config: any };

const known = {
  stripe:           { name: "Stripe",          blurb: "Refunds + subscription cancellation",  glyph: "S" },
  shopify:          { name: "Shopify",         blurb: "Replacement + order cancellation",     glyph: "Sh" },
  zendesk:          { name: "Zendesk",         blurb: "Ticket close + public comment",        glyph: "Z" },
  generic_webhook:  { name: "Generic webhook", blurb: "Any backend over signed HTTP POST",    glyph: "W" }
} as const;

type Kind = keyof typeof known;

export default function IntegrationsPage() {
  const [rows, setRows] = useState<Integration[]>([]);
  const [open, setOpen] = useState<Kind | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const r = await fetch("/api/backend/tenant/integrations", { cache: "no-store" });
    if (r.ok) setRows(await r.json());
    setLoading(false);
  }
  useEffect(() => { refresh(); }, []);

  async function disconnect(id: string) {
    if (!confirm("Disconnect this integration? Tools provided by it will stop working immediately.")) return;
    await fetch(`/api/backend/tenant/integrations/${id}`, { method: "DELETE" });
    refresh();
  }

  const byKind = new Map(rows.map((i) => [i.kind, i]));
  const connected = rows.length;

  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Integrations" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">
              {loading ? "loading…" : `${connected} connected · ${Object.keys(known).length - connected} available`}
            </div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Integrations</h1>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-px bg-line border border-line">
          {(Object.entries(known) as [Kind, typeof known[Kind]][]).map(([kind, meta]) => {
            const inst = byKind.get(kind);
            return (
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
                      <button
                        onClick={() => setOpen(kind)}
                        className="h-9 px-3 border border-line text-[13px] hover:border-ink"
                      >Reconfigure</button>
                      <button
                        onClick={() => disconnect(inst.id)}
                        className="h-9 px-3 border border-line text-[13px] text-ink-2 hover:border-danger hover:text-danger"
                      >Disconnect</button>
                    </>
                  ) : (
                    <button
                      onClick={() => setOpen(kind)}
                      className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5"
                    >
                      <Plug size={13} /> Connect
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {open && (
        <ConnectIntegrationModal
          kind={open}
          onClose={() => setOpen(null)}
          onDone={() => { setOpen(null); refresh(); }}
        />
      )}
    </>
  );
}
