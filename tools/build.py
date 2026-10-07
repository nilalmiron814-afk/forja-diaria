"""Construye la app instalable (PWA) a partir de src/app.html.

Uso:  python tools/build.py [ruta/al/app.html]
Si se pasa una ruta, primero la copia a src/app.html.
Genera index.html, sw.js y version.json en la raíz del repo.
"""
import os, re, shutil, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src", "app.html")
if len(sys.argv) > 1:
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    shutil.copyfile(sys.argv[1], SRC)

body = open(SRC, encoding="utf8").read()
body = re.sub(r'^\s*<meta charset="utf-8">\s*', "", body)
m = re.search(r"<title>(.*?)</title>\s*", body)
title = m.group(1) if m else "Forja Diaria"
body = body.replace(m.group(0), "", 1) if m else body
build = time.strftime("%Y%m%d%H%M%S")

head = f"""<!doctype html>
<html lang="es" class="pwa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="theme-color" content="#03060D">
<meta name="color-scheme" content="dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Forja">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<style>html,body{{margin:0;background:#03060D}}html{{-webkit-text-size-adjust:100%;touch-action:manipulation}}[hidden]{{display:none!important}}img{{max-width:100%}}</style>
</head>
<body>
"""

pwa = f"""
<div id="upd" hidden style="position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:90;width:max-content;max-width:calc(100% - 32px)">
  <button id="updBtn" style="font:700 .9rem Figtree,system-ui,sans-serif;color:#03101F;background:linear-gradient(90deg,#5EE1FF,#2F7BFF);border:0;border-radius:14px;padding:12px 18px;box-shadow:0 0 22px rgba(67,214,255,.5);cursor:pointer">Nueva versión disponible · Actualizar</button>
</div>
<script>
(function(){{
  "use strict";
  var BUILD = "{build}";
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(function(){{}});
  var shown = false;
  function check(){{
    fetch("version.json?t=" + Date.now(), {{cache:"no-store"}}).then(function(r){{ return r.ok ? r.json() : null; }}).then(function(v){{
      if (v && v.build && v.build !== BUILD && !shown) {{ shown = true; document.getElementById("upd").hidden = false; }}
    }}).catch(function(){{}});
  }}
  document.getElementById("updBtn").addEventListener("click", function(){{ location.reload(); }});
  document.addEventListener("visibilitychange", function(){{ if (document.visibilityState === "visible") check(); }});
  setTimeout(check, 4000);
}})();
</script>
</body>
</html>
"""

open(os.path.join(ROOT, "index.html"), "w", encoding="utf8").write(head + body + pwa)
open(os.path.join(ROOT, "version.json"), "w", encoding="utf8").write('{"build":"%s"}\n' % build)

sw = """/* Forja Diaria: red primero (las mejoras llegan solas) y caché si no hay conexión. */
const V = "forja-%s";
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
  if (/fonts\\.(googleapis|gstatic)\\.com$/.test(url.hostname)) {
    e.respondWith(caches.open("forja-fonts").then(async c => {
      const hit = await c.match(req);
      const net = fetch(req).then(r => { if (r.ok || r.type === "opaque") c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
  }
});
""" % build
open(os.path.join(ROOT, "sw.js"), "w", encoding="utf8").write(sw)
print("build", build, "->", ROOT)
