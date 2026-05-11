import { cn } from "@/lib/cn";

const map: Record<string, { dot: string; ink: string; label?: string }> = {
  succeeded:         { dot: "bg-success",       ink: "text-success" },
  resolved:          { dot: "bg-success",       ink: "text-success" },
  healthy:           { dot: "bg-success",       ink: "text-success" },
  active:            { dot: "bg-success",       ink: "text-success" },
  pending_approval:  { dot: "bg-warn",          ink: "text-warn", label: "pending approval" },
  pending:           { dot: "bg-warn",          ink: "text-warn" },
  degraded:          { dot: "bg-warn",          ink: "text-warn" },
  escalated:         { dot: "bg-warn",          ink: "text-warn" },
  failed:            { dot: "bg-danger",        ink: "text-danger" },
  disconnected:      { dot: "bg-ink-3",         ink: "text-ink-2" },
  denied:            { dot: "bg-danger",        ink: "text-danger" },
  running:           { dot: "bg-blue",          ink: "text-blue" }
};

export function StatusPill({ status }: { status: string }) {
  const s = map[status] ?? { dot: "bg-ink-3", ink: "text-ink-2" };
  return (
    <span className={cn("inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider", s.ink)}>
      <span className={cn("w-1.5 h-1.5 rounded-full", s.dot)} />
      {s.label ?? status.replace(/_/g, " ")}
    </span>
  );
}
