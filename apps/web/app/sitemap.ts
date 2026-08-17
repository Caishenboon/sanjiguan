import type { MetadataRoute } from "next";

export default function sitemap():MetadataRoute.Sitemap{
  const origin=process.env.PUBLIC_ORIGIN||"http://127.0.0.1:3000";
  return [
    {url:`${origin}/`,changeFrequency:"weekly",priority:1},
    {url:`${origin}/about`,changeFrequency:"monthly",priority:.7},
  ];
}
