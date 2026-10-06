---
name: laravel-vps-bootstrap
description: Bootstrap Laravel project from scratch on bare Ubuntu VPS. Covers environment audit, dependency install (PHP 8.3, MariaDB, Composer), project creation, database setup, and web server (Caddy) configuration. Includes common pitfalls and troubleshooting paths.
---

# Skill: Laravel VPS Bootstrap

Bootstrap a production-ready Laravel application on a bare Ubuntu VPS, from initial environment audit through functional deployment with database and web server integration.

## Scope

This skill covers:
- Environment audit (OS, resources, installed tools)
- Installation of PHP 8.3, PHP-FPM, MariaDB, Composer
- Laravel project creation and configuration
- Database setup (credentials, schema initialization)
- Web server configuration (Caddy + PHP-FPM)
- Common permission & socket issues
- Verification and troubleshooting

## Procedure (Step-by-Step)

### 1. Environment Audit

```bash
# Check OS and system
uname -a
lsb_release -a

# Check resources
free -h
df -h /

# Check web server
which nginx
which apache2
systemctl status caddy

# Check installed languages/tools
php -v
composer --version
node -v
```

**Outcomes to verify**:
- Ubuntu 20.04+ LTS recommended
- At least 1GB RAM free, 10GB+ disk
- Caddy (or Nginx/Apache) available
- PHP not yet installed (or outdated version)

### 2. Install PHP 8.3 + Extensions

```bash
sudo apt update
sudo apt install -y php8.3 php8.3-fpm php8.3-cli \
  php8.3-mysql php8.3-pdo php8.3-mbstring php8.3-xml \
  php8.3-curl php8.3-bcmath php8.3-zip php8.3-gd php8.3-intl php8.3-sqlite3
```

**Verify**:
```bash
php -v
php-fpm8.3 -v
sudo systemctl status php8.3-fpm
```

Expected: `PHP 8.3.x (cli/fpm)`, `php8.3-fpm.service` active (running).

### 3. Install MariaDB

```bash
sudo apt install -y mariadb-server mariadb-client
sudo mysql_secure_installation  # Follow prompts for security
```

**Verify**:
```bash
mysql --version
sudo systemctl status mariadb
```

Expected: `mariadb.service` active (running), port 3306 listening on localhost.

### 4. Install Composer

```bash
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
composer --version
```

Expected: `Composer version 2.x.x`.

### 5. Setup Database & User

```bash
sudo mysql << EOF
CREATE DATABASE app_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'laravel_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON app_name.* TO 'laravel_user'@'localhost';
FLUSH PRIVILEGES;
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User='laravel_user';
EOF
```

**Replace**:
- `app_name` → your database name
- `secure_password_here` → strong password

### 6. Create Laravel Project

```bash
cd /home/username/project-folder
composer create-project laravel/laravel app --prefer-dist
cd app
php artisan key:generate
```

**Verify**:
```bash
php artisan --version
ls -la
```

Expected: Full Laravel directory structure, `APP_KEY` set in `.env`.

### 7. Configure .env for MariaDB

Edit `app/.env`:
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=app_name
DB_USERNAME=laravel_user
DB_PASSWORD=secure_password_here
```

### 8. Run Migrations

```bash
php artisan migrate
```

**Verify**:
```bash
php artisan migrate:status
```

Expected: Migrations listed as `Ran` with timestamps.

### 9. Configure Caddy for Laravel

Create/update `/etc/caddy/Caddyfile`:
```caddy
:80 {
	root * /home/username/project-folder/app/public
	encode gzip
	php_fastcgi unix//run/php/php8.3-fpm.sock
	file_server
}
```

**Replace**:
- `/home/username/project-folder` → actual project path

Reload:
```bash
sudo systemctl reload caddy
sudo systemctl status caddy
```

### 10. Fix Permissions

```bash
chmod -R 755 /home/username/project-folder/app/public
chmod -R 777 /home/username/project-folder/app/storage
chmod -R 777 /home/username/project-folder/app/bootstrap/cache
```

### 11. Cache Configuration

```bash
cd /home/username/project-folder/app
php artisan config:cache
php artisan view:cache
```

### 12. Test

```bash
curl -i http://localhost
# Expected: HTTP 200, Laravel welcome page visible
```

---

## Common Pitfalls & Fixes

See `references/pitfalls.md` for:
- tempnam() permission errors (500)
- Caddy 403 Forbidden
- PHP-FPM socket connection refused
- Database connection timeouts
- Laravel command-line errors (KEY not set, etc.)

---

## Troubleshooting

### Services not running
```bash
sudo systemctl restart php8.3-fpm
sudo systemctl restart mariadb
sudo systemctl reload caddy
```

### Database errors
```bash
# Verify credentials in .env
sudo mysql -u laravel_user -p app_name
SHOW TABLES;

# Reset migrations if needed
php artisan migrate:reset
php artisan migrate
```

### Web server returns 500 or 403
- Check storage/ and bootstrap/cache/ permissions (775+)
- Verify Caddy config points to correct public/ path
- Check PHP-FPM socket path matches Caddyfile

### Laravel command-line errors
```bash
# Regenerate key if missing
php artisan key:generate

# Clear caches
php artisan cache:clear
php artisan config:clear
```

---

## Files & Credentials

After bootstrap, you'll have:
- **Project root**: `/home/username/project-folder/app`
- **Database**: `app_name` (user: `laravel_user`, password: in `.env`)
- **Web URL**: `http://localhost` (or domain)
- **Web server**: Caddy on port 80
- **PHP-FPM**: Unix socket `/run/php/php8.3-fpm.sock`

---

## Next Steps

After bootstrap completes:
1. Create application-specific migrations (models, seeders)
2. Build API routes, controllers, form requests
3. Setup authentication (Laravel Sanctum, Fortify, Breeze)
4. Configure mail, queue, storage services
5. Add frontend (Vue 3, React, Inertia) if PWA/SPA
6. Enable HTTPS (Caddy auto-HTTPS when domain pointed)

---

## Quick Existing Repository Bootstrapping (For Dev/Testing)

When cloning an existing Laravel repo to VPS for fast evaluation or testing:

1. **Clone & Environment Setup**
   ```bash
   git clone <repo-url>
   cd <project-folder>
   cp -n .env.example .env
   composer install --no-interaction --prefer-dist --optimize-autoloader
   php artisan key:generate --force
   ```

2. **SQLite Fast Database (No MariaDB/MySQL setup required)**
   ```bash
   sed -i 's/DB_CONNECTION=mysql/DB_CONNECTION=sqlite/' .env
   chmod -R 775 storage bootstrap/cache
   php artisan storage:link --force
   php artisan migrate --force
   php artisan db:seed --force
   ```

3. **Frontend Build & Dev Server**
   ```bash
   npm install && npm run build
   php artisan serve --host=127.0.0.1 --port=<available-port, e.g. 8022>
   ```

4. **HTTPS Exposure & Seeder Credentials Check**
   - Check `database/seeders/UserSeeder.php` or `DatabaseSeeder.php` to extract default admin credentials.
   - Run `cloudflared tunnel --url http://127.0.0.1:<port>` to get instant HTTPS for PWA and mobile testing.

