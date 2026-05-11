import { Topbar } from "@/components/app/Topbar";
import { Sparkline } from "@/components/app/Sparkline";
import { kpis, billingSeries } from "@/lib/mock";
import { fmtCompact } from "@/lib/fmt";

export default function BillingPage() {
  const pct = kpis.monthly_tokens / kpis.token_cap;
  return (
    <>
      <Topbar crumb={[{ label: "Account" }, { label: "Billing" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">May 2026 cycle</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Billing</h1>
          </div>
          <div className="flex items-center gap-2">
            <button className="h-9 px-3 border border-line text-[13px] hover:border-ink">Invoices</button>
            <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Update budget</button>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Token usage (this month)</div>
              <div className="font-mono text-[11px] text-ink-3">input + output</div>
            </div>
            <div className="p-5">
              <Sparkline values={billingSeries.map(d => d.tokens)} w={760} h={220} />
              <div className="mt-4 grid grid-cols-4 gap-px bg-line border border-line">
                <Mini label="This month" value={fmtCompact(kpis.monthly_tokens)} />
                <Mini label="Cap" value={fmtCompact(kpis.token_cap)} />
                <Mini label="Projected" value="5.4M" />
                <Mini label="Est. cost" value="$214" />
              </div>
            </div>
          </div>

          <div className="border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">Budget cap</div>
              <span className="font-mono text-[11px] text-blue">hard cap on</span>
            </div>
            <div className="p-5">
              <div className="font-display text-[40px] leading-none tracking-tightest">6.0M <span className="text-ink-2 text-[15px]">tok / mo</span></div>
              <p className="text-ink-2 text-[13px] mt-1.5">Chat returns 402 after exhaustion. Reset on the 1st.</p>
              <div className="mt-5 h-1.5 bg-line-2 relative">
                <div className="absolute left-0 top-0 bottom-0 bg-blue" style={{ width: `${pct * 100}%` }} />
                <span
                  className="absolute -top-1 -translate-x-1/2 font-mono text-[10.5px] text-ink-3"
                  style={{ left: "80%" }}
                >notify @ 80%</span>
              </div>
              <div className="mt-6 flex items-center gap-2">
                <input className="flex-1 h-9 px-2.5 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink" defaultValue="6000000" />
                <button className="h-9 px-3 border border-ink text-[13px]">Apply</button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 border border-line bg-paper">
          <div className="px-5 h-11 border-b border-line flex items-center justify-between">
            <div className="font-display text-[18px] tracking-tightest">Plan</div>
          </div>
          <div className="p-6 grid md:grid-cols-3 gap-px bg-line border-t border-line">
            <Plan label="Scale" body="$0.18 / resolution · token + per-action" current />
            <Plan label="Operator" body="Free up to 200 resolutions / mo" />
            <Plan label="Enterprise" body="VPC + SSO + BYO key — talk to us" />
          </div>
        </div>
      </div>
    </>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-paper p-4">
      <div className="text-[10.5px] uppercase tracking-[0.18em] text-ink-3">{label}</div>
      <div className="mt-1.5 font-display text-[22px] leading-none tracking-tightest">{value}</div>
    </div>
  );
}

function Plan({ label, body, current }: { label: string; body: string; current?: boolean }) {
  return (
    <div className={"bg-paper p-5 " + (current ? "ring-1 ring-inset ring-ink" : "")}>
      <div className="flex items-center justify-between">
        <span className="font-display text-[20px] tracking-tightest">{label}</span>
        {current && <span className="font-mono text-[11px] text-blue">current</span>}
      </div>
      <p className="text-ink-2 text-[13px] mt-1.5">{body}</p>
      {!current && <button className="mt-4 h-9 px-3 border border-line text-[13px] hover:border-ink">Switch</button>}
    </div>
  );
}
