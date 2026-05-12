"use client";
import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Send, X } from "lucide-react";

type Msg = { role: "user" | "agent"; text: string; action?: string };

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function EmbedChat() {
  const params = useParams<{ tenant: string }>();
  const search = useSearchParams();
  const pk = search.get("pk") || "";

  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "agent", text: "Hi — I'm Resolve, the support operator for this site. Tell me what you need and I'll handle it." }
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [thread, setThread] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [context, setContext] = useState<any>({});
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    parent.postMessage({ __resolve: true, type: "ready" }, "*");
    function onMsg(ev: MessageEvent) {
      const d: any = ev.data;
      if (!d || !d.__resolve) return;
      if (d.type === "boot") { setUser(d.user); setContext(d.context || {}); }
      if (d.type === "set")  { setContext((c: any) => ({ ...c, ...(d.context || {}) })); }
    }
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, thinking]);

  async function send() {
    const text = input.trim();
    if (!text || thinking || !pk) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setThinking(true);
    try {
      const res = await fetch(`${BACKEND}/public/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          publishable_key: pk,
          user_id: user?.user_id,
          thread_id: thread,
          end_user_jwt: user?.user_hmac,
          context
        })
      });
      const data = await res.json();
      if (!res.ok) {
        setMsgs((m) => [...m, { role: "agent", text: `Error: ${data.detail || res.statusText}` }]);
        return;
      }
      if (data.thread_id) setThread(data.thread_id);
      const reply: Msg = {
        role: "agent",
        text: data.response || "(no response)",
        action: data.metadata?.intent
      };
      setMsgs((m) => [...m, reply]);
      if (data.action_run_id) {
        parent.postMessage({ __resolve: true, type: "resolved", payload: { action_run_id: data.action_run_id } }, "*");
      }
      parent.postMessage({ __resolve: true, type: "message", payload: { role: "agent", text: reply.text } }, "*");
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "agent", text: `Network error: ${e?.message || "unknown"}` }]);
    } finally {
      setThinking(false);
    }
  }

  return (
    <div className="h-dvh flex flex-col bg-paper text-ink font-sans">
      <header className="h-12 border-b border-line px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
          <span className="font-display text-[16px] tracking-tightest leading-none">
            Resolve<span className="text-blue">.</span>
          </span>
          <span className="ml-2 font-mono text-[10.5px] uppercase tracking-widest text-ink-3">
            {params.tenant}
          </span>
        </div>
        <button
          onClick={() => parent.postMessage({ __resolve: true, type: "close" }, "*")}
          className="text-ink-2 hover:text-ink"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {msgs.map((m, i) => <Bubble key={i} m={m} />)}
        {thinking && (
          <div className="flex items-center gap-2 text-ink-3 text-[12px] font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-blue animate-pulse" />
            resolve is thinking…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(); }}
        className="border-t border-line p-2.5 flex items-end gap-2"
      >
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder={pk ? "Describe what you need…" : "Missing publishable key"}
          disabled={!pk}
          className="flex-1 resize-none border border-line bg-paper px-3 py-2 text-[13.5px] outline-none focus:border-ink min-h-[40px] max-h-[140px] disabled:bg-cream disabled:text-ink-3"
        />
        <button
          type="submit"
          disabled={!input.trim() || thinking || !pk}
          className="h-10 px-3 bg-ink text-paper text-[13px] inline-flex items-center gap-1.5 hover:bg-blue disabled:opacity-50 transition"
        >
          <Send size={14} /> Send
        </button>
      </form>

      <footer className="border-t border-line px-4 h-8 flex items-center justify-between text-[10.5px] font-mono text-ink-3">
        <span>powered by Resolve</span>
        <span>{user?.user_id ? `id ${user.user_id}` : "anon"}{context?.order_id ? ` · order ${context.order_id}` : ""}</span>
      </footer>
    </div>
  );
}

function Bubble({ m }: { m: Msg }) {
  if (m.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-ink text-paper text-[13.5px] px-3 py-2 leading-[1.5]">{m.text}</div>
      </div>
    );
  }
  return (
    <div className="flex gap-2">
      <span className="shrink-0 mt-1 w-1.5 h-1.5 bg-blue" />
      <div className="max-w-[88%]">
        <div className="text-[13.5px] text-ink leading-[1.55]">{m.text}</div>
      </div>
    </div>
  );
}
