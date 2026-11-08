# Split Infrastructure DNS, Backup Cron Telegram, dan Audit Keamanan Inspect

Dokumentasi pola teknis dan temuan nyata dari operasional PWA Bruder FIC (formatio-fic.com di VPS, hosting cPanel di DomaiNesia via MCP).

---

## 1. Split DNS: Web di VPS, Email di Hosting cPanel (DomaiNesia)
### Gejala / Masalah
Email resmi biara (misal `sandi27@formatio-fic.com`) dibuat di cPanel hosting DomaiNesia, tetapi tidak bisa menerima kode OTP atau email masuk dari internet saat web domain utama (`formatio-fic.com`) diarahkan ke VPS.

### Akar Masalah
Secara default di cPanel DNS Zone:
1. `formatio-fic.com` (A Record) diarahkan ke IP VPS (`43.173.9.113`).
2. `mail.formatio-fic.com` berupa CNAME ke `formatio-fic.com` (yang berarti menuju IP VPS).
3. `MX Record` bernilai `formatio-fic.com` (menuju IP VPS).
Karena VPS Linux kita murni web server (tidak menjalankan mail server MTA/IMAP/SMTP), semua email kiriman dari luar (Google, OTP, dll.) mental (*bounce*).

### Solusi Permanen via MCP cPanel
1. Hapus DNS record CNAME `mail.formatio-fic.com` (cek nomor barisnya via `get_dns_records`).
2. Buat A Record baru: `mail.formatio-fic.com` -> IP Hosting DomaiNesia (`202.155.137.49`) dengan TTL 300.
3. Edit MX Record: ubah exchange/destination menjadi `mail.formatio-fic.com` (prioritas 0).
4. Verifikasi via `dig @ns1.domainesia.net MX formatio-fic.com +short` dan `A mail.formatio-fic.com +short`.

---

## 2. Pengiriman Otomatis Backup Database SQLite ke Telegram (Cron Job)
### Pola Implementasi
Untuk mengirimkan backup database harian otomatis setiap 01:00 WIB ke obrolan Telegram pengguna tanpa memboroskan token LLM:
1. Gunakan `default_api:cronjob` dengan konfigurasi `no_agent: true`.
2. Letakkan skrip bash di `~/.hermes/profiles/coding/scripts/cron-backup-database-telegram.sh`.
3. **Jebakan Binary CLI**: Server Ubuntu minimal sering kali tidak memiliki utilitas `zip` CLI (`command not found`). Jangan andalkan `zip` command. Gunakan Python stdlib `zipfile`:
   ```bash
   python3 -c "
   import zipfile, os
   with zipfile.ZipFile('$OUT_ZIP', 'w', compression=zipfile.ZIP_DEFLATED) as zf:
       zf.write('$SRC', arcname=os.path.basename('$SRC'))
   "
   ```
4. **Penyampaian Lampiran**: Di akhir stdout skrip bash, cetak baris `MEDIA:/path/ke/file.zip`. Platform Telegram Hermes otomatis mengubah marker ini menjadi file dokumen lampiran native yang terkirim ke pengguna.
5. **Konversi Timezone**: Server menggunakan timezone CST (UTC+8 / Asia/Shanghai), sedangkan pengguna berada di WIB (UTC+7). Jadwal pukul 01:00 WIB setara dengan pukul 02:00 CST -> schedule cron: `0 2 * * *`.

---

## 3. Audit Celah Keamanan yang Terlihat saat Inspect Browser (DevTools)
Saat pengguna atau bruder muda melakukan *Inspect Element* / *DevTools* pada PWA:

### A. Celah Nyata yang Harus Diperbaiki
1. **`APP_DEBUG=true` di `.env` (Risiko Tinggi)**
   - Jika ada galat tak tertangani atau request abnormal, tab Network -> Response menampilkan halaman debug *Ignition*. Ini membocorkan path direktori server, query SQL, nama tabel, dan konfigurasi lingkungan.
   - **Perbaikan**: Wajib set `APP_DEBUG=false` dan `APP_ENV=production` pada live server, lalu restart service `pwa-bruder.service`.
2. **Informasi Versi PHP di Header Response (`X-Powered-By` & `Server`)**
   - Header `X-Powered-By: PHP/8.3.6` memberitahu versi eksak PHP ke publik.
   - **Perbaikan di Caddyfile**: Gunakan kombinasi blok `header` global dan `header_down` di dalam `reverse_proxy`:
     ```caddy
     header {
         -Server
         -X-Powered-By
         X-Frame-Options "SAMEORIGIN"
         X-Content-Type-Options "nosniff"
         Referrer-Policy "strict-origin-when-cross-origin"
         Strict-Transport-Security "max-age=31536000; includeSubDomains"
     }
     reverse_proxy @notStatic 127.0.0.1:8022 {
         header_down -X-Powered-By
         header_down -Server
     }
     ```
     *Catatan:* `header_down` di dalam `reverse_proxy` penting karena header upstream dari PHP runtime sering menembus blok header luar jika tidak dicabut secara eksplisit.
3. **Ketiadaan Security Headers Standar**
   - Tambahkan header proteksi di Caddyfile:
     - `X-Frame-Options: SAMEORIGIN` (mencegah Clickjacking).
     - `X-Content-Type-Options: nosniff`.
     - `Referrer-Policy: strict-origin-when-cross-origin`.
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS).
   - Validasi Caddy via `sudo caddy validate --config /etc/caddy/Caddyfile` lalu reload `sudo systemctl reload caddy`. Cek via `curl -I -s https://formatio-fic.com/login`.

### B. False Positives (Hal Normal yang Sering Dikira Kebocoran oleh Pemula)
- **CSRF Token di `<meta name="csrf-token" content="...">`**: Ini adalah mekanisme pertahanan standar web terhadap Cross-Site Request Forgery, bukan token rahasia yang bocor.
- **Respons `/push/vapid-key`**: Berisi public key VAPID (`{"key":"BD..."}`) yang memang secara spesifikasi W3C wajib disiarkan ke browser agar Service Worker bisa berlangganan Push Notification.
- **`data-uid="12"` pada tag script notifikasi**: ID integer internal untuk indexing `localStorage` penanda notifikasi di HP bruder.

---

## 4. Batasan UNIX Domain Socket vs TCP Remote
- Jika user bertanya apakah Redis socket (misal `/home/formatio/.local/apps/run/redis.sock` di cPanel) bisa dihubungkan ke aplikasi di VPS:
- **Jawab tegas: TIDAK BISA**. UNIX domain socket adalah IPC (*Inter-Process Communication*) berbasis berkas lokal dalam satu kernel OS yang sama. Server VPS tidak memiliki akses fisik ke socket filesystem cPanel tersebut.
- Membuka Redis TCP remote lewat internet antar-server justru menambah latensi network (50–100ms per request).
