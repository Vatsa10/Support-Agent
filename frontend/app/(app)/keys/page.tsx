"use client";
import { useState } from "react";
import { Topbar } from "@/components/app/Topbar";
import { Copy, RotateCw, Eye, EyeOff } from "lucide-react";

const apiKeys = [
  { id: "k_8a01", label: "Production", masked: "rsv_live_…f4a2", created: "2026-02-01", last_used: "12s ago" },
  { id: "k_8a02", label: "Staging",    masked: "rsv_test_…0e91", created: "2026-03-14", last_used: "3h ago"  }
];

export default function KeysPage() {
  const [show, setShow] = useState(false);
  return (
    <>
      <Topbar crumb={[{ label: "Account" }, { label: "API & JWT" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="flex items-end justify-between gap-6 mb-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Secrets · keep them somewhere safe</div>
            <h1 className="font-display text-[36px] leading-[1] tracking-tightest">API keys & JWT</h1>
          </div>
        </div>

        <section className="border border-line bg-paper">
          <div className="px-5 h-11 border-b border-line flex items-center justify-between">
            <div className="font-display text-[18px] tracking-tightest">API keys</div>
            <button className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue">+ Create key</button>
          </div>
          <div className="divide-y divide-line">
            {apiKeys.map((k) => (
              <div key={k.id} className="px-5 py-4 grid grid-cols-12 gap-4 items-center">
                <div className="col-span-3">
                  <div className="text-[14px]">{k.label}</div>
                  <div className="font-mono text-[11px] text-ink-3">{k.id}</div>
                </div>
                <div className="col-span-5 font-mono text-[13px]">{k.masked}</div>
                <div className="col-span-2 text-[12px] text-ink-2">last used {k.last_used}</div>
                <div className="col-span-2 flex items-center justify-end gap-2">
                  <button className="h-8 w-8 inline-flex items-center justify-center border border-line hover:border-ink"><Copy size={13} /></button>
                  <button className="h-8 px-2.5 inline-flex items-center gap-1.5 border border-line hover:border-ink text-[12.5px]"><RotateCw size={12} /> Rotate</button>
                  <button className="h-8 px-2.5 inline-flex items-center border border-line hover:border-danger hover:text-danger text-[12.5px]">Revoke</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-8 border border-line bg-paper">
          <div className="px-5 h-11 border-b border-line flex items-center justify-between">
            <div className="font-display text-[18px] tracking-tightest">End-user JWT secret</div>
            <span className="font-mono text-[11px] text-ink-3">HS256 · per-tenant</span>
          </div>
          <div className="p-5 space-y-4">
            <p className="text-ink-2 text-[13.5px] max-w-2xl">
              Sign per-end-user JWTs to attribute actions and rate-limit by user. Pass them as <span className="font-mono text-ink">X-End-User-JWT</span> on /api/chat.
            </p>
            <div className="flex items-center gap-2">
              <input
                readOnly
                type={show ? "text" : "password"}
                value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.SECRET_NOT_REAL_DATA._sig"
                className="flex-1 h-10 px-3 font-mono text-[13px] border border-line bg-paper outline-none"
              />
              <button onClick={() => setShow(!show)} className="h-10 w-10 inline-flex items-center justify-center border border-line hover:border-ink">
                {show ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
              <button className="h-10 px-3 border border-line text-[13px] inline-flex items-center gap-1.5 hover:border-ink"><Copy size={13} /> Copy</button>
              <button className="h-10 px-3 border border-ink text-[13px] inline-flex items-center gap-1.5 hover:bg-ink hover:text-paper"><RotateCw size={13} /> Rotate</button>
            </div>
            <pre className="font-mono text-[12px] bg-cream border border-line p-3 overflow-auto">
{`# python example
import jwt
token = jwt.encode({"sub": "u_44a02"}, secret, algorithm="HS256")`}
            </pre>
          </div>
        </section>
      </div>
    </>
  );
}
