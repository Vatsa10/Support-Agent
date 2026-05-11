// Server-side fetch helper. Reads the api_key from the httpOnly cookie
// and forwards it as X-API-Key. Use inside server components / route handlers.
import { cookies } from "next/headers";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
export const COOKIE_NAME = "rsv_session";

export type Session = { api_key: string } | null;

export function getSession(): Session {
  const v = cookies().get(COOKIE_NAME)?.value;
  if (!v) return null;
  return { api_key: v };
}

export async function backendFetch<T>(
  path: string,
  init: RequestInit & { apiKey?: string } = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const key = init.apiKey ?? getSession()?.api_key;
  if (key) headers.set("X-API-Key", key);

  const res = await fetch(`${BACKEND}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 240)}`);
  }
  return res.json() as Promise<T>;
}

export async function backendFetchSafe<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    return await backendFetch<T>(path, init);
  } catch {
    return null;
  }
}
