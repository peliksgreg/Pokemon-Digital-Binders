// Service worker: makes the binder work offline once it has been opened
// over http(s) (e.g. GitHub Pages). Not used when opened as a local file.
const SHELL = "binder-shell-v3";
const IMAGES = "binder-images-v1";
const API = "binder-api-v1";
const SHELL_FILES = ["./", "index.html", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];
const MAX_IMAGES = 600;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  const keep = new Set([SHELL, IMAGES, API]);
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function trim(cacheName, max) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

// Card images never change: serve from cache, fetch once.
async function cacheFirst(req) {
  const cache = await caches.open(IMAGES);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === "opaque") {
    cache.put(req, res.clone());
    trim(IMAGES, MAX_IMAGES);
  }
  return res;
}

// App shell and API: try the network, fall back to the last good copy.
async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(req, { ignoreSearch: cacheName === SHELL });
    if (hit) return hit;
    throw err;
  }
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    e.respondWith(networkFirst(req, SHELL));
  } else if (["cdn.artofpkm.com", "assets.tcgdex.net", "images.pokemontcg.io", "images.scrydex.com"].includes(url.hostname)) {
    e.respondWith(cacheFirst(req));
  } else if (url.hostname === "api.tcgdex.net" || url.hostname === "api.pokemontcg.io") {
    e.respondWith(networkFirst(req, API));
  }
});
