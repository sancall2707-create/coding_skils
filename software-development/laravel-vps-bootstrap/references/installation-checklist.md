# Installation Sequence Checklist (Session Reference)

This checklist reflects the exact sequence used in the session on 2026-09-24 for a Laravel PWA project on Ubuntu 24.04 LTS with Caddy.

---

## Exact Commands Run

### 1. System Update & PHP/MariaDB Install
```bash
sudo apt update
sudo apt install -y php8.3 php8.3-fpm php8.3-cli php8.3-mysql \
  php8.3-pdo php8.3-mbstring php8.3-xml php8.3-curl php8.3-bcmath \
  php8.3-zip php8.3-gd php8.3-intl php8.3-sqlite3 mariadb-server mariadb-client
```

### 2. Verify Installed Services
```bash
php -v
php-fpm8.3 -v
sudo systemctl status php8.3-fpm --no-pager
mysql --version
sudo systemctl status mariadb --no-pager
```

### 3. Secure MariaDB
```bash
sudo mysql_secure_installation
# Interactive prompts: set root password, remove anon users, disallow remote root, remove test DB
```

### 4. Create Database & User
```bash
sudo mysql << 'EOF'
CREATE DATABASE pwa_peminjaman CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'laravel_user'@'localhost' IDENTIFIED BY 'laravel_password_secure_2026';
GRANT ALL PRIVILEGES ON pwa_peminjaman.* TO 'laravel_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### 5. Install Composer
```bash
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
composer --version
```

### 6. Create Laravel Project
```bash
cd ~/pwa-peminjaman-fasilitas
composer create-project laravel/laravel app --prefer-dist
cd app
php artisan key:generate
```

### 7. Configure .env
```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=pwa_peminjaman
DB_USERNAME=laravel_user
DB_PASSWORD=laravel_password_secure_2026
```

### 8. Run Migrations
```bash
php artisan migrate
php artisan migrate:status
```

### 9. Configure Caddy
```bash
sudo tee /etc/caddy/Caddyfile > /dev/null << 'EOF'
:80 {
	root * /home/ubuntu/pwa-peminjaman-fasilitas/app/public
	encode gzip
	php_fastcgi unix//run/php/php8.3-fpm.sock
	file_server
}
EOF
sudo systemctl reload caddy
```

### 10. Fix Permissions
```bash
chmod -R 755 /home/ubuntu/pwa-peminjaman-fasilitas/app/public
chmod -R 777 /home/ubuntu/pwa-peminjaman-fasilitas/app/storage
chmod -R 777 /home/ubuntu/pwa-peminjaman-fasilitas/app/bootstrap/cache
```

### 11. Cache Config
```bash
cd ~/pwa-peminjaman-fasilitas/app
php artisan config:cache
php artisan view:cache
```

### 12. Test
```bash
curl -i http://localhost
# HTTP 200 + Laravel welcome page = SUCCESS
```

---

## Timing Summary (Session)

| Step | Duration |
|------|----------|
| apt update + install PHP/MariaDB | ~5 min |
| MariaDB secure + DB/user setup | ~3 min |
| Composer install | ~2 min |
| Laravel create + migrate | ~3 min |
| Caddy config + reload | ~1 min |
| Permissions + cache | ~1 min |
| **Total** | **~15 minutes** |

---

## Files Created in This Session

```
/home/ubuntu/pwa-peminjaman-fasilitas/
├── TAHAP1_AUDIT_DAN_FONDASI.md
├── TAHAP2_SETUP_DAN_INSTALASI.md
├── README.md
├── pwa_peminjaman_fasilitas.md
└── app/
    ├── .env
    ├── composer.json
    ├── artisan
    ├── config/
    ├── database/
    ├── public/
    ├── routes/
    ├── storage/
    └── ...
```

---

## Next Steps Documented in Session

1. Create application migrations (vehicles, facilities, bookings, categories, roles)
2. Build API controllers + form requests + resources
3. Setup Laravel Sanctum authentication
4. Configure frontend (Vue 3 + Tailwind + PWA)