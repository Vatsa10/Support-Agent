"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

export default function SignIn() {
  const _router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const fd = new FormData(e.currentTarget);
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 30_000);
    try {
      const res = await fetch("/api/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: fd.get("email"), password: fd.get("password") }),
        signal: ctrl.signal
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErr(data.error || "Sign-in failed");
        setBusy(false);
        return;
      }
      window.location.href = "/dashboard";
    } catch (e: any) {
      setErr(e?.name === "AbortError" ? "Timed out. Try again." : e?.message || "Network error");
      setBusy(false);
    } finally {
      clearTimeout(t);
    }
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Welcome back</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Sign in to <span className="italic text-blue">Resolve.</span>
      </h1>
      <p className="mt-3 text-ink-2 text-[14px]">Operating support at the speed of an API call.</p>

      <form onSubmit={submit} className="mt-10 space-y-5">
        <Field name="email" label="Work email" type="email" placeholder="kira@acme.co" required />
        <Field name="password" label="Password" type="password" placeholder="••••••••••" required />
        {err && <div className="text-[13px] text-danger">{err}</div>}
        <div className="flex items-center justify-between text-[12.5px]">
          <label className="inline-flex items-center gap-2 text-ink-2">
            <input type="checkbox" className="accent-blue h-3.5 w-3.5" /> Keep me signed in
          </label>
          <Link href="/forgot" className="text-ink-2 hover:text-blue transition">Forgot password?</Link>
        </div>
        <button
          type="submit"
          disabled={busy}
          className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition disabled:opacity-50"
        >
          {busy ? "Signing in…" : <>Sign in <ArrowRight size={15} /></>}
        </button>
      </form>

      <p className="mt-10 text-[13px] text-ink-2">
        New to Resolve? <Link href="/signup" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">Create an account →</Link>
      </p>
    </div>
  );
}

function Field({ label, ...rest }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        {...rest}
        className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
      />
    </label>
  );
}
