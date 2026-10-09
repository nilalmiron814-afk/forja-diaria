/* Forja Diaria: red primero (las mejoras llegan solas) y caché si no hay conexión. */
const V = "forja-20261009220231";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png"];
self.addEventListener("install", e => { self.skipWaiting(); e.waitUntil(caches.open(V).then(c => c.addAll(SHELL))); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("forja-") && k !== V && k !== "forja-fonts").map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
const withTimeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]);
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (url.pathname.endsWith("version.json")) return;
    e.respondWith(withTimeout(fetch(req), 3500).then(r => {
      if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(req.mode === "navigate" ? "./index.html" : req, cp)); }
      return r;
    }).catch(() => caches.match(req.mode === "navigate" ? "./index.html" : req).then(m => m || caches.match("./index.html"))));
    return;
  }
  if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    e.respondWith(caches.open("forja-fonts").then(async c => {
      const hit = await c.match(req);
      const net = fetch(req).then(r => { if (r.ok || r.type === "opaque") c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
  }
});
