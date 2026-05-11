"use client";
import { useState } from "react";
import { Topbar } from "@/components/app/Topbar";
import { DataTable } from "@/components/app/DataTable";
import { EmptyState } from "@/components/app/EmptyState";
import { kbSources } from "@/lib/mock";
import { fmtTimeAgo } from "@/lib/fmt";
import { Upload, X } from "lucide-react";

export default function KbPage() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Knowledge" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{kbSources.length} sources · 150 chunks indexed</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Knowledge base</h1>
            <p className="text-ink-2 text-[14px] mt-2 max-w-xl">
              The grounding for every answer. Chunked, embedded with Gemini, and retrieved with hybrid pgvector + BM25.
            </p>
          </div>
          <button
            onClick={() => setOpen(true)}
            className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5"
          >
            <Upload size={14} /> Upload source
          </button>
        </div>

        {kbSources.length ? (
          <DataTable
            columns={[
              { key: "source", label: "Source", render: (r: any) => <span className="font-mono">{r.source}</span> },
              { key: "chunks", label: "Chunks", width: "120px", align: "right", render: (r: any) => <span className="font-mono">{r.chunks}</span> },
              { key: "updated", label: "Last updated", width: "180px", align: "right", render: (r: any) => <span className="text-ink-3">{fmtTimeAgo(r.updated)}</span> }
            ]}
            rows={kbSources as any}
          />
        ) : (
          <EmptyState
            title="No sources yet."
            body="Upload your help center, FAQs, or any markdown. Resolve will chunk and embed in seconds."
            cta={{ label: "Upload source", onClick: () => setOpen(true) }}
          />
        )}
      </div>

      {open && (
        <div className="fixed inset-0 z-50 bg-ink/60 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="w-full max-w-[560px] bg-paper border border-ink">
            <div className="flex items-center justify-between px-5 h-11 border-b border-line">
              <div className="font-display text-[19px] tracking-tightest">Upload source</div>
              <button onClick={() => setOpen(false)} className="text-ink-2 hover:text-ink"><X size={16} /></button>
            </div>
            <div className="p-5 space-y-4">
              <Field label="Source name" placeholder="returns-policy.md" />
              <label className="block">
                <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Text content</span>
                <textarea
                  rows={8}
                  placeholder="Paste markdown / plain text. We chunk at 800 / 200 overlap."
                  className="w-full p-3 border border-line bg-paper text-[13px] font-mono outline-none focus:border-ink"
                />
              </label>
              <label className="inline-flex items-center gap-2 text-[12.5px] text-ink-2">
                <input type="checkbox" defaultChecked className="accent-blue h-3.5 w-3.5" />
                Replace existing chunks for this source
              </label>
            </div>
            <div className="px-5 h-12 border-t border-line flex items-center justify-end gap-2">
              <button onClick={() => setOpen(false)} className="h-9 px-3 border border-line text-[13px]">Cancel</button>
              <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Upload + index</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Field({ label, ...rest }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input {...rest} className="w-full h-10 px-3 border border-line bg-paper text-[13.5px] outline-none focus:border-ink" />
    </label>
  );
}
