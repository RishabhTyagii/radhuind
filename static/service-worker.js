// This file intentionally REMOVES the old PWA/service-worker instead of
// running one. Devices that already installed the old service-worker.js
// will still have it running until it gets replaced - browsers check for
// a new version of this exact file periodically. This version:
//   1. Deletes every cache the old service worker created
//   2. Unregisters itself
//   3. Tells the page to reload so the browser goes back to normal
//      network requests instead of the broken cached version
//
// Once every device has picked this up (usually within a day or so of
// normal browsing), you can delete this file and its <link>/registration
// entirely - it will have done its job.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => Promise.all(cacheNames.map((name) => caches.delete(name))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll({ type: 'window' }))
      .then((clients) => {
        clients.forEach((client) => client.navigate(client.url));
      })
  );
});

// Never serve from cache - always go to the network.
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});