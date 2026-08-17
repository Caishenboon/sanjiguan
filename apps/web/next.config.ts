import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  transpilePackages: ["@sanji/ui"],
  async headers(){
    const privateHeaders=[
      {key:"Cache-Control",value:"private, no-store, max-age=0"},
      {key:"X-Robots-Tag",value:"noindex, nofollow, noarchive"},
    ];
    return ["/api/:path*","/admin/:path*","/me/:path*","/profile/:path*","/chronicle/:path*","/records/:path*","/consult/:path*","/results/:path*","/onboarding","/start"].map(source=>({source,headers:privateHeaders}));
  },
};

export default nextConfig;
