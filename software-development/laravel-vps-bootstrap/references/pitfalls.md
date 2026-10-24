# Common Pitfalls & Solutions in Laravel VPS Bootstrap

This reference documents common issues encountered when setting up Laravel on an Ubuntu VPS with Caddy and PHP-FPM, along with tested fixes.

---

## 1. `tempnam(): file created in system's temporary directory` (500 Error)

### Symptom
When visiting the site via HTTP, Caddy returns an HTTP 500 error page with text:
`tempnam(): file created in the system's temporary directory (500 Internal Server Error)`

### Root Cause
Laravel attempts to write temporary view/blade files to `storage/framework/views` or cache files to `storage/framework/cache`, but the web server process (run as `www-data` or `caddy`) lacks write permissions to those subdirectories.

### Fix
```bash
cd /path/to/laravel/app
mkdir -p storage/logs storage/framework/cache storage/framework/sessions storage/framework/views
chmod -R 777 storage bootstrap/cache
php artisan config:cache
```

---

## 2. HTTP 403 Forbidden from Caddy

### Symptom
`curl http://localhost` returns HTTP 403 Forbidden.

### Root Cause
1. Caddy lacks read/execute permissions on parent directories up to `public/`.
2. The root directive in `Caddyfile` does not point to the `public/` directory (e.g. points to the project root instead).

### Fix
```bash
# 1. Ensure parent directories are readable/executable by Caddy
chmod 755 /home/ubuntu
chmod 755 /home/ubuntu/project-folder
chmod 755 /home/ubuntu/project-folder/app
chmod 755 /home/ubuntu/project-folder/app/public

# 2. Check Caddyfile root path
# Make sure it points to /path/to/laravel/public, NOT just /path/to/laravel
```

---

## 3. Caddy FastCGI Socket Error

### Symptom
HTTP 502 Bad Gateway from Caddy.

### Root Cause
Caddyfile specifies an incorrect PHP-FPM socket path or PHP-FPM is not running.

### Fix
```bash
# Find actual socket path
ls -la /run/php/

# Usually: /run/php/php8.3-fpm.sock
# Update Caddyfile:
# php_fastcgi unix//run/php/php8.3-fpm.sock

# Restart PHP-FPM
sudo systemctl restart php8.3-fpm
sudo systemctl reload caddy
```

---

## 4. `ERROR Migration table not found` on `php artisan migrate:status`

### Symptom
Running `php artisan migrate:status` fails with `ERROR Migration table not found`.

### Root Cause
Normal when running on a fresh database before the first `php artisan migrate` execution.

### Fix
Run `php artisan migrate` first to create the `migrations` table and apply initial schema.

---

## 5. `APP_KEY` Missing Error

### Symptom
`RuntimeException: No application encryption key has been specified.`

### Fix
```bash
php artisan key:generate
php artisan config:cache
```

---

## 6. MariaDB Authentication Failed for `laravel_user`

### Symptom
`Access denied for user 'laravel_user'@'localhost'` in Laravel logs or CLI.

### Fix
```bash
# Re-grant privileges via root
sudo mysql << EOF
GRANT ALL PRIVILEGES ON pwa_peminjaman.* TO 'laravel_user'@'localhost' IDENTIFIED BY 'your_password';
FLUSH PRIVILEGES;
EOF
```

