/* Keep word-list chunks in sync with the index; scope each edition's cache. */
const PREFIX = "word-atlas:" + new URL(self.registration.scope).pathname + ":";
const VERSION = PREFIX + "v2";
const SHELL = `${VERSION}-shell`;
const MEDIA = `${VERSION}-media`;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith(PREFIX) && !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

async function trim(name, max) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || req.headers.has("range")) return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  const isShell = req.mode === "navigate" || url.pathname.endsWith("/index.json") || /\/atlas\/entries\/\d+\.json$/.test(url.pathname);
  if (isShell) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) caches.open(SHELL).then((c) => c.put(req, res.clone()));
          return res;
        })
        .catch(async () => {
          const cache = await caches.open(SHELL);
          const hit = await cache.match(req) || await caches.match(req);
          return hit || (req.mode === "navigate" ? await cache.match(self.registration.scope) : undefined) || Response.error();
        }),
    );
    return;
  }
  event.respondWith(
    caches.open(/\/atlas\/(img|thumb|audio)\//.test(url.pathname) ? MEDIA : SHELL).then(async (cache) => await cache.match(req) || await caches.match(req)).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          if (res.ok && res.type === "basic") {
            const copy = res.clone();
            const name = /\/atlas\/(img|thumb|audio)\//.test(url.pathname) ? MEDIA : SHELL;
            caches.open(name).then((c) => c.put(req, copy)).then(() => name === MEDIA && trim(MEDIA, 1500));
          }
          return res;
        }),
    ),
  );
});
