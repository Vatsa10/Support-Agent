import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
const COOKIE = "rsv_session";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const res = await fetch(`${BACKEND}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store"
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return NextResponse.json({ error: data.detail || "Signup failed" }, { status: res.status });
  }
  const r = NextResponse.json({
    tenant_id: data.tenant_id,
    tenant_name: data.tenant_name,
    user: { id: data.user_id, email: data.email, name: data.name },
    next: "/onboarding"
  });
  r.cookies.set(COOKIE, data.api_key, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30
  });
  return r;
}
