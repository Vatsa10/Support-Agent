import { Topbar } from "@/components/app/Topbar";

export default function SettingsPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Settings" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Workspace voice + behavior</div>
          <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Settings</h1>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 border border-line bg-paper">
            <div className="px-5 h-11 border-b border-line flex items-center justify-between">
              <div className="font-display text-[18px] tracking-tightest">System prompt override</div>
              <span className="font-mono text-[11px] text-ink-3">default uses prompt.md</span>
            </div>
            <div className="p-5">
              <textarea
                rows={16}
                defaultValue={`You are Resolve operating as the customer support agent for Acme Goods.

Tone: warm, precise, never apologetic without reason. Use the customer's name once.
Always confirm any side-effect ("I've issued the refund for $X") and propose the next useful step.
For sensitive categories (fraud, dispute) — escalate rather than act.`}
                className="w-full p-4 border border-line bg-paper text-[13.5px] font-mono leading-[1.55] outline-none focus:border-ink"
              />
              <div className="mt-4 flex items-center justify-end gap-2">
                <button className="h-9 px-3 border border-line text-[13px]">Discard</button>
                <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Save override</button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <Card title="Workspace">
              <Row k="Name" v="Acme Goods" />
              <Row k="ID" v="org_2pq…" mono />
              <Row k="Created" v="Feb 1, 2026" />
              <Row k="Plan" v="Scale" />
            </Card>
            <Card title="Branding">
              <Row k="Display name" v="Resolve for Acme" />
              <Row k="Accent color" v="#1B4DFF" mono />
            </Card>
            <Card title="Danger zone">
              <button className="w-full h-9 border border-line text-danger text-[13px] hover:border-danger transition">
                Suspend workspace
              </button>
              <button className="w-full mt-2 h-9 border border-danger text-danger text-[13px] hover:bg-danger hover:text-paper transition">
                Delete workspace
              </button>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-line bg-paper">
      <div className="px-4 h-9 border-b border-line flex items-center text-[11px] uppercase tracking-[0.18em] text-ink-3">{title}</div>
      <div className="p-4 space-y-2.5">{children}</div>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 text-[13px]">
      <span className="text-ink-2">{k}</span>
      <span className={mono ? "font-mono" : ""}>{v}</span>
    </div>
  );
}
