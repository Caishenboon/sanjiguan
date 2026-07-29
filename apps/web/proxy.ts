import { NextRequest, NextResponse } from "next/server";

export async function proxy(request: NextRequest) {
  // Browser tests have no API process. The bypass is explicit, process-local,
  // and unavailable unless the test runner sets the environment flag.
  if (
    process.env.SANJI_RESEARCH_UI_TEST_MODE === "1"
    && request.headers.get("x-sanji-test-role") === "research_admin"
  ) {
    return NextResponse.next();
  }

  const apiOrigin = process.env.SANJI_API_ORIGIN;
  if (apiOrigin) {
    try {
      const response = await fetch(new URL("/api/v1/me", apiOrigin), {
        headers: { cookie: request.headers.get("cookie") || "" },
        cache: "no-store",
      });
      if (response.ok) {
        const session = await response.json();
        if (session.role === "owner" || session.role === "research_admin") {
          return NextResponse.next();
        }
      }
    } catch {
      // Fail closed. The permission page contains a safe retry path.
    }
  }
  return NextResponse.redirect(new URL("/forbidden", request.url));
}

export const config = { matcher: ["/admin/:path*"] };