Ensure `.env` matches:
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=pwa_peminjaman
DB_USERNAME=laravel_user
DB_PASSWORD=your_password
```

---

## 7. Domain Points to VPS but Returns `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` (Hidden IPv6 / `AAAA` Record)

### Symptom
After pointing a domain's `A` record from shared hosting / cPanel (e.g. Domainesia, Niagahoster, Hostinger) to the VPS IP, browsers (Chrome, Brave, Firefox) report:
`ERR_SSL_VERSION_OR_CIPHER_MISMATCH` or `error:0A000410:SSL routines::sslv3 alert handshake failure`.

### Root Cause
Shared hosting DNS templates automatically generate both `A` (IPv4) and `AAAA` (IPv6) records pointing to their shared cPanel server. When users update only the `A` record to the VPS IP, modern browsers implement Happy Eyeballs (RFC 8305) and prioritize the IPv6 (`AAAA`) record. The browser connects to the old shared hosting IP via IPv6 where no SSL certificate exists for the custom domain, failing the TLS handshake.

### Diagnosis
```bash
# Check authoritative DNS for both A and AAAA
dig A +short yourdomain.com @ns1.registrar.net
dig AAAA +short yourdomain.com @ns1.registrar.net
# If AAAA returns an old shared hosting IPv6 (e.g. 2001:...), that is the culprit!
```

### Fix
1. In cPanel **Zone Editor** (or registrar DNS management), filter by `AAAA` and delete all `AAAA` records for `yourdomain.com` and `www.yourdomain.com` (unless the VPS itself has an allocated IPv6 address configured).
2. Configure Caddy reverse proxy or php_fastcgi block on the VPS:
   ```caddy
   yourdomain.com, www.yourdomain.com {
       encode gzip
       reverse_proxy 127.0.0.1:8022  # or php_fastcgi unix//run/php/php8.3-fpm.sock
   }
   ```
3. Reload Caddy: `sudo systemctl reload caddy`. Caddy automatically requests and provisions Let's Encrypt / ZeroSSL certificates via ALPN/HTTP-01 once DNS resolves to the VPS.
4. Flush DNS resolver and advise testing in Incognito or mobile network to bypass the default 14,400s (4-hour) TTL client cache:
   ```bash
   sudo resolvectl flush-caches
   sudo systemctl restart systemd-resolved
   ```

---

## 8. `php artisan optimize` Breaking PHPUnit Tests (`419 Page Expired` / CSRF Mismatch)

### Symptom
Running `php artisan test` after running `php artisan optimize` or `php artisan config:cache` causes dozens of feature test POST/PUT/DELETE requests to fail with `419 Page Expired` (expected 200/302, received 419).

### Root Cause
`php artisan config:cache` creates `bootstrap/cache/config.php`. When this cached configuration file exists on disk, Laravel's test environment ignores `phpunit.xml` environment overrides (such as `APP_ENV=testing`, `SESSION_DRIVER=array`, or testing CSRF bypass) and loads the production cached configuration, which enforces strict CSRF token validation on every non-GET request.

### Fix
Always clear the configuration cache before executing tests in development/staging:
```bash
php artisan optimize:clear
php artisan test
```

---

## 9. Sluggish PWA / App Loading Due to Single-Threaded Dev Server & Unoptimized Assets

### Symptom
Web app/PWA feels heavy and sluggish, loading spinners take several seconds, especially on mobile or slower network connections.

### Root Cause
1. **Routing Static Files through PHP**: When using `reverse_proxy` without static file handling, every `.css`, `.js`, `.png`, and `.svg` request is routed through single-threaded `php artisan serve`. Large assets or concurrent requests block one another in queue.
2. **Uncompressed User Uploads**: Storing multi-megabyte raw photos directly from phone cameras (often 1–5 MB) and serving them with `Cache-Control: private, no-store` forces clients to download megabytes on every page navigation.
3. **Missing OPcache CLI**: By default, `opcache.enable_cli=0` in `/etc/php/8.3/cli/php.ini`, forcing the PHP CLI worker to re-parse and compile scripts on every incoming HTTP request.

### Fix
1. **Caddy Direct Static File Serving & Long-Lived Caching**:
   Let Caddy serve static files directly from disk with compression and immutable headers, reverse proxying only dynamic routes to PHP:
   ```caddy
   yourdomain.com {
       root * /path/to/laravel/public
       encode zstd gzip

       @static {
           file
           path *.ico *.css *.js *.gif *.webp *.avif *.jpg *.jpeg *.png *.svg *.woff *.woff2 *.webmanifest
       }
       header @static {
           Cache-Control "public, max-age=31536000, immutable"
           X-Content-Type-Options "nosniff"
       }

       file_server

       @notStatic {
           not file
       }
       reverse_proxy @notStatic 127.0.0.1:8022
   }
   ```
2. **Server-Side Avatar / Upload Resizing (`ProfileImageCompressor`)**:
   Resize avatar photos to max 400x400 px with 80% JPEG/WEBP quality before saving to disk. This shrinks raw 1MB–5MB phone uploads to 20KB–45KB (90–95% payload reduction).
3. **HTTP Cache Headers on Image Endpoints**:
   Serve dynamic image routes (`/profil/foto`) with `ETag`, `Last-Modified`, and `Cache-Control: private, max-age=86400, must-revalidate`. Return `304 Not Modified` when `If-None-Match` matches.
4. **Enable OPcache CLI**:
   ```bash
   sudo sed -i 's/;opcache.enable_cli=0/opcache.enable_cli=1/' /etc/php/8.3/cli/php.ini
   sudo sed -i 's/;opcache.enable=1/opcache.enable=1/' /etc/php/8.3/cli/php.ini
   ```

---

## 10. PWA Icon Compatibility (Android Maskable vs iOS Pitch-Black Background)

### Symptom
- PWA icon on Android gets cropped irregularly inside round or squircle adaptive icon frames.
- PWA icon on iOS (iPhone/iPad) displays an ugly solid pitch-black square around a circular logo.

### Root Cause
- iOS Safari does not support transparency on `apple-touch-icon.png` (renders all transparent alpha pixels as solid black).
- Android adaptive launchers require icons declared with `purpose: "maskable"` and an inner safe zone (the logo must fit within the center 80% circle) to avoid clipping.

### Fix
1. **Master Square Canvas**: Generate master icon (e.g. 800x800) with smooth antialiased circular mask.
2. **Apple Touch Icon (`apple-touch-icon.png`, 180x180)**: Paste the logo onto an opaque pure white background (`RGB (255, 255, 255)`), never transparent.
3. **Android Icons (`icon-192.png`, `icon-512.png`)**: Provide ~10-12% padding so the logo stays inside the safe zone, and declare both `any` and `maskable` in `manifest.webmanifest`:
   ```json
   "icons": [
       { "src": "/images/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
       { "src": "/images/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
       { "src": "/images/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
       { "src": "/images/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
   ]
   ```
4. **Bump Service Worker Version**: Increment `CACHE_VERSION` in `sw.js` whenever icons/branding change so browsers and installed PWAs immediately fetch fresh assets.


