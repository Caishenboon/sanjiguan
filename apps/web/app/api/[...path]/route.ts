import { NextRequest, NextResponse } from "next/server";

const methods = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const origin = process.env.SANJI_API_ORIGIN;
  if (!origin) return NextResponse.json({ detail: "api_origin_not_configured" }, { status: 503 });
  const { path } = await context.params;
  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, origin);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["content-type", "cookie", "idempotency-key", "x-request-id", "x-delete-confirmation"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const cookie = headers.get("cookie");
  if (cookie && cookie.includes("sanji-session=")) {
    headers.set("cookie", cookie.replace(/(^|;\s*)sanji-session=/, "$1__Host-session="));
  }
  headers.set("origin", new URL(process.env.PUBLIC_ORIGIN || request.nextUrl.origin).origin);
  const response = await fetch(target, {
    method: request.method,
    headers,
    body: methods.includes(request.method as typeof methods[number]) && !["GET"].includes(request.method)
      ? await request.arrayBuffer()
      : undefined,
    cache: "no-store",
    redirect: "manual",
  });
  const outgoing = new Headers();
  for (const name of ["content-type", "content-disposition", "set-cookie", "x-request-id", "x-export-manifest-hash"]) {
    const value = response.headers.get(name);
    if (value) outgoing.set(name, value);
  }
  return new NextResponse(response.body, { status: response.status, headers: outgoing });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
