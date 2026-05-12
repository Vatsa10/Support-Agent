"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

export default function Forgot() {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    const fd = new FormData(e.currentTarget);
    await fetch("/api/auth/forgot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: fd.get("email") })
    }).catch(() => null);
    setBusy(false);
    setDone(true);
  }

  if (done) {
    return (
      <div>
        <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Check your inbox</div>
        <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
          Look for an <span className="italic text-blue">email.</span>
        </h1>
        <p className="mt-3 text-ink-2 text-[14px]">
          If an account exists for that address, a reset link is on its way. The link expires in 30 minutes.
        </p>
        <p className="mt-10 text-[13px] text-ink-2">
          <Link href="/signin" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">
            Back to sign in →
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Forgot password</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Reset your <span className="italic text-blue">password.</span>
      </h1>
      <p className="mt-3 text-ink-2 text-[14px]">Enter your work email — we'll send a one-time link.</p>

      <form onSubmit={submit} className="mt-10 space-y-5">
        <label className="block">
          <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Work email</span>
          <input
            name="email"
            type="email"
            required
            placeholder="kira@acme.co"
            className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition disabled:opacity-50"
        >
          {busy ? "Sending…" : <>Send reset link <ArrowRight size={15} /></>}
        </button>
      </form>

      <p className="mt-10 text-[13px] text-ink-2">
        Remembered it? <Link href="/signin" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">Sign in →</Link>
      </p>
    </div>
  );
}
