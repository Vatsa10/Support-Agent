import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between bg-ink text-paper p-12 border-r border-line relative overflow-hidden">
        <div className="absolute inset-0 bg-dot opacity-10 pointer-events-none" />
        <Link href="/" className="relative flex items-center gap-2.5">
          <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
          <span className="font-display text-[22px] tracking-tightest leading-none">
            Resolve<span className="text-blue">.</span>
          </span>
        </Link>
        <div className="relative">
          <p className="font-display italic text-[44px] leading-[1.05] tracking-tightest max-w-md">
            "We deflected 84% of tier-1 tickets in week one. The agent <span className="text-blue not-italic">acts</span>."
          </p>
          <div className="mt-8 font-mono text-[11px] uppercase tracking-[0.2em] text-paper/60">
            June H. · Head of CX, Northwind
          </div>
        </div>
        <div className="relative font-mono text-[10.5px] text-paper/40 tracking-widest">
          v3.0 · the operator release · built with Aiven + Gemini
        </div>
      </div>
      <div className="flex items-center justify-center px-6 py-16 bg-paper relative">
        <div className="absolute inset-0 bg-grid opacity-50 pointer-events-none" />
        <div className="relative w-full max-w-[380px]">{children}</div>
      </div>
    </div>
  );
}
