---
name: laravel-vps-capacity-audit
description: "Audit kapasitas dan tuning produksi Laravel di VPS (Caddy/artisan serve/PHP-FPM, SQLite) tanpa menyentuh produksi - menilai prompt tuning generik terhadap kenyataan server, uji beban lokal login+CSRF di salinan DB, harness Caddy+PHP-FPM sementara, cari bottleneck CPU sebenarnya, dan evaluasi pindah ke hosting bersama (DomaiNesia via MCP)."
---

# Audit kapasitas Laravel di VPS (aman untuk produksi)

Dipakai saat user menempelkan prompt tuning generik (Nginx, PHP-FPM, Redis, Supervisor, k6) atau bertanya "bagaimana kalau pindah hosting". Konteks: PWA Bruder FIC, nol toleransi data loss, jangan ubah fitur, Bahasa Indonesia.

## Aturan inti
1. JANGAN menjalankan prompt generik apa adanya. Periksa dulu kenyataan server (baca saja), laporkan tiap asumsi yang tidak cocok, lalu tawarkan opsi lewat `clarify`.
2. Semua uji beban pada SALINAN (port uji, `DB_DATABASE`, `LARAVEL_STORAGE_PATH` terpisah). Catat md5 `database.sqlite` sebelum dan sesudah; harus identik.
3. Klaim angka harus terukur. Perkiraan teori (mis. "bcrypt 10 = 4x lebih cepat") ternyata tidak muncul di uji beban karena CPU jenuh; laporkan koreksi secara terbuka.

## Pemeriksaan awal (semua baca saja)
`nproc; free -h; php -v`, `ss -ltnp`, `ps aux | grep -E 'artisan serve|php-fpm|caddy'`, `systemctl is-active nginx php8.3-fpm redis-server supervisor caddy`, isi `/etc/caddy/Caddyfile`, `.env` (APP_ENV, SESSION_DRIVER, QUEUE_CONNECTION, BCRYPT_ROUNDS), `grep -rn "dispatch(\|ShouldQueue" app` (kalau kosong, Redis queue/Supervisor tidak berguna), `grep -n "function *(" routes/*.php` (closure menggagalkan `route:cache`), throttle login yang sudah ada.

Fakta server ini: Caddy -> `artisan serve` 127.0.0.1:8022 tanpa systemd (mati = 502). PHP-FPM pool `www` hanya melayani blok `:80` aplikasi lain, bukan domain produksi. Tuning pm.max_children/OPcache di pool itu tidak berpengaruh ke produksi. Ganti Nginx tidak perlu: Caddy `php_fastcgi unix//run/php/php8.3-fpm.sock` cukup.

## Uji beban lokal
- Klien Python stdlib (`http.cookiejar` + thread): GET /login ambil `_token`, POST /login, lalu GET halaman. Pakai akun berbeda per VU (rate limit login 5/menit per username+IP mengaburkan hasil). Password uji ditulis ke SALINAN DB saja. Tambah akun uji di salinan bila VU > jumlah akun.
- Validasi login benar-benar berhasil: status akhir bukan URL `/login` (catat sebagai 401 palsu), jangan percaya HTTP 200.
- Tiga skenario: login terus-menerus, penelusuran halaman (pola nyata, jeda 3 detik), login serentak (kasus terburuk).
- Server uji `artisan serve`: `PHP_CLI_SERVER_WORKERS=N` + `--no-reload`.

## Harness Caddy + PHP-FPM sementara
`scripts/fpmtest.sh up <max_children>|down`: php-fpm dengan config di /tmp (socket sendiri, `daemonize=yes`, `clear_env=no`, `env[...]` untuk DB/storage uji), Caddy port 18300 (`admin off`, `auto_https off`). Jalan sebagai user biasa, tanpa root, tanpa menyentuh layanan produksi. Nilai env FPM boolean harus berkutip (`"false"`) atau muncul "empty value".

