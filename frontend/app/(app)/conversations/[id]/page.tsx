import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Topbar } from "@/components/app/Topbar";
import { ReactTimeline } from "@/components/app/ReactTimeline";
import { StatusPill } from "@/components/app/StatusPill";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtTimeAgo, shortId } from "@/lib/fmt";

type Conv = {
  id: string;
  thread_id: string;
  user_id: string;
  started_at: string;
  messages: { role: string; content: string; metadata: any; at: string }[];
  actions: { id: string; tool_name: string; status: string; args: any; result: any; at: string }[];
};

export default async function ConversationDetail({ params }: { params: { id: string } }) {
  const c = await backendFetchSafe<Conv>(`/tenant/conversations/${params.id}`);

  if (!c) {
    return (
      <>
        <Topbar crumb={[{ label: "Operate" }, { label: "Conversations", href: "/conversations" }, { label: params.id }]} />
        <div className="px-6 lg:px-10 py-8">
          <p className="text-ink-2 text-[14px]">Conversation not found.</p>
        </div>
      </>
    );
  }

  // Build a minimal ReACT-like trace from messages + actions
  const trace: any[] = [];
  let step = 1;
  c.actions.forEach((a) => {
    trace.push({ step: step++, kind: "action", text: a.tool_name, meta: a.args });
    trace.push({
      step: step++,
      kind: "observation",
      text: a.result?.error || `${a.tool_name} ${a.status}${a.result?.external_id ? " · " + a.result.external_id : ""}`
    });
  });
  const lastAssistant = [...c.messages].reverse().find((m) => m.role === "assistant");
  if (lastAssistant) trace.push({ step: step++, kind: "response", text: lastAssistant.content });

  return (
    <>
      <Topbar crumb={[{ label: "Operate" }, { label: "Conversations", href: "/conversations" }, { label: params.id }]} />
      <div className="px-6 lg:px-10 py-8">
        <Link href="/conversations" className="inline-flex items-center gap-1 text-[12.5px] text-ink-2 hover:text-blue mb-6">
          <ChevronLeft size={14} /> Back to all
        </Link>

        <div className="grid lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-[11.5px] text-ink-3">{shortId(c.id, 10)}</span>
              <StatusPill status={c.actions.some((a) => a.status === "pending_approval") ? "pending_approval" : "resolved"} />
              <span className="text-[12px] text-ink-3">{fmtTimeAgo(c.started_at)}</span>
            </div>
            <h1 className="font-display text-[34px] leading-[1.05] tracking-tightest">
              Thread <span className="font-mono text-[18px] text-ink-2">{c.thread_id}</span>
            </h1>

            <div className="mt-6 border border-line bg-paper">
              <div className="px-5 h-10 border-b border-line text-[11px] uppercase tracking-[0.18em] text-ink-3 flex items-center">Transcript</div>
              <div className="p-5 space-y-5">
                {c.messages.map((m, i) => (
                  <div key={i} className="flex gap-3">
                    <span
                      className={
                        "shrink-0 w-[64px] font-mono text-[10.5px] uppercase tracking-widest pt-1 " +
                        (m.role === "user" ? "text-ink-3" : "text-blue")
                      }
                    >
                      {m.role}
                    </span>
                    <p className={m.role === "user" ? "text-ink-2 text-[14px]" : "text-ink text-[14px] leading-[1.55]"}>{m.content}</p>
                  </div>
                ))}
              </div>
            </div>

            {trace.length > 0 && (
              <div className="mt-6 border border-line bg-paper p-6">
                <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-3">Operator trace</div>
                <ReactTimeline trace={trace} />
              </div>
            )}
          </div>

          <aside className="lg:col-span-4 space-y-6">
            <Card title="Customer">
              <KV k="User ID" v={c.user_id} mono />
              <KV k="Thread" v={c.thread_id} mono />
              <KV k="Started" v={fmtTimeAgo(c.started_at)} />
            </Card>
            <Card title={`Action runs · ${c.actions.length}`}>
              {c.actions.length === 0 && <div className="text-[12.5px] text-ink-3">No side-effects yet.</div>}
              {c.actions.map((a) => (
                <KV
                  key={a.id}
                  k={a.tool_name}
                  v={a.result?.external_id || a.status}
                  mono
                  pill={a.status}
                />
              ))}
            </Card>
          </aside>
        </div>
      </div>
    </>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-line bg-paper">
      <div className="px-4 h-9 border-b border-line flex items-center text-[11px] uppercase tracking-[0.18em] text-ink-3">{title}</div>
      <div className="p-4 space-y-2.5">{children}</div>
    </div>
  );
}

function KV({ k, v, mono, pill }: { k: string; v: string; mono?: boolean; pill?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-[13px]">
      <span className="text-ink-2">{k}</span>
      <span className="flex items-center gap-2">
        {pill && <StatusPill status={pill} />}
        <span className={mono ? "font-mono text-ink truncate max-w-[160px]" : "text-ink"}>{v}</span>
      </span>
    </div>
  );
}
