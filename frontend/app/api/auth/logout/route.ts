import { NextRequest, NextResponse } from "next/server";

function clear(res: NextResponse) {
  res.cookies.set("rsv_session", "", { httpOnly: true, path: "/", maxAge: 0 });
  return res;
}

// Form POST: redirect to landing
export async function POST(req: NextRequest) {
  return clear(NextResponse.redirect(new URL("/", req.url), { status: 303 }));
}

// fetch() POST: JSON response
export async function GET(req: NextRequest) {
  return clear(NextResponse.redirect(new URL("/", req.url), { status: 303 }));
}