Uji fitur yang peka lingkungan di harness ini: PDF raport (Chrome headless via `Process`), simpan agenda (tulis DB), unggah `profile_photo` (rute `POST /profil`, form `/profil/edit`), `GET /profil/foto`.

## Temuan yang berlaku untuk server ini
- Bottleneck login serentak = CPU, bukan konfigurasi aplikasi. `top` menunjukkan idle 0,2%: dua proses root `snap run cups.cupsd` / `cups-browsed` (chromium) memakai ~83% CPU masing-masing selama berhari-hari, plus YDService ~28%. `ps` %CPU = rata-rata seumur proses; ukur sesaat dengan `top -bn2 -d 3`.
- bcrypt cost 12 ~410-560 ms/verify, cost 10 ~95-146 ms (diukur terpisah), tetapi uji beban hampir tak berubah karena CPU jenuh. Hash lama cost 12 tetap valid bila `BCRYPT_ROUNDS` diturunkan.
- Hasil (bcrypt 10, FPM 12 worker): 22 login serentak ~2,9 s; 50 login serentak ~6,2 s (maks 6,9 s), 0 galat 5xx. Satu pengguna tanpa antrean 0,12-0,26 s. `artisan serve` 1 worker 22 login serentak 4,8 s.
- FPM sebagai `www-data` TIDAK bisa menulis `database/`, `database.sqlite`, `storage/`, `bootstrap/cache/` (milik ubuntu). Bila produksi dipindah ke FPM, pakai pool khusus `user = ubuntu`, jangan chown massal. Pool `www` dipakai app lain; jangan diubah.
- Jangan sarankan: Redis/Supervisor/Nginx (tidak ada queue, RAM sempit, swap hampir habis), `route:cache` (closure), `opcache.validate_timestamps=0` (butuh restart tiap deploy). `config:cache`, `view:cache`, `event:cache` aman. Perubahan `.env` ke `SESSION_DRIVER=redis` mengeluarkan semua user.
- Menyentuh proses root (cups/chromium) butuh persetujuan eksplisit; selidiki baca-saja dulu.

## Stabilitas produksi: systemd + uji hosting
Produksi `artisan serve` pernah mati sendiri (502 nyata). Sekarang dikelola `pwa-bruder.service` (Restart=always, enabled). Resep, urutan peralihan aman (nyalakan unit dalam satu rantai; JANGAN matikan proses lama lewat tool proses yang menjadi induk perintah berjalan, situs 502 ~1 menit), dan langkah uji subdomain `uji.formatio-fic.com` via MCP (create_subdomain, git_deploy, wajib ubah docroot ke `uji/public`): `references/systemd-artisan-serve-dan-uji-hosting.md`.

## Eksekusi bertahap optimasi beban (sesi 6 Nov 2026)
Ketika user setuju optimasi kapasitas untuk 50 user serentak:
1. **Solusi 1 (BCRYPT_ROUNDS)**: Ubah `BCRYPT_ROUNDS=10` di `.env` lalu `php artisan config:clear`. Verifikasi: cost 12 ~1,2 detik vs cost 10 ~0,3 detik (CPU VPS saat ini). Password lama tetap valid karena bcrypt menyimpan cost di hash header (`$2y$12$...`). DB tidak disentuh (0% migrasi), tes user login pass.
2. **Solusi 2 (Multi-worker systemd)**: Tambahkan `Environment=PHP_CLI_SERVER_WORKERS=4` di `/etc/systemd/system/pwa-bruder.service`. Backup unit lama, `sudo systemctl daemon-reload && sudo systemctl restart pwa-bruder.service`. Verifikasi: 4 request paralel serentak merespons 200 via `ThreadPoolExecutor`.
3. **Solusi 3 (Cache build Laravel - PERINGATAN JEBAKAN config:cache)**:
   - **JANGAN jalankan `config:cache` pada proyek Laravel SQLite yang menggunakan `RefreshDatabase`**: Menjalankan `config:cache` membekukan koneksi database default ke berkas fisik (`database.sqlite`) di dalam `bootstrap/cache/config.php`. Ketika suite tes (`php artisan test`) dijalankan, runner tes tidak lagi bisa meng-override koneksi ke in-memory (`:memory:`), sehingga tes mengeksekusi migrasi/rollback pada database fisik produksi dan memicu proteksi keamanan atau mengosongkan tabel!
   - Jika terlanjur dijalankan: segera jalankan `php artisan config:clear` dan pulihkan database dari backup terbaru.
   - Yang AMAN dan direkomendasikan untuk produksi: **`php artisan view:cache`** (cache template Blade) dan **`php artisan event:cache`**. Keduanya menghemat I/O disk saat rendering HTML tanpa mengunci konfigurasi database.
   - `route:cache` tetap dilarang jika ada closure route di `routes/web.php`.
