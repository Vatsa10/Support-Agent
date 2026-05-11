import Link from "next/link";

export function EmptyState({
  title,
  body,
  cta
}: {
  title: string;
  body: string;
  cta?: { label: string; href?: string; onClick?: () => void };
}) {
  return (
    <div className="border border-line border-dashed bg-paper px-8 py-16 text-center">
      <div className="mx-auto w-10 h-10 border border-ink-2 mb-6 flex items-center justify-center font-display italic text-ink-2">
        ø
      </div>
      <h3 className="font-display text-[28px] leading-tight tracking-tightest">{title}</h3>
      <p className="mt-2 text-ink-2 text-[14px] max-w-md mx-auto">{body}</p>
      {cta && (
        cta.href ? (
          <Link href={cta.href} className="mt-6 inline-flex h-10 px-4 bg-ink text-paper text-[13.5px] hover:bg-blue transition">
            {cta.label}
          </Link>
        ) : (
          <button onClick={cta.onClick} className="mt-6 inline-flex h-10 px-4 bg-ink text-paper text-[13.5px] hover:bg-blue transition">
            {cta.label}
          </button>
        )
      )}
    </div>
  );
}
