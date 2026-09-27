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
