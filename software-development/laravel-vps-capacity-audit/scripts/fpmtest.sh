#!/usr/bin/env bash
# Lingkungan uji Caddy + PHP-FPM untuk PWA Bruder FIC (TIDAK menyentuh produksi).
# Pemakaian: fpmtest.sh up <pm.max_children> | down
# Opsi env: BCRYPT_ROUNDS (default 12), VALIDATE_TS (default 1)
set -u
W=/tmp/fpmtest
APP=/home/ubuntu/PWA_Bruder-Muda
PORT=18300
case "${1:-}" in
down)
  [ -f $W/fpm.pid ] && kill "$(cat $W/fpm.pid)" 2>/dev/null
  [ -f $W/caddy.pid ] && kill "$(cat $W/caddy.pid)" 2>/dev/null
  sleep 1; echo "dihentikan"; exit 0 ;;
up)
  CH=${2:-8}
  rm -rf $W; mkdir -p $W/storage/framework/{sessions,views,cache/data} $W/storage/logs $W/run
  cp $APP/database/database.sqlite $W/db.sqlite
  cat > $W/php-fpm.conf <<EOF
[global]
pid = $W/fpm.pid
error_log = $W/fpm.log
daemonize = yes
[bruder]
listen = $W/run/fpm.sock
listen.mode = 0666
pm = dynamic
pm.max_children = $CH
pm.start_servers = 2
pm.min_spare_servers = 2
pm.max_spare_servers = 4
pm.max_requests = 500
clear_env = no
env[DB_DATABASE] = $W/db.sqlite
env[LARAVEL_STORAGE_PATH] = $W/storage
env[APP_URL] = http://127.0.0.1:$PORT
env[SESSION_SECURE_COOKIE] = "false"
env[SESSION_DRIVER] = file
env[CACHE_STORE] = file
env[BCRYPT_ROUNDS] = ${BCRYPT_ROUNDS:-12}
php_admin_value[opcache.enable] = 1
php_admin_value[opcache.memory_consumption] = 128
php_admin_value[opcache.validate_timestamps] = ${VALIDATE_TS:-1}
EOF
  cat > $W/Caddyfile <<EOF
{
  admin off
  auto_https off
}
:$PORT {
  root * $APP/public
  encode zstd gzip
  php_fastcgi unix/$W/run/fpm.sock
  file_server
}
EOF
  php-fpm8.3 -y $W/php-fpm.conf -c /etc/php/8.3/fpm/php.ini 2>&1 | head -3
  nohup caddy run --config $W/Caddyfile --adapter caddyfile > $W/caddy.log 2>&1 &
  echo $! > $W/caddy.pid
  for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:$PORT/login && break; sleep 0.5; done
  curl -s -o /dev/null -w "GET /login -> %{http_code}\n" http://127.0.0.1:$PORT/login
  ;;
esac
