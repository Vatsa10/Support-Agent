"use client";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Send, ArrowUpRight } from "lucide-react";

type Msg = { role: "user" | "agent"; text: string; action?: string };

export default function HostedChat() {
  const params = useParams<{ slug: string }>();
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "agent", text: `Hi, I'm Resolve, the AI support operator for ${prettify(params.slug)}. Tell me what you need — refunds, replacements, cancellations, or general questions are all in scope.` }
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, busy]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setBusy(true);
    await new Promise((r) => setTimeout(r, 900));
    const reply: Msg = text.toLowerCase().includes("refund")
      ? { role: "agent", text: "Verified your order is in the 30-day window. Refund issued — 3–5 business days to appear. Want a confirmation email too?", action: "issue_refund" }
      : { role: "agent", text: "Let me check our knowledge base. One moment.", action: "knowledge_search" };
    setMsgs((m) => [...m, reply]);
    setBusy(false);
  }

  return (
    <div className="min-h-dvh flex flex-col bg-paper">
      <header className="border-b border-line">
        <div className="mx-auto max-w-3xl px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
            <div>
              <div className="font-display text-[18px] tracking-tightest leading-none">
                {prettify(params.slug)} <span className="text-ink-3 text-[12px] ml-1">support</span>
              </div>
              <div className="text-[11px] text-ink-3 font-mono mt-0.5">
                powered by Resolve · 24×7 · resolves in seconds
              </div>
            </div>
          </div>
          <Link href="/" className="inline-flex items-center gap-1 text-[12px] text-ink-2 hover:text-blue">
            Resolve <ArrowUpRight size={12} />
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-6 py-10 space-y-6">
            {msgs.map((m, i) => (
              <div key={i} className="flex gap-4">
                <span className={
                  "shrink-0 w-[64px] font-mono text-[10.5px] uppercase tracking-widest pt-1 " +
                  (m.role === "user" ? "text-ink-3" : "text-blue")
                }>
                  {m.role === "user" ? "you" : "resolve"}
                </span>
                <div className="flex-1">
                  {m.action && (
                    <div className="font-mono text-[10.5px] uppercase tracking-widest text-blue mb-0.5">
                      {m.action}
                    </div>
                  )}
                  <p className={(m.role === "user" ? "text-ink-2" : "text-ink") + " text-[15px] leading-[1.6]"}>
                    {m.text}
                  </p>
                </div>
              </div>
            ))}
            {busy && (
              <div className="flex gap-4">
                <span className="shrink-0 w-[64px] font-mono text-[10.5px] uppercase tracking-widest text-blue pt-1">
                  resolve
                </span>
                <div className="flex items-center gap-2 text-ink-3 text-[12px] font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue animate-pulse" />
                  thinking…
                </div>
              </div>
            )}
          </div>
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          className="border-t border-line"
        >
          <div className="mx-auto max-w-3xl px-6 py-4 flex items-end gap-2">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="Describe what you need…"
              className="flex-1 resize-none border border-line bg-paper px-3 py-2.5 text-[14px] outline-none focus:border-ink min-h-[44px] max-h-[160px]"
            />
            <button
              type="submit"
              disabled={!input.trim() || busy}
              className="h-11 px-4 bg-ink text-paper text-[13.5px] inline-flex items-center gap-1.5 hover:bg-blue disabled:opacity-50 transition"
            >
              <Send size={14} /> Send
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

function prettify(slug: string) {
  return (slug || "").replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
