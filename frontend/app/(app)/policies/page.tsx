"use client";
import { useEffect, useState } from "react";
import { Topbar } from "@/components/app/Topbar";

type Policy = {
  id?: string;
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

function emptyFor(tool: string): Policy {
  return {
    tool_name: tool,
    allow: false,
    max_amount: null,
    currency: null,
    requires_approval_above: null,
    frequency_per_user_per_day: null,
    blocked_categories: []
  };
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Record<string, Policy>>({});
  const [dirty, setDirty] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const r = await fetch("/api/backend/tenant/policies", { cache: "no-store" });
    const data = r.ok ? await r.json() : [];
    const map: Record<string, Policy> = {};
    for (const t of TOOLS) map[t] = emptyFor(t);
    for (const p of data as Policy[]) map[p.tool_name] = { ...emptyFor(p.tool_name), ...p };
    setPolicies(map);
    setDirty({});
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  function patch(tool: string, fn: (p: Policy) => Policy) {
    setPolicies((cur) => ({ ...cur, [tool]: fn(cur[tool]) }));
    setDirty((d) => ({ ...d, [tool]: true }));
  }

  async function save(tool: string) {
    setSaving(tool);
    const p = policies[tool];
    const res = await fetch("/api/backend/tenant/policies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool_name: p.tool_name,
        allow: p.allow,
        max_amount: p.max_amount,
        currency: p.currency || null,
        requires_approval_above: p.requires_approval_above,
        frequency_per_user_per_day: p.frequency_per_user_per_day,
        blocked_categories: p.blocked_categories,
        extra: {}
      })
    });
    setSaving(null);
    if (res.ok) setDirty((d) => ({ ...d, [tool]: false }));
  }

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

        <div className="border border-line bg-paper overflow-hidden">
          <div className="grid border-b border-line bg-cream" style={{ gridTemplateColumns: "260px 100px 140px 200px 140px 1fr 110px" }}>
            {["Tool", "Allow", "Max amount", "Requires approval >", "Freq / user / day", "Blocked categories", ""].map((h) => (
              <div key={h} className="px-4 h-9 flex items-center text-[11px] uppercase tracking-[0.16em] text-ink-3">{h}</div>
            ))}
          </div>
          {loading ? (
            <div className="px-4 py-6 text-[13px] text-ink-3">loading…</div>
          ) : (
            TOOLS.map((tool) => {
              const p = policies[tool];
              const isDirty = !!dirty[tool];
              return (
                <div key={tool} className="grid border-b border-line last:border-b-0 items-center" style={{ gridTemplateColumns: "260px 100px 140px 200px 140px 1fr 110px" }}>
                  <div className="px-4 h-14 flex items-center font-mono text-[13px]">{tool}</div>
                  <div className="px-4">
                    <Switch
                      checked={p.allow}
                      onChange={(v) => patch(tool, (x) => ({ ...x, allow: v }))}
                    />
                  </div>
                  <div className="px-4">
                    <NumInput
                      value={p.max_amount}
                      onChange={(v) => patch(tool, (x) => ({ ...x, max_amount: v }))}
                      placeholder="∞"
                    />
                  </div>
                  <div className="px-4">
                    <NumInput
                      value={p.requires_approval_above}
                      onChange={(v) => patch(tool, (x) => ({ ...x, requires_approval_above: v }))}
                      placeholder="none"
                    />
                  </div>
                  <div className="px-4">
                    <NumInput
                      value={p.frequency_per_user_per_day}
                      onChange={(v) => patch(tool, (x) => ({ ...x, frequency_per_user_per_day: v }))}
                      placeholder="—"
                      integer
                    />
                  </div>
                  <div className="px-4">
                    <input
                      type="text"
                      value={(p.blocked_categories || []).join(", ")}
                      onChange={(e) => patch(tool, (x) => ({ ...x, blocked_categories: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                      placeholder="fraud, chargeback"
                      className="w-full h-9 px-2.5 border border-line bg-paper text-[12.5px] font-mono outline-none focus:border-ink"
                    />
                  </div>
                  <div className="px-4">
                    <button
                      onClick={() => save(tool)}
                      disabled={!isDirty || saving === tool}
                      className="h-9 px-3 bg-ink text-paper text-[12.5px] hover:bg-blue disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      {saving === tool ? "…" : isDirty ? "Save" : "Saved"}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}

function Switch({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={"relative inline-flex h-5 w-9 items-center border transition " + (checked ? "bg-ink border-ink" : "bg-paper border-line")}
    >
      <span className={"inline-block w-3 h-3 transition-all " + (checked ? "translate-x-5 bg-blue" : "translate-x-1 bg-ink-3")} />
    </button>
  );
}

function NumInput({
  value,
  onChange,
  placeholder,
  integer
}: {
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder?: string;
  integer?: boolean;
}) {
  return (
    <input
      type="number"
      step={integer ? 1 : 0.01}
      value={value ?? ""}
      onChange={(e) => {
        const raw = e.target.value;
        if (raw === "") onChange(null);
        else onChange(integer ? parseInt(raw, 10) : parseFloat(raw));
      }}
      placeholder={placeholder}
      className="w-full h-9 px-2.5 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink"
    />
  );
}
