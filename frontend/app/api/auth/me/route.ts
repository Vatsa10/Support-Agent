import { NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  const key = cookies().get("rsv_session")?.value;
  if (!key) return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  const res = await fetch(`${BACKEND}/auth/me`, {
    headers: { "X-API-Key": key },
    cache: "no-store"
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
