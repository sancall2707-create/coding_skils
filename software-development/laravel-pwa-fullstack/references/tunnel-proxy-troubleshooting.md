# Reverse Proxy, Cloudflare Tunnel, HTTPS & SPA Routing Troubleshooting

## Overview
When deploying a Laravel + Vue 3 SPA + PWA behind Cloudflare Tunnel or a reverse proxy (Caddy, Nginx), several configuration layers must align to prevent:
1. `ERR_TOO_MANY_REDIRECTS` (Redirect loops)
2. `Mixed Content` Errors (HTTPS page requesting HTTP Vite assets)
3. `404 Not Found` on SPA route reloads (`/login`, `/vehicles`, `/bookings`)

---

## 1. Preventing HTTP-HTTPS Redirect Loops (`ERR_TOO_MANY_REDIRECTS`)

### Cause
Cloudflare Tunnel handles SSL termination at the edge (HTTPS) and forwards requests to Caddy on HTTP port 80. If Caddy is configured with `tls internal` or forces HTTPS redirects (`:443`), Caddy sends an HTTP 308 redirect back to Cloudflare, causing an infinite loop.

### Fix: Caddyfile Configuration
Ensure Caddy listens explicitly on port 80 (`:80`) without TLS directives when behind a tunnel:

```caddyfile
:80 {
    root * /home/ubuntu/pwa-peminjaman-fasilitas/app/public
    encode gzip

    # SPA Fallback for static vs dynamic requests
    @notStatic {
        not file {path}
    }
    rewrite @notStatic /index.php?{query}

    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```

---

## 2. Fixing Mixed Content Errors (HTTPS Page + HTTP Assets)

### Cause
Because Caddy receives HTTP requests on port 80 internally from Cloudflare Tunnel, Laravel's request helper thinks the request is insecure (`http://`). As a result, `@vite` helper generates `http://` asset tags, which modern browsers block as mixed content on HTTPS pages.

### Fix 1: Laravel Trusted Proxies (`bootstrap/app.php`)
Instruct Laravel 11/13 to trust `X-Forwarded-Proto` and `X-Forwarded-Host` headers from proxies:

```php
// bootstrap/app.php
return Application::configure(basePath: dirname(__DIR__))
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->trustProxies(at: '*');
    })->create();
```

### Fix 2: Force HTTPS Scheme (`app/Providers/AppServiceProvider.php`)
Force HTTPS scheme in URL generator when running behind proxy/tunnel:

```php
// app/Providers/AppServiceProvider.php
use Illuminate\Support\Facades\URL;

public function boot(): void
{
    if (config('app.env') !== 'local' || request()->header('X-Forwarded-Proto') === 'https' || str_contains(config('app.url'), 'https://')) {
        URL::forceScheme('https');
    }
}
```

### Fix 3: Environment Configuration (`.env`)
```ini
APP_URL=https://your-tunnel-domain.trycloudflare.com
SANCTUM_STATEFUL_DOMAINS="your-tunnel-domain.trycloudflare.com,localhost,127.0.0.1"
```

After modifying `.env` and `AppServiceProvider.php`, run:
```bash
php artisan config:cache
php artisan route:cache
npm run build
```

---

## 3. Fixing 404 Errors on Direct SPA Route Reloads (`/login`, `/vehicles`)

### Cause
Vue Router uses HTML5 history mode (e.g., `/login`, `/admin/unit`). When a user refreshes the page directly at `/login`, the request hits Laravel web routes. If `routes/web.php` only defines `Route::get('/')`, Laravel returns a 404 Not Found error.

### Fix: Web Route Fallback (`routes/web.php`)
Add `Route::fallback()` in Laravel to serve the SPA Blade host view for any unmatched non-API web route:

```php
<?php

use Illuminate\Support\Facades\Route;

// Host SPA Blade view for root route
Route::get('/', function () {
    return view('welcome');
});

// Fallback for all SPA client-side routes (Vue Router handles rendering)
Route::fallback(function () {
    return view('welcome');
});
```

Verify with:
```bash
php artisan route:cache
curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/login  # Expected: 200
```
