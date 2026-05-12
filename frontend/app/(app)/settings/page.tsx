"use client";
import { useEffect, useState } from "react";
import { Topbar } from "@/components/app/Topbar";

const DEFAULT = `You are Resolve operating as the customer support agent for {COMPANY}.

Tone: warm, precise, never apologetic without reason. Use the customer's name once.
Always confirm any side-effect ("I've issued the refund for $X") and propose the next useful step.
For sensitive categories (fraud, dispute) — escalate rather than act.`;

export default function SettingsPage() {
  const [prompt, setPrompt] = useState("");
  const [topK, setTopK] = useState(5);
  const [conf, setConf] = useState(0.7);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/backend/tenant/settings", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)),
      fetch("/api/auth/me", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null))
    ]).then(([s, u]) => {
      if (s) {
        setPrompt(s.system_prompt_override || "");
        setTopK(s.top_k ?? 5);
        setConf(s.confidence_threshold ?? 0.7);
      }
      setMe(u);
      setLoading(false);
    });
  }, []);

  async function save() {
    setSaving(true);
    setMsg(null);
    const res = await fetch("/api/backend/tenant/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_prompt_override: prompt || null,
        top_k: topK,
        confidence_threshold: conf
      })
    });
    setSaving(false);
    setMsg(res.ok ? "Saved." : "Save failed.");
    setTimeout(() => setMsg(null), 2500);
  }

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
              <span className="font-mono text-[11px] text-ink-3">empty → use default</span>
            </div>
            <div className="p-5">
              {loading ? (
                <div className="text-[13px] text-ink-3">loading…</div>
              ) : (
                <>
                  <textarea
                    rows={16}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={DEFAULT}
                    className="w-full p-4 border border-line bg-paper text-[13.5px] font-mono leading-[1.55] outline-none focus:border-ink"
                  />
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <Field label="Retrieval top_k" value={String(topK)} onChange={(v) => setTopK(parseInt(v, 10) || 5)} />
                    <Field label="Confidence threshold" value={String(conf)} onChange={(v) => setConf(parseFloat(v) || 0.7)} />
                  </div>
                  <div className="mt-4 flex items-center justify-end gap-3">
                    {msg && <span className="text-[12px] text-ink-2">{msg}</span>}
                    <button onClick={() => setPrompt("")} className="h-9 px-3 border border-line text-[13px]">Clear</button>
                    <button
                      onClick={save}
                      disabled={saving}
                      className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue disabled:opacity-50"
                    >
                      {saving ? "Saving…" : "Save"}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <Card title="Workspace">
              <Row k="Name" v={me?.tenant_name || "—"} />
              <Row k="ID" v={me?.tenant_id || "—"} mono />
              <Row k="Plan" v={me?.plan || "free"} />
              <Row k="Status" v={me?.status || "—"} />
            </Card>
            <Card title="You">
              <Row k="Name" v={me?.user?.name || "—"} />
              <Row k="Email" v={me?.user?.email || "—"} mono />
              <Row k="Role" v={me?.user?.role || "—"} />
            </Card>
            <Card title="Danger zone">
              <button className="w-full h-9 border border-line text-danger text-[13px] hover:border-danger transition">
                Suspend workspace
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
      <span className="text-ink-2 shrink-0">{k}</span>
      <span className={(mono ? "font-mono " : "") + "truncate text-right"}>{v}</span>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        type="number"
        step="0.01"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-10 px-3 border border-line bg-paper text-[13.5px] font-mono outline-none focus:border-ink"
      />
    </label>
  );
}
