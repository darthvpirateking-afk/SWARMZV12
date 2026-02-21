// SWARMZ Service Worker — caches the app shell for offline use on mobile
const CACHE = "swarmz-shell-v1";

// Files that make up the app shell (populated at build time by Vite)
const SHELL = ["/", "/index.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // Delete any old caches
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
      ),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Pass API and health requests straight through to the network — never cache them
  if (url.pathname.startsWith("/v1") || url.pathname.startsWith("/health")) {
    return; // falls through to default browser network fetch
  }

  // Cache-first for everything else (the app shell)
  event.respondWith(
    caches.match(event.request).then(
      (cached) => cached ?? fetch(event.request),
    ),
  );
});