4. Selalu cadangkan DB (`backup-pwa-bruder.sh`) dan cek MD5 `database.sqlite` sebelum & sesudah tiap langkah untuk membuktikan 0% data loss.

## Penanganan Zombie Loop Snap CUPS / Chromium (Sesi 7 Nov 2026)
- **Gejala:** Website melambat bertahap, load average tembus 4-5 pada server 2-core, `ps aux` menunjukkan proses root `/bin/bash /snap/bin/chromium run cups.cups-browsed` dan `cups.cupsd` memakan 40-50% CPU per proses secara konstan.
- **Akar Masalah:** Snap package `cups` mencoba menjalankan daemon printing di server yang tidak memiliki hardware printer / interface terkait, menyebabkan infinite busy-loop.
- **Penting:** PWA Bruder FIC mencetak PDF menggunakan `google-chrome-stable` (paket `.deb` resmi Google), BUKAN snap chromium / cups.
- **Solusi Permanen (Sudo):**
  1. Hentikan dan matikan autostart service systemd snap:
     `sudo systemctl stop snap.cups.cups-browsed.service snap.cups.cupsd.service`
     `sudo systemctl disable snap.cups.cups-browsed.service snap.cups.cupsd.service`
  2. JANGAN hanya melakukan `sudo kill -9` pada PID bash/chromium karena systemd snap akan otomatis melakukan restart spawn PID baru. Wajib `systemctl stop` & `disable`.
  3. Verifikasi: `ps aux | grep -E "cups|chromium"` harus kosong, dan waktu respon web langsung kembali normal (< 0.05 detik).

## Evaluasi pindah ke hosting DomaiNesia (nimbus_go)
Detail dan klien MCP: `references/mcp-domainesia-evaluasi.md`. Ringkas: 1 core, 1 GB RAM, entry process 12 (request ke-13 bisa 508), Chrome headless belum terverifikasi (PDF raport berisiko mati), MCP baru >100 tool tapi tetap tanpa eksekusi shell/composer (SSH aktif, agen tak punya kredensial); lebih kecil dari VPS, jadi bukan peningkatan. Repo tidak membawa `database.sqlite`/`storage/app`; deploy tanpa data = data loss.

## Catatan sesi 5 Nov 2026
- Sebelum git_deploy ke hosting, cek repo publik/privat (`curl api.github.com/repos/<owner>/<repo>`, field private) dan `git ls-files twa-release`: repo ini publik dan sempat memuat keystore APK (lihat skill `pwa-web-push-twa`).
- Deploy git ke hosting tanpa `vendor/` dan `.env` menghasilkan HTTP 500 kosong; MCP tidak bisa `composer install`. Docroot awal `uji` membuka `artisan`/`README.md` lewat web sampai diganti `uji/public`.
- Panduan pengguna bergambar: skill `app-user-manual-book`.

## Pitfalls skrip
- Hapus `&` dari heredoc foreground atau tulis skrip via write_file.
- `sed -i` pada baris multi-baris memotong sintaks; setelah edit skrip uji jalankan `ast.parse`.
- Baca skill `laravel-production-safe-change` untuk alur backup/migrasi/commit.
