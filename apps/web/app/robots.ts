import type { MetadataRoute } from "next";

export default function robots():MetadataRoute.Robots{
  return {
    rules:{
      userAgent:"*",
      allow:["/","/about","/llms.txt","/llms-full.txt"],
      disallow:["/api/","/admin/","/me/","/profile/","/subjects/","/results/","/relationships/","/journal/","/chronicle/","/records/","/consult/","/onboarding","/start"],
    },
    sitemap:`${process.env.PUBLIC_ORIGIN||"http://127.0.0.1:3000"}/sitemap.xml`,
  };
}
