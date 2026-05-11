"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid,
  MessageSquare,
  Zap,
  CheckSquare,
  Plug,
  ShieldCheck,
  Database,
  Coins,
  KeyRound,
  Settings,
  BookOpen,
  Code2
} from "lucide-react";

type NavItem = {
  href: string;
  title: string;
  icon: typeof LayoutGrid;
  badge?: string;
  emphasize?: boolean;
};
type NavGroup = { label: string; items: NavItem[] };

const groups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { href: "/dashboard", title: "Home", icon: LayoutGrid }
    ]
  },
  {
    label: "Operate",
    items: [
      { href: "/conversations", title: "Conversations", icon: MessageSquare, badge: "12" },
      { href: "/actions",       title: "Action runs",   icon: Zap },
      { href: "/approvals",     title: "Approvals",     icon: CheckSquare, badge: "7", emphasize: true }
    ]
  },
  {
    label: "Configure",
    items: [
      { href: "/install",      title: "Install",      icon: Code2, emphasize: true },
      { href: "/integrations", title: "Integrations", icon: Plug },
      { href: "/policies",     title: "Policies",     icon: ShieldCheck },
      { href: "/kb",           title: "Knowledge",    icon: Database },
      { href: "/settings",     title: "Settings",     icon: Settings }
    ]
  },
  {
    label: "Account",
    items: [
      { href: "/billing", title: "Billing", icon: Coins },
      { href: "/keys",    title: "API & JWT", icon: KeyRound },
      { href: "/docs",    title: "Docs", icon: BookOpen }
    ]
  }
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex flex-col w-[248px] shrink-0 border-r border-line bg-paper sticky top-0 h-dvh">
      <div className="px-5 h-14 flex items-center border-b border-line">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
          <span className="font-display text-[19px] tracking-tightest leading-none">
            Resolve<span className="text-blue">.</span>
          </span>
        </Link>
      </div>

      <div className="px-3 py-3 border-b border-line">
        <button className="w-full text-left h-10 px-2.5 hover:bg-cream transition flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 bg-ink text-paper text-[10.5px] flex items-center justify-center font-mono">AG</div>
            <div className="leading-tight">
              <div className="text-[13px]">Acme Goods</div>
              <div className="text-[10.5px] font-mono text-ink-3">org_2pq…</div>
            </div>
          </div>
          <span className="text-ink-3 text-[12px]">⇅</span>
        </button>
      </div>

      <nav className="flex-1 overflow-auto px-3 py-4 space-y-6">
        {groups.map((g) => (
          <div key={g.label}>
            <div className="px-2 text-[10.5px] uppercase tracking-[0.18em] text-ink-3 mb-2">{g.label}</div>
            <ul className="space-y-px">
              {g.items.map((it) => {
                const active = pathname === it.href || pathname?.startsWith(it.href + "/");
                const Icon = it.icon;
                return (
                  <li key={it.href}>
                    <Link
                      href={it.href}
                      className={
                        "group flex items-center gap-2.5 px-2.5 h-8 text-[13px] transition " +
                        (active
                          ? "bg-ink text-paper"
                          : "text-ink-2 hover:text-ink hover:bg-cream")
                      }
                    >
                      <Icon size={14} strokeWidth={1.75} className={active ? "text-blue" : ""} />
                      <span className="flex-1">{it.title}</span>
                      {it.badge && (
                        <span
                          className={
                            "px-1.5 h-[18px] inline-flex items-center font-mono text-[10.5px] " +
                            (active
                              ? "bg-paper/15 text-paper"
                              : it.emphasize
                              ? "bg-blue text-paper"
                              : "bg-line-2 text-ink-2")
                          }
                        >
                          {it.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-line p-3 text-[11px] text-ink-3 font-mono flex items-center justify-between">
        <span>v3.0.0</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> all systems
        </span>
      </div>
    </aside>
  );
}
