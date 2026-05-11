import Link from "next/link";

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/85 backdrop-blur">
      <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
          <span className="font-display text-[19px] tracking-tightest leading-none">Resolve<span className="text-blue">.</span></span>
        </Link>
        <nav className="hidden md:flex items-center gap-7 text-[13.5px] text-ink-2">
          <Link href="#features" className="hover:text-ink transition">Product</Link>
          <Link href="#how" className="hover:text-ink transition">How it works</Link>
          <Link href="#pricing" className="hover:text-ink transition">Pricing</Link>
          <Link href="#faq" className="hover:text-ink transition">FAQ</Link>
          <Link href="/docs" className="hover:text-ink transition">Docs</Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href="/signin"
            className="hidden md:inline-flex items-center h-8 px-3 text-[13px] text-ink-2 hover:text-ink transition"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center h-8 px-3 text-[13px] bg-ink text-paper hover:bg-blue transition"
          >
            Start free
          </Link>
        </div>
      </div>
    </header>
  );
}
