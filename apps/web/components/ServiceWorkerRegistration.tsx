"use client";

import { useEffect, useState } from "react";

export default function ServiceWorkerRegistration() {
  const [waiting, setWaiting] = useState<ServiceWorker | null>(null);
  useEffect(() => {
    if ("serviceWorker" in navigator && window.isSecureContext) {
      let disposed = false;
      navigator.serviceWorker.register("/sw.js").then((registration) => {
        if (registration.waiting && navigator.serviceWorker.controller) setWaiting(registration.waiting);
        registration.addEventListener("updatefound", () => {
          const worker = registration.installing;
          worker?.addEventListener("statechange", () => {
            if (!disposed && worker.state === "installed" && navigator.serviceWorker.controller) {
              setWaiting(worker);
            }
          });
        });
      }).catch(() => {
        // Installation is optional; never interrupt access to the private research UI.
      });
      const reload = () => window.location.reload();
      navigator.serviceWorker.addEventListener("controllerchange", reload, { once: true });
      return () => {
        disposed = true;
        navigator.serviceWorker.removeEventListener("controllerchange", reload);
      };
    }
  }, []);
  if (!waiting) return null;
  return <aside className="pwa-update" role="status" aria-live="polite">
    <span>三际观已有新版本。更新不会缓存或上传私人资料。</span>
    <button onClick={() => waiting.postMessage({ type: "SKIP_WAITING" })}>安全更新</button>
  </aside>;
}
