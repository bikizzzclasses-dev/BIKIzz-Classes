const CACHE_NAME = "bikizz-pwa-v1";
const STATIC_ASSETS = [
  "/",
  "/login",
  "/register",
  "/static/style.css",
  "/static/auth.css",
  "/static/dashboard.css",
  "/static/script.js",
  "/static/images/logo.png",
  "/static/images/pwa-icon-192.png",
  "/static/images/pwa-icon-512.png",
  "/static/images/math-hero-3d.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) {
            return key !== CACHE_NAME;
          })
          .map(function (key) {
            return caches.delete(key);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(function () {
        return caches.match("/");
      })
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(function (cachedResponse) {
      return (
        cachedResponse ||
        fetch(request).then(function (response) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(request, responseClone);
          });
          return response;
        })
      );
    })
  );
});
