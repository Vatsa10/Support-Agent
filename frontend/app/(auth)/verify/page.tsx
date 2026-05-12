"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="text-ink-3 text-[13px]">Loading…</div>}>
      <Verify />
    </Suspense>
  );
}

function Verify() {
  const search = useSearchParams();
  const token = search.get("token") || "";
  const [state, setState] = useState<"verifying" | "ok" | "fail">("verifying");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setState("fail");
      setErr("Missing token.");
      return;
    }
    (async () => {
      const r = await fetch("/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token })
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok) setState("ok");
      else { setState("fail"); setErr(d.detail || "Verification failed"); }
    })();
  }, [token]);

  return (
    <div>
      {state === "verifying" && (
        <>
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Just a moment</div>
          <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
            Verifying your <span className="italic text-blue">email…</span>
          </h1>
        </>
      )}
      {state === "ok" && (
        <>
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Done</div>
          <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
            Email <span className="italic text-blue">verified.</span>
          </h1>
          <p className="mt-3 text-ink-2 text-[14px]">You're set. Alerts and security updates will reach you now.</p>
          <Link href="/dashboard" className="mt-8 inline-flex h-11 px-5 bg-ink text-paper text-[14px] items-center hover:bg-blue">
            Open dashboard →
          </Link>
        </>
      )}
      {state === "fail" && (
        <>
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Hmm</div>
          <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
            Could not <span className="italic text-blue">verify.</span>
          </h1>
          <p className="mt-3 text-ink-2 text-[14px]">{err || "Link expired or already used."}</p>
          <Link href="/signin" className="mt-8 inline-flex h-11 px-5 border border-ink text-[14px] items-center hover:bg-ink hover:text-paper">
            Back to sign in →
          </Link>
        </>
      )}
    </div>
  );
}
