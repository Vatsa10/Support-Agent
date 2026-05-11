import { cn } from "@/lib/cn";

type Col<T> = {
  key: keyof T | string;
  label: string;
  width?: string;
  align?: "left" | "right";
  render?: (row: T) => React.ReactNode;
};

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  empty,
  rowHref
}: {
  columns: Col<T>[];
  rows: T[];
  empty?: React.ReactNode;
  rowHref?: (row: T) => string;
}) {
  if (!rows.length && empty) return <>{empty}</>;
  return (
    <div className="border border-line bg-paper overflow-hidden">
      <div className="grid border-b border-line bg-cream" style={gridStyle(columns)}>
        {columns.map((c) => (
          <div
            key={String(c.key)}
            className={cn(
              "px-4 h-9 flex items-center text-[11px] uppercase tracking-[0.16em] text-ink-3",
              c.align === "right" && "justify-end"
            )}
          >
            {c.label}
          </div>
        ))}
      </div>
      <div className="divide-y divide-line">
        {rows.map((r) => {
          const href = rowHref?.(r);
          const Tag: any = href ? "a" : "div";
          return (
            <Tag
              key={r.id}
              href={href}
              className={cn(
                "grid items-center hover:bg-cream/70 transition",
                href && "cursor-pointer"
              )}
              style={gridStyle(columns)}
            >
              {columns.map((c) => (
                <div
                  key={String(c.key)}
                  className={cn(
                    "px-4 h-12 flex items-center text-[13px] text-ink min-w-0",
                    c.align === "right" && "justify-end"
                  )}
                >
                  <div className="truncate">{c.render ? c.render(r) : String((r as any)[c.key] ?? "")}</div>
                </div>
              ))}
            </Tag>
          );
        })}
      </div>
    </div>
  );
}

function gridStyle<T>(cols: Col<T>[]): React.CSSProperties {
  return { gridTemplateColumns: cols.map((c) => c.width || "minmax(0,1fr)").join(" ") };
}
