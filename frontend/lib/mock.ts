// Demo data for the dashboard shell. Replace with `api` calls when wiring real backend.

export const kpis = {
  resolutions_30d: 12483,
  deflection_rate: 0.842,
  monthly_tokens: 4_213_540,
  token_cap: 6_000_000,
  approvals_pending: 7,
  action_success_rate: 0.967,
  avg_resolve_seconds: 14
};

export const sparkline = [12, 18, 22, 17, 28, 31, 27, 34, 42, 38, 51, 49, 58, 62, 71];

export const conversations = [
  { id: "c_8af31", subject: "Refund for order #SH-29481", end_user: "kira@acme.co",  status: "resolved",        action: "issue_refund",       updated: "2026-05-12T08:22:00Z" },
  { id: "c_a02e2", subject: "Subscription cancellation",  end_user: "sam@indie.dev", status: "resolved",        action: "cancel_subscription", updated: "2026-05-12T07:51:00Z" },
  { id: "c_71b09", subject: "Replace damaged order",      end_user: "rin@studio.io", status: "pending_approval",action: "replace_order",      updated: "2026-05-12T07:30:00Z" },
  { id: "c_55c12", subject: "Where is my package?",       end_user: "jay@retro.fm",  status: "resolved",        action: "knowledge_search",   updated: "2026-05-12T06:48:00Z" },
  { id: "c_31de4", subject: "Charged twice",              end_user: "nia@orb.io",    status: "escalated",       action: "create_ticket",      updated: "2026-05-12T05:11:00Z" },
  { id: "c_22f9a", subject: "Wrong size delivered",       end_user: "lev@hush.app",  status: "resolved",        action: "replace_order",      updated: "2026-05-11T23:02:00Z" }
];

export const trace = [
  { step: 1, kind: "thought",     text: "Customer requests refund for order SH-29481. Order is within 30-day window. Check return policy + customer history before issuing refund." },
  { step: 2, kind: "action",      text: "knowledge_search",   meta: { query: "refund policy 30 days" } },
  { step: 3, kind: "observation", text: "Found 3 docs. Policy: full refund within 30 days, restocking fee waived if defective." },
  { step: 4, kind: "action",      text: "classify_intent",    meta: { sentiment: "neutral", category: "returns" } },
  { step: 5, kind: "thought",     text: "Sentiment is neutral, amount $48.20 is under policy cap $100. Proceed to refund." },
  { step: 6, kind: "action",      text: "issue_refund",       meta: { charge_id: "ch_3PqW…42b", amount: 48.20 } },
  { step: 7, kind: "observation", text: "Stripe refund re_3PqW…7c1 succeeded. external_id captured. Reconciled via webhook in 4s." },
  { step: 8, kind: "response",    text: "I've issued your $48.20 refund. You'll see it in 3-5 business days. Anything else?" }
];

export const actionRuns = [
  { id: "ar_19af",  tool: "issue_refund",        status: "succeeded",         external: "re_3PqW…7c1", attempts: 1, at: "2026-05-12T08:22:00Z" },
  { id: "ar_19b0",  tool: "cancel_subscription", status: "succeeded",         external: "sub_1NA…",    attempts: 1, at: "2026-05-12T07:51:00Z" },
  { id: "ar_19b1",  tool: "replace_order",       status: "pending_approval",  external: null,           attempts: 0, at: "2026-05-12T07:30:00Z" },
  { id: "ar_19b2",  tool: "close_zendesk_ticket",status: "succeeded",         external: "tk_4823",     attempts: 1, at: "2026-05-12T06:48:00Z" },
  { id: "ar_19b3",  tool: "issue_refund",        status: "failed",            external: null,           attempts: 3, at: "2026-05-12T06:11:00Z", error: "integration_unhealthy" },
  { id: "ar_19b4",  tool: "generic_webhook_call",status: "succeeded",         external: "evt_7711",    attempts: 1, at: "2026-05-12T05:02:00Z" }
];

export const approvals = [
  {
    id: "ap_aa01",
    run_id: "ar_19b1",
    tool: "replace_order",
    args: { order_id: "SH-29553", reason: "damaged on arrival" },
    reason: "Amount $312 over approval threshold ($200)",
    created_at: "2026-05-12T07:30:00Z",
    end_user: "rin@studio.io"
  },
  {
    id: "ap_aa02",
    run_id: "ar_19b5",
    tool: "issue_refund",
    args: { charge_id: "ch_3PqW…", amount: 540 },
    reason: "Customer flagged 'frustrated' — sentiment gate",
    created_at: "2026-05-12T06:14:00Z",
    end_user: "nia@orb.io"
  }
];

export const integrations = [
  { kind: "stripe",           label: "Production",        connected: true,  status: "healthy",     usage_24h: 184 },
  { kind: "shopify",          label: "acme-store",        connected: true,  status: "healthy",     usage_24h: 92  },
  { kind: "zendesk",          label: "acme.zendesk.com",  connected: true,  status: "degraded",    usage_24h: 24  },
  { kind: "generic_webhook",  label: "Internal CRM",      connected: false, status: "disconnected",usage_24h: 0   }
];

export const policies = [
  { tool: "issue_refund",         allow: true,  max_amount: 500, requires_approval_above: 200, frequency: 3 },
  { tool: "cancel_subscription",  allow: true,  max_amount: null, requires_approval_above: null, frequency: 1 },
  { tool: "replace_order",        allow: true,  max_amount: 800, requires_approval_above: 200, frequency: 2 },
  { tool: "cancel_order",         allow: true,  max_amount: null, requires_approval_above: 500, frequency: 2 },
  { tool: "close_zendesk_ticket", allow: true,  max_amount: null, requires_approval_above: null, frequency: 20 },
  { tool: "generic_webhook_call", allow: false, max_amount: null, requires_approval_above: null, frequency: 0 }
];

export const kbSources = [
  { source: "returns-policy.md",  chunks: 24, updated: "2026-05-10T12:00:00Z" },
  { source: "shipping-faq.md",    chunks: 41, updated: "2026-05-08T09:11:00Z" },
  { source: "billing-faq.md",     chunks: 18, updated: "2026-04-30T16:42:00Z" },
  { source: "troubleshooting.md", chunks: 67, updated: "2026-04-21T14:00:00Z" }
];

export const billingSeries = Array.from({ length: 30 }).map((_, i) => ({
  day: i + 1,
  tokens: Math.round(80_000 + 50_000 * Math.sin(i / 3) + i * 1800)
}));
