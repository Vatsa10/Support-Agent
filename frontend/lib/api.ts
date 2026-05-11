// Typed fetch wrappers. In dev, proxied via next.config rewrites to FastAPI.
const BASE = "/api/backend";

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {})
    },
    cache: "no-store"
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  chat: (apiKey: string, body: { message: string; user_id: string; thread_id?: string }) =>
    req<any>("/api/chat", {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: JSON.stringify(body)
    }),
  tenant: {
    integrations: (apiKey: string) =>
      req<any[]>("/tenant/integrations", { headers: { "X-API-Key": apiKey } }),
    policies: (apiKey: string) =>
      req<any[]>("/tenant/policies", { headers: { "X-API-Key": apiKey } }),
    approvals: (apiKey: string) =>
      req<any[]>("/tenant/approvals", { headers: { "X-API-Key": apiKey } }),
    billing: (apiKey: string) =>
      req<any>("/tenant/billing", { headers: { "X-API-Key": apiKey } }),
    kbSources: (apiKey: string) =>
      req<any[]>("/tenant/kb/sources", { headers: { "X-API-Key": apiKey } })
  }
};
