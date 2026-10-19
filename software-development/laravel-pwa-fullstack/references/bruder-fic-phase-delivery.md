# Bruder FIC PWA Phase-Gated Delivery Notes

Session-derived reference for Laravel/PWA work with Yohsan/Sandi, especially mobile-reviewed admin/user dashboards.

## Durable Patterns

### Phase-gated implementation
- When user requests “fase/tahap”, implement exactly that phase and stop.
- Provide a live HTTPS link after each phase.
- For backend-only phases, create a lightweight read-only check page (e.g. `/super-admin/fase-1-check`, `/super-admin/fase-2-check`) rather than building full later-phase UI.
- Keep phase check pages mobile-first and visually polished because user verifies on a phone.

### Laravel + Cloudflare Tunnel session fixes
Use these before asking user to test login:
- `.env`: `APP_URL=https://<tunnel-or-domain>`.
- `.env`: use `SESSION_DRIVER=file` if `sessions` table is not ready.
- `bootstrap/app.php`: `$middleware->trustProxies(at: '*');`.
- `AppServiceProvider`: `URL::forceScheme('https')` when `HTTP_X_FORWARDED_PROTO === 'https'` or `APP_URL` is HTTPS.
This prevents common `419 | PAGE EXPIRED` and cookie/CSRF mismatches.

### Role testing pitfall
If user sees `403` while testing admin/user pages, first check active browser session role. Switching from `userdemo` to `superadmin` in the same mobile browser requires logout/session reset. Do not assume route/middleware is broken until session role is verified.

### Mobile UX corrections
- Every sub-page/form needs a clear back button in header (`←`) or a full-width “Kembali” button.
- Use `Plus Jakarta Sans` + `Inter` explicitly in standalone Blade pages; mobile browsers may otherwise show ugly fallback fonts.
- Full-width bottom actions are preferred over small floating squares unless intentionally using FAB.
- Screenshot markups/circles are targeted feedback: fix that exact component first.

### User profile/account forms
For religious/community PWA user management, account creation may need identity fields beyond credentials:
- `birth_date`
- `parents_name`
- `last_education`
- `entry_year`
- `community_location`
- `phone`
- `bio`
Add DB columns, model `$fillable`, casts (`birth_date` date, `entry_year` int), validation, and show these fields in track record.

### Report/reflection forms
For formation/reflection modules:
- Enforce 200–500 character limit both backend and frontend.
- Add live character counters with red (<200 or >500) and green (within range).
- Support logbook/proof uploads: JPG/PNG/PDF max 5MB, stored under `storage/app/public/logbooks/...`.

### Git & VPS Deployment / Push Pattern
- Repository remote di VPS awal menggunakan HTTPS (`https://github.com/...`) yang meminta kredensial saat `gh` tidak terinstal.
- VPS telah memiliki SSH key aktif untuk akun `sancall2707-create`.
- Sebelum push dari VPS, ubah remote ke SSH: `git remote set-url origin git@github.com:sancall2707-create/<repo>.git`.
- Pastikan berkas agent lokal seperti `/.hermes` masuk ke `.gitignore` sebelum melakukan `git add` dan commit.
- Ketika aset/fitur (seperti logo, ikon PWA, atau layout) dilaporkan belum muncul setelah `git pull origin main`, periksa seluruh remote branch via `git branch -a` dan `git log --all --grep="<keyword>" --oneline`. Seringkali pekerjaan berada di feature branch (misal `origin/cursor/...`). Lakukan checkout branch feature terkait atau tanyakan apakah ingin di-merge.
- Saat menggabungkan (*merge*) feature branch Cursor ke `main`, jika timbul konflik pada `routes/web.php` atau Controller/View yang sedang dikerjakan secara paralel, teliti bagian konflik dengan cermat. Seringkali branch fitur memuat implementasi final terlengkap. Gunakan strategi resolusi terpadu, jalankan `php artisan test` untuk memastikan semua skenario fitur tetap lolos (*PASS*), lalu bersihkan cache (`php artisan optimize:clear`) sebelum melakukan commit merge dan push ke `origin/main`.
- Untuk PWA offline support dan kompresi media: sediakan `public/sw.js` untuk cache statis serta service kompresi gambar (seperti `SapaanImageCompressor`) agar gambar profil dan sapaan tidak membebani kuota atau memperlambat render mobile.

### Multi-Tier Dashboard Architecture (User vs Admin TPPBM vs Super Admin)
- **User (Bruder Muda)**: Formasi rohani harian, input laporan bimbingan/wawanhati (200-500 karakter), jurnal refleksi, agenda, dan kalender.
- **Admin (TPPBM / Pendamping)**: Pemantauan pembinaan rohani — statistik kepatuhan bulanan, direktori bruder muda, rekam jejak bimbingan/jurnal, feed laporan terbaru, dan rilis pengumuman/sapaan pendamping. Tidak memiliki akses CRUD akun bruder atau kontrol sistem.
- **Super Admin**: Pengendali penuh sistem teknis dan manajemen pengguna (tambah akun baru, aktivasi/nonaktifkan, hapus akun).
- **Route Authorization Split**: Rute monitoring, direktori pengguna, dan sapaan dapat diakses oleh `role:admin,super_admin`. Hanya aksi berdampak tinggi (`users.create`, `users.store`, `users.status`, `users.destroy`) yang diisolasi eksklusif pada `role:super_admin`.

### Mobile Layout & Fixed Bottom Navigation Spacing
- Pada aplikasi PWA dengan layout mobile (`max-width: 480px; margin: 0 auto;`), bilah navigasi bawah tetap (`position: fixed; bottom: 0; left: 50%; transform: translateX(-50%)`) wajib memiliki `box-sizing: border-box`.
- Kontainer pembungkus halaman (`.sa-body` atau `.container`) WAJIB memiliki `padding-bottom: 90px`–`100px`. Jika padding bawah kurang, kartu, tombol, atau daftar di posisi paling bawah akan terpotong atau tertutup navigasi saat digulir (*scrolled*).
- Navigasi bawah harus mengarahkan tombol "Dashboard" secara dinamis berdasarkan peran aktif: `auth()->user()->role === 'admin' ? route('admin.dashboard') : route('superadmin.dashboard')`.

### Background Tunnel & Process Management di VPS
- Ketika background process `php artisan serve` atau `cloudflared` mati/terhenti (misal saat restart atau pembersihan memori), port dev lokal (seperti 8022) berhenti mendengarkan (*listen*).
- Cek port terlebih dahulu dengan `ss -tlpn | grep <port>`.
- Jika belum aktif, jalankan service di background: `cd <project_dir> && php artisan serve --host=127.0.0.1 --port=<port>` (background=true).
- Jalankan cloudflared tunnel di background dengan watch pattern `trycloudflare.com` untuk menangkap domain HTTPS publik instan.
- Selalu verifikasi respons HTTP dengan `curl -s -o /dev/null -w "%{http_code}" https://<domain>/login` (harus 200).

## Verification Checklist
- `php -l` new PHP files/controllers.
- `php artisan route:list | grep <feature>`.
- `php artisan view:clear && php artisan route:clear` after Blade/route changes.
- Login with curl + cookie jar to verify protected routes.
- `npm run build` after frontend/CSS/Blade asset changes.
- Mobile browser screenshot review before advancing to next phase.
