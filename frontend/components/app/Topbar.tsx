"use client";
import { Search, Bell, Sparkles } from "lucide-react";

export function Topbar({ crumb }: { crumb: { label: string; href?: string }[] }) {
  return (
    <header className="sticky top-0 z-30 bg-paper/85 backdrop-blur border-b border-line">
      <div className="h-14 px-6 flex items-center justify-between gap-6">
        <ol className="flex items-center gap-2 text-[13px] text-ink-2 min-w-0">
          {crumb.map((c, i) => (
            <li key={c.label} className="flex items-center gap-2 min-w-0">
              {i > 0 && <span className="text-ink-3">/</span>}
              <span className={i === crumb.length - 1 ? "text-ink truncate" : "truncate"}>{c.label}</span>
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
          <div className="w-8 h-8 bg-ink text-paper font-mono text-[11px] inline-flex items-center justify-center">
            KT
          </div>
        </div>
      </div>
    </header>
  );
}
