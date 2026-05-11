import { Topbar } from "@/components/app/Topbar";
import { backendFetchSafe } from "@/lib/api-server";
import { fmtCompact } from "@/lib/fmt";

type Billing = {
  tenant_id: string;
  period: string;
  llm_input_tokens: number;
  llm_output_tokens: number;
  total_tokens: number;
};

export default async function BillingPage() {
  const b = (await backendFetchSafe<Billing>("/tenant/billing")) || {
    period: "—",
    llm_input_tokens: 0,
    llm_output_tokens: 0,
    total_tokens: 0,
    tenant_id: ""
  };

  return (
    <>
      <Topbar crumb={[{ label: "Account" }, { label: "Billing" }]} />
      <div className="px-6 lg:px-10 py-8">
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">Period {b.period}</div>
          <h1 className="font-display text-[36px] leading-[1] tracking-tightest">Billing</h1>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <Card label="Total tokens" value={fmtCompact(b.total_tokens)} hint="input + output" />
          <Card label="Input tokens" value={fmtCompact(b.llm_input_tokens)} hint="prompts to LLM" />
          <Card label="Output tokens" value={fmtCompact(b.llm_output_tokens)} hint="LLM responses" />
        </div>

        <div className="mt-8 border border-line bg-paper p-6">
          <div className="font-display text-[22px] tracking-tightest">Set monthly cap</div>
          <p className="text-ink-2 text-[13.5px] mt-1 max-w-2xl">
            Chat returns <span className="font-mono text-ink">402</span> once the cap is hit (hard cap). Resets on the 1st of each month.
          </p>
          <form action="/api/backend/tenant/budget" method="post" className="mt-4 flex items-center gap-2 max-w-md">
            <input
              name="monthly_token_cap"
              type="number"
              placeholder="6000000"
              className="flex-1 h-10 px-3 border border-line bg-paper text-[13.5px] font-mono outline-none focus:border-ink"
            />
            <button className="h-10 px-3 bg-ink text-paper text-[13px] hover:bg-blue">Apply</button>
          </form>
        </div>
      </div>
    </>
  );
}

function Card({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="border border-line bg-paper p-6">
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3">{label}</div>
      <div className="mt-3 font-display text-[44px] leading-none tracking-tightest">{value}</div>
      <div className="mt-1.5 text-[12px] text-ink-3">{hint}</div>
    </div>
  );
}
