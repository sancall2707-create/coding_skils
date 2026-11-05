# systemd untuk artisan serve + uji subdomain di hosting (DomaiNesia)

## 1. Unit systemd produksi (terbukti 5 Nov)
Produksi `formatio-fic.com` = Caddy -> `php artisan serve` 127.0.0.1:8022. Tanpa systemd, proses mati = 502 (terjadi nyata; log Caddy: `dial tcp 127.0.0.1:8022: connection refused`).

`/etc/systemd/system/pwa-bruder.service` (salinan di `~/backups/systemd/`):
```
[Unit]
Description=PWA Bruder FIC (Laravel) di 127.0.0.1:8022 di belakang Caddy
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/PWA_Bruder-Muda
ExecStart=/usr/bin/php artisan serve --host=127.0.0.1 --port=8022
Restart=always
RestartSec=2
KillMode=control-group
LimitNOFILE=65536
[Install]
WantedBy=multi-user.target
```
Cek: `sudo systemd-analyze verify`, `daemon-reload`, `enable --now`. Bukti ketahanan: `sudo kill -9 $(systemctl show -p MainPID --value pwa-bruder)` -> HTTP 200 kembali dalam ~3,5 s (`NRestarts` naik). `sudo -n` tersedia tanpa sandi.

### Urutan peralihan (PELAJARAN: jangan mematikan proses lama dulu)
Mematikan sesi latar lama (`process kill`) dan `pkill` dalam satu perintah memutus perintah itu sendiri dan menyisakan ~1 menit 502. Urutan benar: backup DB; tulis unit + verify + daemon-reload; lalu SATU rantai perintah `pkill -f "php8.3 -S 127.0.0.1:8022"; sudo systemctl enable --now pwa-bruder` (atau stop lama lalu start unit segera). Jangan matikan proses lewat tool process yang menjadi induk perintah yang sedang berjalan. Segera cek `ss -ltnp | grep 8022` dan `curl /login`.

Bila situs 502: `ss -ltn | grep 8022`; kosong = proses mati, nyalakan ulang (backup dulu).

## 2. Uji subdomain di hosting lewat MCP (nimbus_go)
MCP yang diperbarui user punya >100 tool (domain, subdomain, DNS, file, cron, Git deploy, MySQL, Redis, runtime Node/Bun/Deno, dll). TETAP tidak ada tool eksekusi shell/composer/artisan. Fitur `ssh: 1` aktif tapi kredensial tidak dimiliki agen; jangan minta sandi lewat chat.

Urutan yang berhasil:
1. `create_subdomain(subdomain=uji, domain=formatio-fic.com, document_root=uji)` -> DNS A otomatis ke 202.155.137.49 (cek `dig +short @ns1.domainesia.net`). DNS produksi tidak berubah.
2. `git_deploy_add(domain, docroot=/home/formatio/uji, repo_url, branch)` lalu `git_deploy_deploy(id, confirm=true)`; baca `git_deploy_log(id)`. Docroot harus sudah ada (subdomain membuatnya, berisi `php.ini`).
3. WAJIB `change_subdomain_docroot(domain, docroot="uji/public")` supaya `artisan`, `README.md`, `app/`, `.git`, `.env` tidak terjangkau web. Konfigurasi Apache butuh ~10-30 s; ukur beberapa putaran dengan query acak, jangan simpulkan dari satu cek (sempat 200 lalu 500).
4. Verifikasi dengan `curl --resolve uji.formatio-fic.com:443:202.155.137.49`: `.env`/`.git` harus 403, `/artisan` jangan 200.
5. `/login` 500 kosong = `vendor/` (95 MB, 9.117 berkas, tidak dilacak git), `.env`, `database.sqlite` tidak ada. Perlu SSH (`composer install`, `.env`, `key:generate`, `migrate --seed` dengan DB KOSONG, jangan salin data produksi). Mengunggah vendor lewat `upload_file` tidak praktis.

## 3. SEBELUM git deploy dari repo GitHub
Periksa `git ls-files | grep -i -E "keystore|\.env|\.sqlite|\.pem|secret"` dan status publik repo (`curl api.github.com/repos/<o>/<r>` -> `private:false`). Pernah ditemukan `twa-release/signing.keystore` + `signing-key-info.txt` (sandi) terlacak di repo PUBLIK. Perbaikan minimal: backup di luar repo, `git rm --cached`, tambah `.gitignore`, commit+push. Riwayat lama tetap memuatnya; rotasi kunci = keputusan user (APK harus dibangun ulang). Laporkan terbuka, jangan diam-diam.
