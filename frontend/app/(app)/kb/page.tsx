"use client";
import { useEffect, useState } from "react";
import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { EmptyState } from "@/components/app/EmptyState";
import { Upload, X } from "lucide-react";

type Source = { source: string; chunks: number };

export default function KbPage() {
  const [rows, setRows] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  async function refresh() {
    setLoading(true);
    const res = await fetch("/api/backend/tenant/kb/sources", { cache: "no-store" });
    if (res.ok) setRows(await res.json());
    setLoading(false);
  }
  useEffect(() => { refresh(); }, []);

  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Knowledge" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">
              {loading ? "loading…" : `${rows.length} sources · ${rows.reduce((s, r) => s + r.chunks, 0)} chunks indexed`}
            </div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Knowledge base</h1>
            <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
              Grounding for every answer. Chunked, embedded with Gemini, retrieved with hybrid pgvector + tsvector.
            </p>
          </div>
          <button
            onClick={() => setOpen(true)}
            className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5"
          >
            <Upload size={14} /> Upload source
          </button>
        </div>

        {!loading && rows.length === 0 ? (
          <EmptyState
            title="No sources yet."
            body="Upload your help center, FAQs, or any markdown. Resolve chunks and embeds in seconds."
            cta={{ label: "Upload source", onClick: () => setOpen(true) }}
          />
        ) : (
          <DataTable
            columns={[
              { key: "source", label: "Source", render: (r: any) => <span className="font-mono">{r.source}</span> },
              { key: "chunks", label: "Chunks", width: "120px", align: "right", render: (r: any) => <span className="font-mono">{r.chunks}</span> },
              {
                key: "actions",
                label: "",
                width: "120px",
                align: "right",
                render: (r: any) => (
                  <button
                    onClick={async (e) => {
                      e.preventDefault();
                      if (!confirm(`Delete all chunks for "${r.source}"?`)) return;
                      const res = await fetch(`/api/backend/tenant/kb/sources/${encodeURIComponent(r.source)}`, { method: "DELETE" });
                      if (res.ok) refresh();
                    }}
                    className="text-[12px] text-ink-2 hover:text-danger"
                  >
                    Delete
                  </button>
                )
              }
            ]}
            rows={rows.map((r) => ({ id: r.source, ...r })) as any}
          />
        )}
      </div>

      {open && <UploadModal onClose={() => setOpen(false)} onDone={() => { setOpen(false); refresh(); }} />}
    </>
  );
}

function UploadModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const fd = new FormData(e.currentTarget);
    const res = await fetch("/api/backend/tenant/kb/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: fd.get("source"),
        text: fd.get("text"),
        replace: fd.get("replace") === "on"
      })
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setErr(d.detail || `Upload failed (${res.status})`);
      setBusy(false);
      return;
    }
    onDone();
  }

  return (
    <div className="fixed inset-0 z-50 bg-ink/60 backdrop-blur-sm flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-[560px] bg-paper border border-ink">
        <div className="flex items-center justify-between px-5 h-11 border-b border-line">
          <div className="font-display text-[19px] tracking-tightest">Upload source</div>
          <button type="button" onClick={onClose} className="text-ink-2 hover:text-ink"><X size={16} /></button>
        </div>
        <div className="p-5 space-y-4">
          <label className="block">
            <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Source name</span>
            <input name="source" required placeholder="returns-policy.md" className="w-full h-10 px-3 border border-line bg-paper text-[13.5px] outline-none focus:border-ink" />
          </label>
          <label className="block">
            <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Text content</span>
            <textarea name="text" required rows={10} placeholder="Paste markdown / plain text. Chunked at 800 / 200 overlap." className="w-full p-3 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink" />
          </label>
          <label className="inline-flex items-center gap-2 text-[12.5px] text-ink-2">
            <input type="checkbox" name="replace" defaultChecked className="accent-blue h-3.5 w-3.5" />
            Replace existing chunks for this source
          </label>
          {err && <div className="text-[13px] text-danger">{err}</div>}
        </div>
        <div className="px-5 h-12 border-t border-line flex items-center justify-end gap-2">
          <button type="button" onClick={onClose} className="h-9 px-3 border border-line text-[13px]">Cancel</button>
          <button type="submit" disabled={busy} className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue disabled:opacity-50">
            {busy ? "Uploading…" : "Upload + index"}
          </button>
        </div>
      </form>
    </div>
  );
}
