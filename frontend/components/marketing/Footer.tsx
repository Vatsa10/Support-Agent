import Link from "next/link";

export function Footer() {
  const groups = [
    { title: "Product", links: [["Features", "#features"], ["Pricing", "#pricing"], ["Changelog", "/changelog"], ["Status", "/status"]] },
    { title: "Build", links: [["Docs", "/docs"], ["API", "/docs/api"], ["Connectors", "/docs/connectors"], ["Self-host", "/docs/self-host"]] },
    { title: "Company", links: [["Manifesto", "/about"], ["Customers", "/customers"], ["Careers", "/careers"], ["Security", "/security"]] },
    { title: "Legal", links: [["Terms", "/terms"], ["Privacy", "/privacy"], ["DPA", "/dpa"], ["Sub-processors", "/sub"]] }
  ];
  return (
    <footer className="bg-paper">
      <div className="mx-auto max-w-7xl px-6 pt-20 pb-10">
        <div className="grid lg:grid-cols-12 gap-10">
          <div className="lg:col-span-5">
            <div className="flex items-center gap-2.5">
              <span className="inline-block w-2 h-2 bg-blue translate-y-[1px]" />
              <span className="font-display text-[24px] tracking-tightest leading-none">
                Resolve<span className="text-blue">.</span>
              </span>
            </div>
            <p className="mt-6 max-w-md text-ink-2 text-[14px] leading-[1.6]">
              The AI operator for customer support. Built for teams that want resolutions, not transcripts.
            </p>
            <div className="mt-8 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-3">
              Made for operators · 26°N
            </div>
          </div>
          <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-4 gap-8 lg:gap-10">
            {groups.map((g) => (
              <div key={g.title}>
                <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">{g.title}</div>
                <ul className="space-y-2.5">
                  {g.links.map(([label, href]) => (
                    <li key={label}>
                      <Link href={href} className="text-[13.5px] text-ink hover:text-blue transition">
                        {label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-16 pt-6 border-t border-line flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="text-[12px] text-ink-3">© {new Date().getFullYear()} Vatsa's Labs</div>
          <div className="font-mono text-[11px] text-ink-3">v3.0.0 · build 0a91c</div>
        </div>
      </div>
    </footer>
  );
}
