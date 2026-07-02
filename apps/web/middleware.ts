import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";
  const hostname = host.split(":")[0].toLowerCase();
  const suffix = ".demo.chromagora.com";

  if (hostname.endsWith(suffix) && hostname !== "demo.chromagora.com") {
    const slug = hostname.slice(0, -suffix.length);
    if (slug && request.nextUrl.pathname === "/") {
      const url = request.nextUrl.clone();
      url.protocol = "http:";
      url.hostname = "127.0.0.1";
      url.port = "3011";
      url.pathname = `/demo/${slug}`;
      return NextResponse.rewrite(url);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/"],
};
