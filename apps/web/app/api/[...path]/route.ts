import { NextRequest, NextResponse } from "next/server";

const methods = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;
const requestIdPattern = /^[A-Za-z0-9._:-]{8,128}$/;

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const origin = process.env.SANJI_API_ORIGIN;
  const suppliedRequestId = request.headers.get("x-request-id") || "";
  const requestId = requestIdPattern.test(suppliedRequestId) ? suppliedRequestId : crypto.randomUUID();
  if (!origin) return NextResponse.json({
    detail: "api_origin_not_configured",
    error: { code: "SERVICE_UNAVAILABLE", message: "api_origin_not_configured", request_id: requestId },
  }, { status: 503, headers: { "X-Request-ID": requestId, "Cache-Control": "no-store" } });
  const { path } = await context.params;
  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, origin);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["content-type", "cookie", "idempotency-key", "x-delete-confirmation"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set("x-request-id", requestId);
  headers.set("origin", new URL(process.env.PUBLIC_ORIGIN || request.nextUrl.origin).origin);
  let response: Response;
  try {
    response = await fetch(target, {
      method: request.method,
      headers,
      body: methods.includes(request.method as typeof methods[number]) && !["GET"].includes(request.method)
        ? await request.arrayBuffer()
        : undefined,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(15_000),
    });
  } catch {
    return NextResponse.json({
      detail: "upstream_unavailable",
      error: { code: "SERVICE_UNAVAILABLE", message: "upstream_unavailable", request_id: requestId },
    }, { status: 503, headers: { "X-Request-ID": requestId, "Cache-Control": "no-store" } });
  }
  const outgoing = new Headers();
  for (const name of ["content-type", "content-disposition", "set-cookie", "x-request-id", "x-export-manifest-hash"]) {
    const value = response.headers.get(name);
    if (value) outgoing.set(name, value);
  }
  if (!outgoing.has("x-request-id")) outgoing.set("x-request-id", requestId);
  outgoing.set("cache-control", "no-store");
  return new NextResponse(response.body, { status: response.status, headers: outgoing });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
