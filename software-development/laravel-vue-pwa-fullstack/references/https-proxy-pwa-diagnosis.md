# HTTPS Proxy & PWA: Diagnosis & Fixes

When deploying Laravel PWA behind reverse proxies (Cloudflare Tunnel, nginx, etc.) with HTTPS upstream and HTTP backend, several gotchas cause blank pages or redirect loops. This reference captures diagnostic methodology and fixes.

---

## 1. SYMPTOM: Blank Page (HTTP 200 But No App Render)

**What appears**: Browser loads page, but all content is white/blank. No errors in JavaScript console initially, but Network tab shows asset 404s or mixed-content blocks.

### Root Cause Pattern

**Mixed Content**: HTTPS page trying to load HTTP assets.

```
User browser (HTTPS) ←→ Cloudflare Tunnel (HTTPS) ←→ Caddy/nginx (HTTP) ←→ PHP
```

When Laravel receives HTTP request from Caddy but user accessed via HTTPS through tunnel:
- Laravel's `URL::asset()` calls still use request scheme (HTTP)
- Generated URLs: `http://cdn.example.com/app.js` inside `https://` page
- Browser blocks (CSP/security policy) → assets 404 or mixed-content error
- Vue app never loads because JS didn't load

### Diagnosis Checklist

1. **Fetch page HTML, check asset URLs:**
   ```bash
   curl -s https://your-domain.trycloudflare.com | grep -E 'href=|src=' | grep -E 'app\.(css|js)|build/'
   ```
   - **Expect**: All URLs `https://` or relative `/build/...`
   - **Bad**: Mix of `http://` and `https://`

2. **Test individual asset load:**
   ```bash
   curl -I https://your-domain.trycloudflare.com/build/assets/app-XYZ.js
   ```
   - **Expect**: `HTTP/2 200`
   - **Bad**: `HTTP/2 404` or `HTTP 403 Forbidden`

3. **Check HTML DOM:**
   ```bash
   curl -s https://your-domain.trycloudflare.com | grep -o '<div id="app"></div>'
   ```
   - **Expect**: Div exists (Vue entry point)
   - **Bad**: Missing or malformed

---

## 2. FIX: Force HTTPS Scheme in Laravel

### Cause in Code

**`.env` file still has dev default:**
```
APP_URL=http://localhost
```

**Laravel `URL::asset()` reads request scheme, not APP_URL** when making URLs. Request scheme from reverse proxy is HTTP (because backend is HTTP), so it generates `http://...` URLs.

### Three-Part Fix

#### Part A: Update APP_URL in `.env`
```bash
APP_URL=https://your-domain.trycloudflare.com
```

#### Part B: Add Trusted Proxies (`bootstrap/app.php`)
```php
->withMiddleware(function (Middleware $middleware) {
    // Trust reverse proxy headers (X-Forwarded-Proto, etc.)
    $middleware->trustProxies(at: '*');
})
```

This tells Laravel to read `X-Forwarded-Proto: https` header from Cloudflare/nginx.

#### Part C: Force HTTPS URL Scheme (`app/Providers/AppServiceProvider.php`)
```php
use Illuminate\Support\Facades\URL;

public function boot(): void {
    // When APP_URL is HTTPS or request is from trusted proxy
    if (config('app.env') !== 'local' || 
        request()->header('X-Forwarded-Proto') === 'https' || 
        str_contains(config('app.url'), 'https://')) {
        URL::forceScheme('https');
    }
}
```

#### Part D: Clear Config Cache
```bash
php artisan config:cache
php artisan view:clear
php artisan route:cache
```

### Verification After Fix

```bash
# Rebuild frontend assets with new APP_URL
npm run build

# Check HTML again
curl -s https://your-domain.trycloudflare.com | grep 'href=\|src=' | grep 'app.'
# Expect: https://your-domain.trycloudflare.com/build/assets/app-XXX.js
#         https://your-domain.trycloudflare.com/build/assets/app-XXX.css
```

