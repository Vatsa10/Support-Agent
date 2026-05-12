"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Topbar } from "@/components/app/Topbar";
import { ConnectIntegrationModal } from "@/components/app/ConnectIntegrationModal";
import { Check, ArrowRight, Plug, Database, Code2 } from "lucide-react";

type Kind = "stripe" | "shopify" | "zendesk" | "generic_webhook";

export default function OnboardingPage() {
  const router = useRouter();
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [pubKey, setPubKey] = useState<string | null>(null);
  const [me, setMe] = useState<any>(null);
  const [openModal, setOpenModal] = useState<Kind | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [iRes, sRes, pkRes, meRes] = await Promise.all([
      fetch("/api/backend/tenant/integrations", { cache: "no-store" }),
      fetch("/api/backend/tenant/kb/sources", { cache: "no-store" }),
      fetch("/api/backend/tenant/publishable-keys", { cache: "no-store" }),
      fetch("/api/auth/me", { cache: "no-store" })
    ]);
    if (iRes.ok) setIntegrations(await iRes.json());
    if (sRes.ok) setSources(await sRes.json());
    if (pkRes.ok) {
      const keys = await pkRes.json();
      const active = keys.find((k: any) => k.status === "active");
      if (active) setPubKey(active.pub_key);
    }
    if (meRes.ok) setMe(await meRes.json());
  }
  useEffect(() => { refresh(); }, []);

  async function ensurePubKey() {
    if (pubKey) return pubKey;
    setBusy(true);
    const r = await fetch("/api/backend/tenant/publishable-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: "widget" })
    });
    setBusy(false);
    if (!r.ok) return null;
    const d = await r.json();
    setPubKey(d.pub_key);
    return d.pub_key;
  }

  const hasIntegration = integrations.length > 0;
  const hasKb = sources.length > 0;
  const tenantSlug = (me?.tenant_name || "demo").toLowerCase().replace(/[^a-z0-9]+/g, "-");

  return (
    <>
      <Topbar crumb={[{ label: "Welcome" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="mb-10">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">3 steps · ~5 minutes</div>
          <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
            Let's get <span className="italic text-blue">{me?.tenant_name || "you"}</span> resolving.
          </h1>
          <p className="text-ink-2 text-[15px] mt-3 max-w-xl leading-[1.55]">
            Connect a backend so the operator can act. Drop in your knowledge so it can answer. Embed the widget so customers can reach it.
          </p>
        </div>

        <div className="space-y-px bg-line border border-line">
          <Step
            num="01"
            title="Connect a backend"
            blurb="Stripe to refund, Shopify to replace, Zendesk to close tickets — pick at least one."
            icon={<Plug size={16} />}
            done={hasIntegration}
            doneLabel={hasIntegration ? `${integrations.length} connected (${integrations.map((i) => i.kind).join(", ")})` : ""}
          >
            <div className="flex flex-wrap gap-2">
              {(["stripe", "shopify", "zendesk", "generic_webhook"] as Kind[]).map((k) => {
                const connected = integrations.some((i) => i.kind === k);
                return (
                  <button
                    key={k}
                    onClick={() => setOpenModal(k)}
                    className={
                      "h-9 px-3 text-[13px] border transition inline-flex items-center gap-2 " +
                      (connected
                        ? "border-success text-success bg-paper"
                        : "border-ink text-ink hover:bg-ink hover:text-paper")
                    }
                  >
                    {connected && <Check size={13} />}
                    {labelOf(k)}
                  </button>
                );
              })}
              <Link href="/integrations" className="h-9 px-3 text-[13px] text-ink-2 hover:text-blue inline-flex items-center">
                See all →
              </Link>
            </div>
          </Step>

          <Step
            num="02"
            title="Drop in your knowledge base"
            blurb="Returns policy, shipping FAQs, troubleshooting. Markdown or plain text. Chunked + embedded in seconds."
            icon={<Database size={16} />}
            done={hasKb}
            doneLabel={hasKb ? `${sources.length} sources indexed` : ""}
          >
            <div className="flex flex-wrap gap-2">
              <Link href="/kb" className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue inline-flex items-center gap-1.5">
                <Database size={13} /> Upload sources
              </Link>
              {hasKb && <span className="text-[12.5px] text-ink-2 self-center">{sources.length} ready</span>}
            </div>
          </Step>

          <Step
            num="03"
            title="Embed the widget"
            blurb="One script tag on your site. Customers chat, the operator acts."
            icon={<Code2 size={16} />}
            done={!!pubKey && hasIntegration && hasKb}
            doneLabel={pubKey ? "publishable key issued" : ""}
          >
            {!pubKey ? (
              <button
                onClick={ensurePubKey}
                disabled={busy}
                className="h-9 px-3 bg-ink text-paper text-[13px] hover:bg-blue disabled:opacity-50 inline-flex items-center gap-1.5"
              >
                {busy ? "Generating…" : "Generate publishable key"}
              </button>
            ) : (
              <div className="space-y-3">
                <pre className="font-mono text-[12.5px] bg-ink text-paper p-4 overflow-auto border border-ink">
{`<script>
  (function () {
    var s = document.createElement("script");
    s.src = "${typeof window !== "undefined" ? window.location.origin : ""}/widget.js";
    s.async = 1;
    s.dataset.tenant = "${tenantSlug}";
    s.dataset.publishableKey = "${pubKey}";
    document.head.appendChild(s);
  })();
</script>`}
                </pre>
                <div className="flex items-center gap-2">
                  <Link
                    href={`/c/${tenantSlug}?pk=${pubKey}`}
                    target="_blank"
                    className="h-9 px-3 border border-ink text-[13px] inline-flex items-center gap-1.5 hover:bg-ink hover:text-paper"
                  >
                    Try hosted chat →
                  </Link>
                  <Link href="/install" className="text-[13px] text-ink-2 hover:text-blue">
                    Full install guide →
                  </Link>
                </div>
              </div>
            )}
          </Step>
        </div>

        <div className="mt-10 flex items-center justify-end gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="h-11 px-5 bg-ink text-paper text-[14px] inline-flex items-center gap-2 hover:bg-blue"
          >
            Go to dashboard <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {openModal && (
        <ConnectIntegrationModal
          kind={openModal}
          onClose={() => setOpenModal(null)}
          onDone={() => { setOpenModal(null); refresh(); }}
        />
      )}
    </>
  );
}

function Step({
  num,
  title,
  blurb,
  icon,
  done,
  doneLabel,
  children
}: {
  num: string;
  title: string;
  blurb: string;
  icon: React.ReactNode;
  done?: boolean;
  doneLabel?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-paper p-6 grid lg:grid-cols-12 gap-6 items-start">
      <div className="lg:col-span-4 flex items-start gap-4">
        <div className={"w-9 h-9 border flex items-center justify-center font-display italic text-[18px] " + (done ? "border-success text-success" : "border-ink text-ink")}>
          {done ? <Check size={16} /> : num}
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-blue">{icon}</span>
            <h3 className="font-display text-[22px] tracking-tightest leading-tight">{title}</h3>
          </div>
          <p className="text-ink-2 text-[13.5px] leading-[1.55] max-w-sm">{blurb}</p>
          {done && doneLabel && (
            <div className="mt-2 font-mono text-[11px] uppercase tracking-widest text-success">{doneLabel}</div>
          )}
        </div>
      </div>
      <div className="lg:col-span-8 lg:pl-6">{children}</div>
    </div>
  );
}

function labelOf(k: Kind) {
  return { stripe: "Stripe", shopify: "Shopify", zendesk: "Zendesk", generic_webhook: "Webhook" }[k];
}
