"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

export default function Reset() {
  const search = useSearchParams();
  const token = search.get("token") || "";
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) {
      setErr("Missing reset token in URL.");
      return;
    }
    setBusy(true);
    setErr(null);
    const fd = new FormData(e.currentTarget);
    const res = await fetch("/api/auth/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, password: fd.get("password") })
    });
    const data = await res.json().catch(() => ({}));
    setBusy(false);
    if (!res.ok) {
      setErr(data.detail || "Reset failed");
      return;
    }
    setDone(true);
  }

  if (done) {
    return (
      <div>
        <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">All set</div>
        <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
          Password <span className="italic text-blue">updated.</span>
        </h1>
        <p className="mt-3 text-ink-2 text-[14px]">You can sign in now.</p>
        <Link
          href="/signin"
          className="mt-8 inline-flex h-11 px-5 bg-ink text-paper text-[14px] items-center gap-2 hover:bg-blue"
        >
          Go to sign in <ArrowRight size={15} />
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Choose a new password</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Set new <span className="italic text-blue">password.</span>
      </h1>

      <form onSubmit={submit} className="mt-10 space-y-5">
        <label className="block">
          <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">New password</span>
          <input
            name="password"
            type="password"
            required
            minLength={10}
            placeholder="•••••••••••"
            className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
          />
          <span className="block mt-1.5 text-[12px] text-ink-3">At least 10 characters.</span>
        </label>
        {err && <div className="text-[13px] text-danger">{err}</div>}
        <button
          type="submit"
          disabled={busy}
          className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition disabled:opacity-50"
        >
          {busy ? "Saving…" : <>Update password <ArrowRight size={15} /></>}
        </button>
      </form>
    </div>
  );
}
