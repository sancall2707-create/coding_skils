# Service Worker Security & Cache Eviction Rules for Full-Stack PWAs

## Core Security Principle

**NEVER CACHE SENSITIVE RESPONSES OR DYNAMIC API ENDPOINTS IN SERVICE WORKERS.**

Caching user data, auth tokens, login pages, or API responses in a service worker introduces critical vulnerabilities:
- Stale user state displayed after logout
- Authorization bypass (cached admin pages shown to unauthenticated users)
- Leaked personal data (PII) to other users on shared devices
- Broken workflow state (cached API 404s/500s persisting across turns)
- **Mixed Content & Stale Asset Hash Mismatch**: Caching old HTML with old Vite JS/CSS hashes causes white blank screens after deployment.

---

## Service Worker Caching Strategy

| Asset Type | Strategy | Pattern | Reason |
|------------|----------|---------|--------|
| **HTML Navigation / Main Page** | **Network-First** with Cache Fallback | `event.request.mode === 'navigate'` or `/` | Always fetch fresh HTML with current Vite JS/CSS asset hashes |
| **Vite Build Assets** (.js, .css) | **Cache-First** with Network Fallback | `/build/assets/*` | Immutable hashed filenames, safe & performant |
| **Public Assets** (manifest, icons, favicon) | **Cache-First** | `public/manifest.json`, `public/icons/*` | Static metadata |
| **API Endpoints** | **Network Only** | `/api/*` | Real-time data & security enforcement |
| **Auth Pages** | **Network Only** | `/login`, `/register` | Security, prevent token leakage |
| **Admin & User Data Routes** | **Network Only** | `/admin/*`, `/booking/*` | Role-based authorization guard |

---

## Production-Grade Implementation (`sw.js`)

```javascript
const CACHE_NAME = 'pwa-app-v3';

// Only pre-cache static, immutable public assets
const PUBLIC_STATIC_ASSETS = [
  '/manifest.json',
  '/favicon.ico',
  '/icons/icon-512.svg',
];

// Install: Pre-cache static assets & skip waiting immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PUBLIC_STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate: Clean ALL old cache versions immediately & claim clients
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('🧹 Evicting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Route-based handling
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. SECURITY RULE: NETWORK ONLY FOR API & SENSITIVE ROUTES
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.includes('/login') ||
    url.pathname.includes('/register') ||
    url.pathname.includes('/booking') ||
    url.pathname.includes('/admin') ||
    event.request.method !== 'GET'
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // 2. HTML NAVIGATION (Root / or SPA navigation): NETWORK-FIRST
  // Guarantees browser receives fresh HTML with latest Vite asset hashes
  if (event.request.mode === 'navigate' || url.pathname === '/') {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // 3. VITE BUILD HASHED ASSETS (/build/assets/*): CACHE-FIRST
  if (url.pathname.startsWith('/build/assets/')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Default: Network First
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
```

---

## Service Worker Registration Pattern (`welcome.blade.php`)

To ensure Service Worker updates take effect immediately on new deployments:

```html
<script>
  if ('serviceWorker' in navigator) {
    // Append version query parameter to bypass HTTP browser cache for sw.js itself
    const swVersion = '1';
    navigator.serviceWorker.register(`/sw.js?v=${swVersion}`)
      .then((registration) => {
        console.log('✅ ServiceWorker registered:', registration.scope);
        // Force update check on page load
        registration.update().catch(err => console.warn('SW update check failed:', err));
      })
      .catch((error) => {
        console.error('❌ ServiceWorker registration failed:', error);
      });
  }
</script>
```

---

## Verification Commands

```bash
# Check service worker content for dangerous cache patterns
grep -E "cache\.put|fetch" public/sw.js

# Ensure manifest and sw.js have correct permissions
chmod 644 public/manifest.json public/sw.js
```