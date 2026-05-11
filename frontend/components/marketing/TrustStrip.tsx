export function TrustStrip() {
  const logos = ["Northwind", "Lumio", "Hatchet", "Atlas Goods", "Folio", "Veridia", "Quill", "Mason"];
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex items-center gap-6 text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-6">
          <span className="w-6 h-px bg-line" />
          <span>Operating support for fast-moving brands</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-px bg-line border border-line">
          {logos.map((l) => (
            <div
              key={l}
              className="bg-paper h-16 flex items-center justify-center font-display text-[18px] text-ink-2 hover:text-ink transition"
            >
              {l}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
