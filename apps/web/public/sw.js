/* Public app-shell cache only. Never cache API or personal routes. */
const CACHE="sanjiguan-public-shell-1.0.0-rc.1";
const PUBLIC_ASSETS=["/icon-192.svg","/icon-512.svg","/manifest.webmanifest"];
self.addEventListener("install",event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(PUBLIC_ASSETS))));
self.addEventListener("fetch",event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=="GET"||url.origin!==self.location.origin)return;
  if(url.pathname.startsWith("/api/")||url.pathname.startsWith("/profile/")||url.pathname.startsWith("/chronicle")||url.pathname.startsWith("/records")||url.pathname.startsWith("/consult")||url.pathname.startsWith("/me")||url.pathname.includes("prompt"))return;
  if(PUBLIC_ASSETS.includes(url.pathname))event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request)));
});
