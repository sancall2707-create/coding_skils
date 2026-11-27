# Diagnosa 419 PAGE EXPIRED (login PWA Bruder FIC)

Kasus 26 Nov 2026: screenshot HP "419 | PAGE EXPIRED". User awalnya bertanya masa kadaluarsa.

## Langkah diagnosa (baca-saja, DB tidak disentuh)
1. Masa sesi: `grep -nE "^(SESSION|APP_ENV)" .env` dan `config/session.php`. Bruder: `SESSION_LIFETIME=720` (12 jam), driver `file`, `expire_on_close=false`.
2. Log Caddy (butuh `sudo`, file tidak terbaca user biasa):
   `sudo grep '"status":419' /var/log/caddy/formatio-access.log | tail -n 15`, lalu parse JSON dengan python (`ts`, `request.method/uri/remote_ip`, `request.headers.Referer/Cookie`).
   Server CST = WIB-1 jam: 10.46 WIB di HP = 11:46 di log (sesuai catatan memori "CST = WIB+1" -> cek selisih nyata lewat `date`).
3. Rangkai semua request `/login` dari IP yang sama di sekitar waktu 419 (GET/POST, status, ada tidaknya header Cookie).
4. Log Laravel TIDAK mencatat 419 (`TokenMismatchException` tidak dilaporkan). Jangan berharap menemukannya di `storage/logs/laravel.log`.

## Temuan
- Cookie sesi ada pada semua request 419 dan form baru dibuka ~11 detik sebelumnya = bukan kadaluarsa 12 jam.
- Pola: dua `POST /login` beruntun dalam detik yang sama (tap ganda). Login pertama memutar ulang sesi/token, POST kedua membawa token lama -> 419. Pola sama pada 25 Nov (Android).

## Perbaikan opsi 1 (dipakai)
`resources/views/auth/login.blade.php`: skrip submit-guard. Flag `sending`, `preventDefault()` pada submit kedua, tombol `disabled` + teks "MEMPROSES...", pemulihan setelah 15 detik. Selektor form lewat `form[action="{{ route('login.store') }}"]`. LSP menandai error JS palsu pada sintaks Blade; verifikasi dengan `php artisan view:cache` dan `curl https://formatio-fic.com/login | grep querySelector`.
Backup view lebih dulu ke `/home/ubuntu/backup-manual/`.

## Opsi 2 (belum dikerjakan)
Tangkap `TokenMismatchException` pada `/login` di `bootstrap/app.php` (`withExceptions`) -> redirect ke `/login` dengan pesan ramah, bukan halaman 419 mentah.

## Catatan proses
- Terminal memblokir perintah gabungan panjang (`cd && grep ... ; git status ...` dengan banyak alternasi/pipe): pisahkan per panggilan.
