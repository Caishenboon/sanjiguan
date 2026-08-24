/* Public app-shell cache only. Never cache API or personal routes. */
const CACHE="sanjiguan-public-shell-1.1.0";
const PUBLIC_ASSETS=["/offline","/icon-192.svg","/icon-512.svg","/manifest.webmanifest"];
self.addEventListener("install",event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(PUBLIC_ASSETS))));
self.addEventListener("activate",event=>event.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith("sanjiguan-public-shell-")&&key!==CACHE).map(key=>caches.delete(key))))
    .then(()=>self.clients.claim())
));
self.addEventListener("message",event=>{if(event.data?.type==="SKIP_WAITING")self.skipWaiting()});
self.addEventListener("fetch",event=>{
  const url=new URL(event.request.url);
  if(event.request.method!=="GET"||url.origin!==self.location.origin)return;
  if(url.pathname.startsWith("/api/")||url.pathname.startsWith("/profile/")||url.pathname.startsWith("/chronicle")||url.pathname.startsWith("/records")||url.pathname.startsWith("/consult")||url.pathname.startsWith("/me")||url.pathname.includes("prompt"))return;
  if(PUBLIC_ASSETS.includes(url.pathname))event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request)));
  else if(event.request.mode==="navigate")event.respondWith(fetch(event.request).catch(()=>caches.match("/offline")));
});
