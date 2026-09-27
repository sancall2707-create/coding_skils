# PWA Deployment Patterns & Caddy + Cloudflare Configuration

## Problem: Redirect Loop (HTTPS Cascade)

When combining **Caddy with internal TLS** + **Cloudflare Quick Tunnel**, browser sees infinite redirects:
```
HTTP/1.1 308 Permanent Redirect
Location: https://...
→ HTTPS connection to Cloudflare Tunnel (which is already HTTPS)
→ Caddy sees HTTP from Tunnel, redirects to HTTPS
→ Back to Cloudflare → Loop
```

**Error in browser**: `ERR_TOO_MANY_REDIRECTS` (Brave, Chrome, Safari)

## Solution: Remove Caddy Internal TLS When Using Tunnel

### Stage 1: Local Testing (No Tunnel)
```caddyfile
:80 {
    root * /home/ubuntu/pwa-peminjaman-fasilitas/app/public
    encode gzip
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```
Access: `http://localhost`

### Stage 2: Public HTTPS via Cloudflare Quick Tunnel
```caddyfile
:80 {
    root * /home/ubuntu/pwa-peminjaman-fasilitas/app/public
    encode gzip
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```
**Then run in background:**
```bash
cloudflared tunnel --url http://127.0.0.1:80
```
Access: `https://assuming-favors-merge-establish.trycloudflare.com` (instant HTTPS, no credentials needed)

**Why it works**: Cloudflare Tunnel terminates HTTPS at its edge; Caddy only sees HTTP from localhost. No redirect loop.

### Stage 3: Production HTTPS (Domain + Let's Encrypt)
```caddyfile
peminjaman.pangudiluhur.sch.id {
    root * /home/ubuntu/pwa-peminjaman-fasilitas/app/public
    encode gzip
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```
Caddy auto-provisions Let's Encrypt cert.

---

## File Permissions Pitfall

**After creating/modifying PWA assets**, ensure correct permissions:
```bash
chmod 644 public/manifest.json public/sw.js
chmod 644 public/icons/icon-512.svg
```

**Why**: If manifest or sw.js have restrictive permissions (e.g., `600` or `-rw-------`), Caddy (running as user or www-data) may fail to serve them with HTTP 403 Forbidden, causing PWA install banner not to appear.

---

## Service Worker Caching: Explicit Exclusion Rules

Security-critical: Service Worker must **NOT cache**:
- `/api/*` endpoints (authentication tokens, user data)
- `/login`, `/register`, `/logout` routes
- `/booking*`, `/admin*` pages (sensitive operations)
- Any POST/PATCH/DELETE request

**Implementation** (in `public/sw.js`):
```javascript
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network Only for sensitive routes & methods
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.includes('login') ||
    url.pathname.includes('register') ||
    url.pathname.includes('booking') ||
    url.pathname.includes('admin') ||
    event.request.method !== 'GET'
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Cache First for static assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request).then((networkResponse) => {
        // Only cache successful static responses
        if (networkResponse && networkResponse.status === 200 &&
            (url.pathname.endsWith('.js') || url.pathname.endsWith('.css') ||
             url.pathname.endsWith('.png') || url.pathname.endsWith('.svg'))) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      });
    })
  );
});
```

**Verification**: Open DevTools → Application → Cache Storage → Inspect. Should contain ONLY:
- `app-*.css`
- `app-*.js`
- `icon-512.svg`
- `manifest.json`
- `favicon.ico`

Should NOT contain any `/api/` responses or `/login` HTML.
