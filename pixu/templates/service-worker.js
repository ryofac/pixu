/*
 * Pixu remains an online application. This worker only supplies the
 * registration required for installation; it never caches account data,
 * charge pages, forms, or payment information.
 */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", (event) => {
  if (event.request.method === "GET") {
    event.respondWith(fetch(event.request));
  }
});