---

## 3. SYMPTOM: Redirect Loop (HTTP ↔ HTTPS)

**What appears**: Browser shows `ERR_TOO_MANY_REDIRECTS`. Response chain is HTTP 301/308 → HTTPS 301/308 → HTTP ... (loop).

### Root Cause

**Caddy (or web server) forcing HTTPS internally** while reverse proxy already handles HTTPS:

```
browser (HTTPS) ←→ Cloudflare (HTTPS, expects HTTP backend) ←→ Caddy (forced HTTPS, redirects back)
```

**Bad Caddyfile:**
```caddy
:80, :443 {
    tls internal  # ← Forces all requests to HTTPS
    php_fastcgi ...
}
```

When Tunnel sends HTTP request to `:80`, Caddy redirects to HTTPS on `:443`, which doesn't exist from tunnel's perspective, causing a loop.

### Fix: Pure HTTP Backend

**Correct Caddyfile:**
```caddy
:80 {
    root * /path/to/public
    encode gzip
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```

Let the **reverse proxy handle HTTPS** (upstream), not the backend server.

---

## 4. Cloudflare Tunnel Quick Setup for PWA Testing

When testing PWA features that require HTTPS (Web App Manifest, Service Worker, installation), use **Cloudflare Quick Tunnel**:

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Start tunnel pointing to local HTTP backend
cloudflared tunnel --url http://127.0.0.1:80

# Output will show:
# https://assuming-favors-merge-establish.trycloudflare.com
```

**Advantages:**
- Instant HTTPS (no Let's Encrypt, no domain)
- Perfect for PWA testing (manifest, SW, install banner all require HTTPS)
- No DNS changes needed
- Temporary (tunnel ID changes on restart, OK for testing)

**Limitations:**
- Domain changes each tunnel restart (don't hardcode)
- Temporary (not for production long-term)
- Rate-limited (100 reqs/min for quick tunnels)

---

## 5. Testing Checklist: Real Diagnosis vs False Negatives

**Just because `curl -I https://... ` returns 200 does NOT mean the app works.** Real validation requires:

- [ ] Fetch full HTML, verify asset URLs are HTTPS/relative (not HTTP)
- [ ] Fetch individual CSS/JS files, verify HTTP/2 200 (not 404/403/mixed-content block)
- [ ] Check `<div id="app"></div>` exists in HTML
- [ ] Check Service Worker script loads (`curl -I /sw.js` → 200)
- [ ] Check manifest loads (`curl /manifest.json` → valid JSON, displays at all)
- [ ] Browser Dev Tools Network tab shows no 404s for static assets
- [ ] Browser Console shows no JavaScript errors or mixed-content warnings
- [ ] Vue app actually mounts (`#app` div gets populated, not stays empty)
- [ ] Test from **different device/private tab** (not cached browser data)

---

## 6. Session-Specific Lessons (Sept 2026)

**Scenario**: Laravel PWA behind Cloudflare Tunnel for public testing.

**Problem flow:**
1. Fresh deploy, tunnel created → app returns HTTP 200
2. User opens URL in phone browser → blank page
3. Developer checks `curl -I` → sees 200, assumes OK
4. Investigation found: HTML contains `http://` asset URLs inside `https://` page
5. Browser blocked mixed content silently

**Fix applied:**
1. Updated `.env` APP_URL to `https://`
2. Added `trustProxies(at: '*')` in `bootstrap/app.php`
3. Added `URL::forceScheme('https')` in AppServiceProvider
4. Ran config cache, view clear, route cache
5. Verification: curl showed `https://` URLs in HTML
6. Test: app rendered in browser

**Time spent on diagnosis**: 20 mins (curl checks + AppServiceProvider pattern known)
**Key win**: Diagnosis methodology (don't trust HTTP 200 alone; validate asset URLs + DOM readiness)
