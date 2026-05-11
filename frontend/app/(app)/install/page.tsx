"use client";
import { useState } from "react";
import { Topbar } from "@/components/app/Topbar";
import { Check, Copy, ExternalLink } from "lucide-react";

const TENANT_SLUG = "acme";
const PUBLISHABLE = "rsv_pub_live_4f7c8a3e9d1b";
const HOSTED_URL = `https://app.resolve.app/c/${TENANT_SLUG}`;
const WIDGET_HOST = "https://app.resolve.app";

const widgetSnippet = `<!-- Resolve. — paste before </body> on every page -->
<script>
  (function () {
    var s = document.createElement("script");
    s.src = "${WIDGET_HOST}/widget.js";
    s.async = 1;
    s.dataset.tenant = "${TENANT_SLUG}";
    s.dataset.publishableKey = "${PUBLISHABLE}";
    document.head.appendChild(s);
  })();
</script>`;

const identifySnippet = `<!-- Identity verification (recommended for logged-in users) -->
<!-- Compute user_hmac server-side: HMAC-SHA256(user_id, tenant_secret) -->
<script>
  window.ResolveSettings = {
    user_id:   "u_42",
    email:     "kira@acme.co",
    user_hmac: "{{ server-issued HMAC }}",
    context:   { order_id: "SH-29481", plan: "pro" }
  };
</script>`;

const sdkSnippet = `// Open the widget programmatically (e.g. from your "Get help" button)
Resolve('open', {
  context: { order_id: 'SH-29481', amount: 48.20 }
});

// Listen for resolution events (refunds, replacements, etc.)
Resolve('on', 'resolved', function (payload) {
  // analytics, banners, etc.
});`;

const headlessSnippet = `# Headless API — for fully custom UIs
curl -X POST https://api.resolve.app/api/chat \\
  -H "X-API-Key: rsv_live_…" \\
  -H "X-End-User-JWT: \${JWT}" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "I need a refund for SH-29481", "user_id": "u_42"}'`;

