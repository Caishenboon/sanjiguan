import type { NextConfig } from "next";

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  "object-src 'none'",
  "img-src 'self' data:",
  "font-src 'self' data:",
  "style-src 'self' 'unsafe-inline'",
  "script-src 'self' 'unsafe-inline'",
  "connect-src 'self'",
  "worker-src 'self'",
  "manifest-src 'self'",
].join("; ");

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: ["@sanji/ui"],
  async headers(){
    const securityHeaders=[
      {key:"Content-Security-Policy",value:contentSecurityPolicy},
      {key:"Permissions-Policy",value:"camera=(), microphone=(), geolocation=()"},
      {key:"Referrer-Policy",value:"no-referrer"},
      {key:"X-Content-Type-Options",value:"nosniff"},
      {key:"X-Frame-Options",value:"DENY"},
    ];
    const privateHeaders=[
      {key:"Cache-Control",value:"private, no-store, max-age=0"},
      {key:"X-Robots-Tag",value:"noindex, nofollow, noarchive"},
    ];
    return [
      {source:"/:path*",headers:securityHeaders},
      ...["/api/:path*","/admin/:path*","/me/:path*","/profile/:path*","/chronicle/:path*","/records/:path*","/consult/:path*","/results/:path*","/onboarding","/start"].map(source=>({source,headers:privateHeaders})),
    ];
  },
};

export default nextConfig;
