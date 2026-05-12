"use client";
import { useState } from "react";
import { X } from "lucide-react";

type Kind = "stripe" | "shopify" | "zendesk" | "generic_webhook";

const SCHEMAS: Record<Kind, { creds: { name: string; label: string; type?: string }[]; config: { name: string; label: string; placeholder?: string }[] }> = {
  stripe: {
    creds: [
      { name: "api_key", label: "Secret API key (sk_test_… / sk_live_…)" },
      { name: "webhook_secret", label: "Webhook signing secret (whsec_…)" }
    ],
    config: []
  },
  shopify: {
    creds: [{ name: "access_token", label: "Admin API access token (shpat_…)" }],
    config: [
      { name: "shop", label: "Shop subdomain", placeholder: "acme (for acme.myshopify.com)" },
      { name: "api_version", label: "API version", placeholder: "2024-07" }
    ]
  },
  zendesk: {
    creds: [
      { name: "email", label: "Agent email" },
      { name: "api_token", label: "API token" }
    ],
    config: [{ name: "subdomain", label: "Subdomain", placeholder: "acme (for acme.zendesk.com)" }]
  },
  generic_webhook: {
    creds: [
      { name: "auth_header_value", label: "Auth header value (optional)" },
      { name: "auth_header_name", label: "Auth header name", type: "text" }
    ],
    config: [
      { name: "url", label: "Webhook URL", placeholder: "https://your.api/resolve" },
      { name: "actions", label: "Allowed actions (comma-sep)", placeholder: "issue_refund,close_ticket" }
    ]
  }
};

export function ConnectIntegrationModal({
  kind,
  onClose,
  onDone
}: {
  kind: Kind;
  onClose: () => void;
  onDone: () => void;
}) {
  const schema = SCHEMAS[kind];
  const [label, setLabel] = useState("default");
  const [creds, setCreds] = useState<Record<string, string>>({});
  const [cfg, setCfg] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const config: any = { ...cfg };
    if (config.actions) {
      config.actions = String(config.actions).split(",").map((s) => s.trim()).filter(Boolean);
    }
    if (config.api_version === "") delete config.api_version;
    const res = await fetch("/api/backend/tenant/integrations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, label, creds, config })
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setErr(d.detail || `Failed (${res.status})`);
      setBusy(false);
      return;
    }
    onDone();
  }

  return (
    <div className="fixed inset-0 z-50 bg-ink/60 backdrop-blur-sm flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-[560px] bg-paper border border-ink">
        <div className="flex items-center justify-between px-5 h-11 border-b border-line">
          <div className="font-display text-[19px] tracking-tightest">
            Connect {labelOf(kind)}
          </div>
          <button type="button" onClick={onClose} className="text-ink-2 hover:text-ink"><X size={16} /></button>
        </div>
        <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
          <Field label="Label" value={label} onChange={setLabel} placeholder="default" />

          {schema.config.length > 0 && (
            <>
              <Section title="Configuration" />
              {schema.config.map((f) => (
                <Field
                  key={f.name}
                  label={f.label}
                  placeholder={f.placeholder}
                  value={cfg[f.name] || ""}
                  onChange={(v) => setCfg((c) => ({ ...c, [f.name]: v }))}
                />
              ))}
            </>
          )}

          <Section title="Credentials (encrypted at rest)" />
          {schema.creds.map((f) => (
            <Field
              key={f.name}
              label={f.label}
              type={f.type || "password"}
              value={creds[f.name] || ""}
              onChange={(v) => setCreds((c) => ({ ...c, [f.name]: v }))}
            />
          ))}

          {err && <div className="text-[13px] text-danger">{err}</div>}
        </div>
        <div className="px-5 h-12 border-t border-line flex items-center justify-end gap-2">
          <button type="button" onClick={onClose} className="h-9 px-3 border border-line text-[13px]">Cancel</button>
          <button type="submit" disabled={busy} className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue disabled:opacity-50">
            {busy ? "Connecting…" : "Connect"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Section({ title }: { title: string }) {
  return <div className="text-[10.5px] uppercase tracking-[0.18em] text-ink-3 pt-2">{title}</div>;
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full h-10 px-3 border border-line bg-paper text-[13.5px] outline-none focus:border-ink font-mono"
      />
    </label>
  );
}

function labelOf(k: Kind) {
  return { stripe: "Stripe", shopify: "Shopify", zendesk: "Zendesk", generic_webhook: "Webhook" }[k];
}