export default function InstallPage() {
  return (
    <>
      <Topbar crumb={[{ label: "Configure" }, { label: "Install" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="mb-8">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Three surfaces, one engine</div>
          <h1 className="font-display text-[40px] leading-[1] tracking-tightest">
            Put Resolve where your <span className="italic text-blue">customers&nbsp;are.</span>
          </h1>
          <p className="text-ink-2 text-[14.5px] mt-3 max-w-xl">
            Most teams start with the widget, send the hosted URL in transactional emails, and add
            in-product SDK calls on order/account pages as they scale.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-10">
          <SurfaceCard
            num="01"
            title="Site widget"
            blurb="Floating launcher, drop-in script tag. Best baseline — works on any page."
            best
          />
          <SurfaceCard
            num="02"
            title="Hosted page"
            blurb="A shareable URL. Perfect for email signatures, QR codes, in-app deep links."
          />
          <SurfaceCard
            num="03"
            title="In-product SDK"
            blurb="Open the widget pre-loaded with context. Refund buttons next to orders."
          />
        </div>

        {/* 1. Widget */}
        <Block
          tag="01 · widget"
          title="Embed the launcher"
          body="One script tag, no build step. The widget lazy-loads on first open and respects your site's CSP."
        >
          <Code text={widgetSnippet} />
          <div className="mt-3">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Identify your users</div>
            <Code text={identifySnippet} />
          </div>
          <div className="mt-3">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Open with context (SDK)</div>
            <Code text={sdkSnippet} lang="javascript" />
          </div>
        </Block>

        {/* 2. Hosted */}
        <Block
          tag="02 · hosted"
          title="A URL you can send"
          body="Share in receipts, password resets, status pages. Same operator, no install required."
        >
          <div className="border border-line bg-paper p-5 flex items-center justify-between gap-4">
            <div className="font-mono text-[14px] text-ink truncate">{HOSTED_URL}</div>
            <div className="flex items-center gap-2 shrink-0">
              <CopyBtn text={HOSTED_URL} />
              <a
                href={`/c/${TENANT_SLUG}`}
                target="_blank"
                className="h-9 px-3 border border-ink text-[13px] inline-flex items-center gap-1.5 hover:bg-ink hover:text-paper"
              >
                Open <ExternalLink size={13} />
              </a>
            </div>
          </div>
          <p className="text-[12.5px] text-ink-3 mt-3 font-mono">
            CNAME support.your-domain.com → resolve.app for a custom domain.
          </p>
        </Block>

        {/* 3. Headless */}
        <Block
          tag="03 · headless"
          title="Roll your own UI"
          body="Already have a chat surface? Talk to the same operator from any client. Same audit, same policies."
        >
          <Code text={headlessSnippet} lang="bash" />
          <a
            href="/docs/api"
            className="mt-3 inline-flex items-center gap-1 text-[13px] text-ink-2 hover:text-blue"
          >
            Full API reference <ExternalLink size={12} />
          </a>
        </Block>

        <div className="border border-line border-dashed bg-paper p-6 mt-2">
          <div className="font-display text-[22px] tracking-tightest">Identity verification</div>
          <p className="text-ink-2 text-[13.5px] mt-2 max-w-2xl leading-[1.6]">
            For production, sign the end-user's <span className="font-mono text-ink">user_id</span> server-side with your tenant
            secret using HMAC-SHA256. The widget passes it through as <span className="font-mono text-ink">X-End-User-JWT</span>;
            actions get attributed correctly and rate-limited per real user. Without it, sessions are treated as anonymous.
          </p>
        </div>
      </div>
    </>
  );
}

function SurfaceCard({ num, title, blurb, best }: { num: string; title: string; blurb: string; best?: boolean }) {
  return (
    <div className={"p-6 border border-line " + (best ? "bg-ink text-paper" : "bg-paper")}>
      <div className="flex items-center justify-between">
        <span className={"font-display italic text-[26px] leading-none " + (best ? "text-blue" : "text-blue")}>
          {num}
        </span>
        {best && <span className="font-mono text-[10.5px] uppercase tracking-widest text-blue">recommended</span>}
      </div>
      <div className="mt-6 font-display text-[26px] leading-tight tracking-tightest">{title}</div>
      <p className={"mt-2 text-[13.5px] leading-[1.55] " + (best ? "text-paper/70" : "text-ink-2")}>{blurb}</p>
    </div>
  );
}

function Block({ tag, title, body, children }: { tag: string; title: string; body: string; children: React.ReactNode }) {
  return (
    <section className="mt-2 mb-10">
      <div className="border-t border-line pt-8 mb-5 grid lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-4">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{tag}</div>
          <h2 className="font-display text-[28px] leading-[1.05] tracking-tightest">{title}</h2>
          <p className="text-ink-2 text-[13.5px] mt-2 leading-[1.55] max-w-md">{body}</p>
        </div>
        <div className="lg:col-span-8">{children}</div>
      </div>
    </section>
  );
}

function Code({ text, lang = "html" }: { text: string; lang?: string }) {
  return (
    <div className="relative border border-line bg-ink text-paper">
      <div className="flex items-center justify-between px-4 h-9 border-b border-paper/10 text-[11px] uppercase tracking-widest font-mono text-paper/60">
        <span>{lang}</span>
        <CopyBtn text={text} dark />
      </div>
      <pre className="font-mono text-[12.5px] leading-[1.6] p-4 overflow-auto">
        <code>{text}</code>
      </pre>
    </div>
  );
}

function CopyBtn({ text, dark }: { text: string; dark?: boolean }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1400); }}
      className={
        "inline-flex items-center gap-1.5 h-7 px-2 text-[11.5px] transition " +
        (dark
          ? "text-paper/70 hover:text-paper border border-paper/10 hover:border-paper/30"
          : "border border-line hover:border-ink")
      }
    >
      {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
    </button>
  );
}
