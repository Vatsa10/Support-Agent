"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

export default function SignUp() {
  const _router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const fd = new FormData(e.currentTarget);
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 40_000);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: fd.get("name"),
          company: fd.get("company"),
          email: fd.get("email"),
          password: fd.get("password")
        }),
        signal: ctrl.signal
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErr(data.error || "Signup failed");
        setBusy(false);
        return;
      }
      // Hard navigation so the new httpOnly cookie is sent on the next request.
      window.location.href = data.next || "/onboarding";
    } catch (e: any) {
      setErr(e?.name === "AbortError" ? "Timed out. Try again." : e?.message || "Network error");
      setBusy(false);
    } finally {
      clearTimeout(t);
    }
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Get started</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Create your <span className="italic text-blue">workspace.</span>
      </h1>
      <p className="mt-3 text-ink-2 text-[14px]">$0 forever for the first 200 resolutions per month.</p>

      <form onSubmit={submit} className="mt-10 space-y-5">
        <div className="grid grid-cols-2 gap-3">
          <Field name="name" label="Full name" placeholder="Kira Tan" required />
          <Field name="company" label="Company" placeholder="Acme Goods" required />
        </div>
        <Field name="email" label="Work email" type="email" placeholder="kira@acme.co" required />
        <Field
          name="password"
          label="Password"
          type="password"
          placeholder="•••••••••••"
          required
          minLength={10}
          hint="At least 10 characters."
        />
        {err && <div className="text-[13px] text-danger">{err}</div>}

        <button
          type="submit"
          disabled={busy}
          className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition disabled:opacity-50"
        >
          {busy ? "Creating workspace…" : <>Create workspace <ArrowRight size={15} /></>}
        </button>
        <p className="text-[12px] text-ink-3 leading-relaxed">
          By continuing you agree to our <Link href="/terms" className="underline underline-offset-4 decoration-line">Terms</Link>{" "}
          and <Link href="/privacy" className="underline underline-offset-4 decoration-line">Privacy</Link>.
        </p>
      </form>

      <p className="mt-10 text-[13px] text-ink-2">
        Have an account? <Link href="/signin" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">Sign in →</Link>
      </p>
    </div>
  );
}

function Field({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        {...rest}
        className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
      />
      {hint && <span className="block mt-1.5 text-[12px] text-ink-3">{hint}</span>}
    </label>
  );
}
