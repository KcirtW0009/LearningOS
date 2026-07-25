// Service Worker for LearningOS
// Caches static assets for offline access and faster subsequent loads.

const CACHE_NAME = "learningos-v1";
const STATIC_ASSETS = [
  "/",
  "/_next/static/",
];

// Install: pre-cache static assets
self.addEventListener("install", (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Non-critical — assets may vary by build
      });
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener("activate", (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// Fetch: cache-first for static assets, network-first for API
self.addEventListener("fetch", (event: FetchEvent) => {
  const url = new URL(event.request.url);

  // API requests: network-first (don't cache stale data)
  if (url.pathname.startsWith("/api/") || url.hostname === "localhost" && url.port === "8000") {
    return; // Let the browser handle API requests normally
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") {
          return response;
        }

        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, clone);
        });

        return response;
      });
    })
  );
});

// TypeScript declarations for Service Worker scope
declare var self: ServiceWorkerGlobalScope;
interface ExtendableEvent extends Event {
  waitUntil(promise: Promise<any>): void;
}
interface FetchEvent extends Event {
  request: Request;
  respondWith(response: Promise<Response> | Response): void;
}
