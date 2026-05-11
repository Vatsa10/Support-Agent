import { cn } from "@/lib/cn";

type Step = { step: number; kind: string; text: string; meta?: any };

const meta = {
  thought:     { label: "Thought",     color: "text-ink-3", line: "bg-ink-3" },
  action:      { label: "Action",      color: "text-blue",  line: "bg-blue" },
  observation: { label: "Observation", color: "text-ink-2", line: "bg-ink-2" },
  response:    { label: "Response",    color: "text-success", line: "bg-success" }
} as const;

export function ReactTimeline({ trace }: { trace: Step[] }) {
  return (
    <ol className="relative">
      {trace.map((s, i) => {
        const m = (meta as any)[s.kind] || meta.thought;
        const last = i === trace.length - 1;
        return (
          <li key={s.step} className="relative pl-12 pb-6">
            {!last && <span className="absolute left-[14px] top-7 bottom-0 w-px bg-line" />}
            <span className={cn("absolute left-[10px] top-2 w-2 h-2 rounded-full", m.line)} />
            <div className="flex items-center gap-3">
              <span className={cn("font-mono text-[10.5px] uppercase tracking-[0.18em]", m.color)}>
                {String(s.step).padStart(2, "0")} · {m.label}
              </span>
              {s.kind === "action" && (
                <span className="font-mono text-[11px] bg-cream border border-line px-1.5 py-0.5 text-ink">
                  {s.text}
                </span>
              )}
            </div>
            <div className={cn("mt-1.5 text-[14px] leading-[1.55]", s.kind === "thought" ? "text-ink-2" : "text-ink")}>
              {s.kind === "action" ? (
                <pre className="font-mono text-[12.5px] text-ink-2 bg-cream border border-line p-3 overflow-auto">
{JSON.stringify(s.meta ?? {}, null, 2)}
                </pre>
              ) : (
                s.text
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
