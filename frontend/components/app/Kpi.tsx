import { cn } from "@/lib/cn";

export function Kpi({
  label,
  value,
  delta,
  hint,
  className
}: {
  label: string;
  value: string;
  delta?: string;
  hint?: string;
  className?: string;
}) {
  const up = delta?.startsWith("+");
  return (
    <div className={cn("bg-paper p-6", className)}>
      <div className="flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3">{label}</div>
        {delta && (
          <span
            className={cn(
              "font-mono text-[11px] tabular-nums",
              up ? "text-success" : "text-danger"
            )}
          >
            {delta}
          </span>
        )}
      </div>
      <div className="mt-3 font-display text-[44px] leading-none tracking-tightest">{value}</div>
      {hint && <div className="mt-1.5 text-[12px] text-ink-3">{hint}</div>}
    </div>
  );
}
