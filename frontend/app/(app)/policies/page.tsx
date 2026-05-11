import { Topbar } from "@/components/app/Topbar";
import { policies } from "@/lib/mock";

export default function PoliciesPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Policies" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{policies.length} tools governed</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Policies</h1>
            <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
              The operator can only do what you say it can. Caps, approval thresholds, and frequency windows enforce
              before every side-effecting call.
            </p>
          </div>
          <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Save changes</button>
        </div>

        <div className="border border-line bg-paper overflow-hidden">
          <div className="grid border-b border-line bg-cream" style={{ gridTemplateColumns: "240px 100px 140px 200px 140px 1fr" }}>
            {["Tool","Allow","Max amount","Requires approval above","Freq / user / day","Categories blocked"].map(h => (
              <div key={h} className="px-4 h-9 flex items-center text-[11px] uppercase tracking-[0.16em] text-ink-3">{h}</div>
            ))}
          </div>
          {policies.map((p) => (
            <div key={p.tool} className="grid border-b border-line last:border-b-0 items-center" style={{ gridTemplateColumns: "240px 100px 140px 200px 140px 1fr" }}>
              <div className="px-4 h-14 flex items-center font-mono text-[13px]">{p.tool}</div>
              <div className="px-4">
                <Switch checked={p.allow} />
              </div>
              <div className="px-4">
                <input
                  defaultValue={p.max_amount ?? ""}
                  placeholder="∞"
                  className="w-full h-9 px-2.5 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink"
                />
              </div>
              <div className="px-4">
                <input
                  defaultValue={p.requires_approval_above ?? ""}
                  placeholder="none"
                  className="w-full h-9 px-2.5 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink"
                />
              </div>
              <div className="px-4">
                <input
                  defaultValue={p.frequency}
                  className="w-full h-9 px-2.5 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink"
                />
              </div>
              <div className="px-4 py-2 flex flex-wrap gap-1.5">
                {["fraud","chargeback"].map(c => (
                  <span key={c} className="font-mono text-[10.5px] bg-cream border border-line px-1.5 py-0.5 text-ink-2">
                    {c} ×
                  </span>
                ))}
                <button className="font-mono text-[10.5px] text-ink-2 hover:text-blue">+ add</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function Switch({ checked }: { checked: boolean }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      className={
        "relative inline-flex h-5 w-9 items-center border transition " +
        (checked ? "bg-ink border-ink" : "bg-paper border-line")
      }
    >
      <span
        className={
          "inline-block w-3 h-3 transition-all " +
          (checked ? "translate-x-5 bg-blue" : "translate-x-1 bg-ink-3")
        }
      />
    </button>
  );
}
