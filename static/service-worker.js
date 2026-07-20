const CACHE_NAME = 'radhu-stock-cache-v1';
const urlsToCache = [
  '/', // Home page
//   '/static/css/base.css',
//   '/static/css/footer.css',
  '/static/icon/radhulogo.png',
];

// Install event: cache static assets
self.addEventListener('install', function(e) {
  console.log('Service Worker: Installed');
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Activate event: cleanup old caches
self.addEventListener('activate', function(e) {
  console.log('Service Worker: Activated');
  e.waitUntil(
    caches.keys().then(cacheNames =>
      Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
                  .map(name => caches.delete(name))
      )
    )
  );
  self.clients.claim();
});

// Fetch event: serve from cache first
self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request)
      .then(response => response || fetch(e.request))
      .catch(() => {
        // Offline fallback (optional)
        if (e.request.destination === 'document') return caches.match('/');
      })
  );
});