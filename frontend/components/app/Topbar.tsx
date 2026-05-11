"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Search, Bell, Sparkles, LogOut, Settings, KeyRound, ChevronDown } from "lucide-react";

type Me = {
  tenant_id: string;
  tenant_name: string;
  plan: string;
  user?: { id: string; email: string; name: string | null; role: string } | null;
};

export function Topbar({ crumb }: { crumb: { label: string; href?: string }[] }) {
  const [me, setMe] = useState<Me | null>(null);
  const [open, setOpen] = useState(false);
  const popRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetch("/api/auth/me", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setMe(d))
      .catch(() => setMe(null));
  }, []);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!popRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const name = me?.user?.name || me?.user?.email?.split("@")[0] || "—";
  const email = me?.user?.email || "";
  const initials =
    (me?.user?.name || me?.user?.email || "R S")
      .split(/[\s@.]+/)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase() ?? "")
      .join("") || "RS";

  return (
    <header className="sticky top-0 z-30 bg-paper/85 backdrop-blur border-b border-line">
      <div className="h-14 px-6 flex items-center justify-between gap-6">
        <ol className="flex items-center gap-2 text-[13px] text-ink-2 min-w-0">
          {crumb.map((c, i) => (
            <li key={c.label} className="flex items-center gap-2 min-w-0">
              {i > 0 && <span className="text-ink-3">/</span>}
              {c.href ? (
                <Link href={c.href} className="truncate hover:text-ink">
                  {c.label}
                </Link>
              ) : (
                <span className={i === crumb.length - 1 ? "text-ink truncate" : "truncate"}>{c.label}</span>
              )}
            </li>
          ))}
        </ol>

        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-2 border border-line h-8 px-2.5 w-[280px]">
            <Search size={14} className="text-ink-3" />
            <input
              placeholder="Search conversations, actions, IDs…"
              className="flex-1 bg-transparent text-[13px] outline-none placeholder:text-ink-3"
            />
            <span className="font-mono text-[10.5px] text-ink-3 bg-line-2 px-1.5 py-0.5">⌘K</span>
          </div>

          <button className="h-8 w-8 inline-flex items-center justify-center border border-line hover:border-ink transition">
            <Bell size={14} />
          </button>
          <button className="h-8 px-3 inline-flex items-center gap-2 border border-line hover:border-ink transition text-[13px]">
            <Sparkles size={13} className="text-blue" /> Ask Resolve
          </button>

          <div ref={popRef} className="relative">
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex items-center gap-2 h-8 pl-1 pr-2 border border-line hover:border-ink transition"
            >
              <span className="w-6 h-6 bg-ink text-paper font-mono text-[10.5px] inline-flex items-center justify-center">
                {initials}
              </span>
              <span className="hidden lg:flex flex-col items-start leading-tight">
                <span className="text-[12px] text-ink truncate max-w-[140px]">{name}</span>
                <span className="text-[10px] font-mono text-ink-3 truncate max-w-[140px]">
                  {me?.tenant_name || "—"}
                </span>
              </span>
              <ChevronDown size={12} className="text-ink-2" />
            </button>

            {open && (
              <div className="absolute right-0 top-10 w-[280px] bg-paper border border-ink z-50">
                <div className="px-4 py-3 border-b border-line">
                  <div className="flex items-center gap-3">
                    <span className="w-9 h-9 bg-ink text-paper font-mono text-[12px] inline-flex items-center justify-center">
                      {initials}
                    </span>
                    <div className="min-w-0">
                      <div className="text-[13px] text-ink truncate">{name}</div>
                      <div className="text-[11.5px] font-mono text-ink-3 truncate">{email}</div>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[11.5px]">
                    <span className="text-ink-2">{me?.tenant_name || "—"}</span>
                    <span className="font-mono uppercase tracking-widest text-blue">{me?.plan || "free"}</span>
                  </div>
                </div>
                <MenuLink href="/settings" icon={<Settings size={13} />} label="Workspace settings" />
                <MenuLink href="/keys" icon={<KeyRound size={13} />} label="API keys & JWT" />
                <form action="/api/auth/logout" method="post">
                  <button
                    type="submit"
                    className="w-full flex items-center gap-2 h-9 px-4 text-[13px] text-ink-2 hover:text-danger hover:bg-cream border-t border-line"
                  >
                    <LogOut size={13} /> Sign out
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

function MenuLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 h-9 px-4 text-[13px] text-ink-2 hover:text-ink hover:bg-cream">
      {icon} {label}
    </Link>
  );
}
