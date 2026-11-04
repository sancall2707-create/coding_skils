# Audit "layar putih/blank" pada PWA Laravel di belakang Caddy

Keluhan user: halaman (Agenda, Sapaan) tiba-tiba putih kosong, padahal internet HP bagus.
User menekankan: jangan ubah data/DB/alur fitur. Audit = baca saja, uji di lingkungan terpisah.

## Urutan diagnosa (murah ke mahal)
1. Log aplikasi: `grep -E "\.(ERROR|CRITICAL)" storage/logs/laravel.log | tail` -> cek tanggal galat terakhir.
2. Waktu render per halaman lewat skrip PHP (bootstrap kernel, `auth()->login(User::find(id))`,
   `Request::create(path)`, `$http->handle()`, ukur `hrtime`, `DB::enableQueryLog`). Hanya membaca.
   Hasil sehat: 13-76 ms, 1-18 query. Jika sehat, kode BUKAN penyebab.
3. Ukuran gambar/aset (mis. foto sapaan) + semua URL `PRECACHE_URLS` di `sw.js` harus HTTP 200
   (satu 404 saja = pemasangan Service Worker gagal total).
4. Log Caddy: `sudo journalctl -u caddy --since "14 days ago" -o cat` lalu parse JSON; cari
   `dial tcp 127.0.0.1:<port>: connect: connection refused` (= 502 dari Caddy). Cetak waktu (WIB),
   IP, method, URI. Bedakan IP VPS sendiri (uji coba) dari pengguna.
   Catatan: baris `aborting with incomplete response` ke `php8.3-fpm.sock` milik situs LAIN
   (blok `:80`) - bukan aplikasi ini.
5. Cara server berjalan: `pstree -sp <pid>`, `systemctl list-units | grep -i app`, `crontab -l`.
   `php artisan serve` tanpa systemd/supervisor = mati bersama sesi induknya dan tidak hidup lagi.
   `PHP_CLI_SERVER_WORKERS` tidak diset = 1 pekerja.
6. Beban host: `top -b -n 2 -d 2` (ambil iterasi ke-2), `free -m`, swap, OOM (`journalctl -k | grep -i oom`).
   `ps %CPU` kumulatif bisa menyesatkan; pakai top.

## Temuan kunci (kasus Bruder FIC)
- Caddy membalas **502 dengan badan 0 byte** saat upstream mati -> browser menampilkan layar putih.
- Kejadian cocok dengan waktu RESTART server oleh agen sendiri saat menerapkan perubahan
  (`pkill` + `php artisan serve`). Restart tanpa penyangga = pengguna melihat blank.
- Kode, DB, gambar, aset PWA, memori: semuanya sehat. Jangan salahkan jaringan pengguna.

## Perbaikan yang diusulkan (minta persetujuan dulu; tidak menyentuh kode/DB)
1. Unit systemd untuk `php artisan serve` (Restart=always) - perbaikan utama. Hilangkan pola `pkill`+jalankan manual.
2. Caddy: `reverse_proxy` dengan `lb_try_duration 6s` + `lb_try_interval 250ms`, dan `handle_errors`
   untuk 502/503/504 -> `respond` HTML ramah + `<meta http-equiv="refresh" content="3">` + `Cache-Control: no-store`.
3. `PHP_CLI_SERVER_WORKERS=4` (butuh ekstensi pcntl; cek `php -m | grep pcntl`).
4. Setelah deploy: gunakan restart yang cepat dan verifikasi `curl` sebelum mengumumkan selesai.

## Cara membuktikan usulan Caddy TANPA menyentuh produksi
Skrip Python: tulis Caddyfile uji (`admin off`, `auto_https off`, port 18081 polos & 18082 usulan,
upstream 18090), jalankan `caddy run` via `subprocess.Popen` (hentikan lewat PID sendiri),
uji 3 skenario: upstream mati (502 kosong vs 503 ramah+refresh), upstream hidup lagi setelah 2 dtk
(polos gagal 502 vs usulan sukses 200 setelah 2,02 dtk), upstream sehat (tak melambat: ~2 ms vs 1,7 ms).
Server HTTP uji dibuat dengan `socketserver.TCPServer` di thread + `Timer(shutdown)`.

## Pitfall alat
- Perintah shell panjang yang menyisipkan `pkill -f <pola>` memakai pola yang juga muncul di
  argumen dirinya sendiri bisa membunuh shell (`exit -15`) atau diblokir sebagai "malformed payload".
  Tulis skrip ke berkas (write_file) lalu jalankan, jangan satu-baris `bash -c` raksasa.
- `&` di dalam heredoc CSS/teks memicu penolakan "backgrounding"; tulis berkas via write_file.
- Jangan `pkill -f "caddy_test"` setelah menjalankan Caddy uji lewat `( ... &)`; pakai Popen + terminate.
