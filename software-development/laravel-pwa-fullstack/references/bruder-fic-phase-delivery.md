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
- **Istilah Baku Bahasa Indonesia (Beranda vs Dashboard)**: Ganti semua istilah serapan bahasa Inggris "Dashboard" menjadi kata baku bahasa Indonesia **"Beranda"** pada seluruh teks antarmuka (*Beranda Bruder Muda*, *Beranda Super Admin*, *Beranda TPPBM*, *Kembali ke Beranda*).
- **Profil Mandiri Super Admin & Admin TPPBM**: Sediakan halaman dan menu khusus bagi Super Admin dan Admin untuk mengedit profil pribadi (`/super-admin/profil`), mencakup avatar, nama lengkap, username (permanen), email, nomor telepon, komunitas tugas, bio, dan form ubah kata sandi mandiri.
- **Tarik Pesan Satu Arah (*Direct Message Retraction*)**: Tombol tarik pesan disediakan pada riwayat kiriman form maupun halaman rekam jejak agar pengirim dapat membatalkan pesan khusus yang salah kirim.
- **Perapian Form & Avatar Terpusat (*Center Alignment*)**: Avatar foto profil/inisial pada formulir profil wajib berada tepat di tengah (*center horizontal*), diikuti judul bagian dan nama yang simetris di bawahnya. Sembunyikan bilah navigasi bawah pada form panjang/edit (`$hideBottomNav = true`) untuk mencegah tab navigasi menutupi konten form atau tombol aksi simpan.
- **Kelola Akun & Penyuntingan Biodata Lengkap oleh Super Admin**: Pada antarmuka Super Admin (`/super-admin/users/{user}/kelola-akun`), jangan membatasi aksi hanya pada email dan sandi. Sediakan form penyuntingan lengkap mencakup nama lengkap, tempat/tanggal lahir, kontak, data keluarga, pendidikan, formasi religius, dan penugasan komunitas. Kirimkan penanda `update_biodata = 1` agar pengujian keamanan regresi lama (yang menguji proteksi manipulasi payload) tetap lulus secara backward-compatible.
- **Ekstraksi PDF Dokumen Spesifikasi via Venv Sementara**: Saat menerima dokumen spesifikasi atau revisi berformat PDF sementara host belum memiliki modul PDF (`pypdf`, `pymupdf`), gunakan venv sementara (`python3 -m venv /tmp/pdfvenv && /tmp/pdfvenv/bin/pip install pymupdf`) untuk membaca teks dan mengekstrak gambar rancangan mockup secara presisi.

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
- **Sinkronisasi Perubahan Data Uji VPS (SQLite & Upload Media) ke Repositori Git**:
  - Ketika pengguna menguji aplikasi dan membuat data baru (seperti akun bruder baru `brunofic`, sapaan rohani, atau laporan) via antarmuka web di VPS, data tersebut tersimpan di `database/database.sqlite` dan `storage/app/public/`.
  - Karena berkas `.sqlite` dan `storage/app/public/*` dikecualikan oleh `.gitignore`, perintah `git status` akan menampilkan `working tree clean`, sehingga perubahan data tersebut tidak otomatis terunggah ke GitHub.
  - Untuk mem-push perubahan data tersebut:
    1. Periksa entitas baru via Tinker (`App\Models\User::withTrashed()`, `ProvincialMessage::all()`, dll).
    2. Masukkan data akun baru ke `database/seeders/UserSeeder.php` dengan hash password dan atribut lengkapnya.
    3. Buat seeder tambahan (misal `PembinaanDataSeeder.php`) untuk data sapaan/pengumuman dan laporan uji coba, lalu daftarkan ke `DatabaseSeeder.php`.
    4. Buat dump SQL menggunakan skrip Python (`sqlite3.connect().iterdump()`) ke berkas `database/database_seed.sql` agar seluruh struktur dan baris data terlacak di Git.
    5. Jalankan `php artisan test`, commit, dan lakukan push ke `main`.
- Untuk PWA offline support dan kompresi media: sediakan `public/sw.js` untuk cache statis serta service kompresi gambar (seperti `SapaanImageCompressor`) agar gambar profil dan sapaan tidak membebani kuota atau memperlambat render mobile.

### Multi-Tier Dashboard Architecture (User vs Admin TPPBM vs Super Admin)
- **User (Bruder Muda)**: Formasi rohani harian, input laporan bimbingan/wawanhati (200-500 karakter), jurnal refleksi, agenda, kalender, dan kotak pesan khusus privat.
- **Admin (TPPBM / Pendamping)**: Pemantauan pembinaan rohani — statistik kepatuhan bulanan, direktori bruder muda, rekam jejak bimbingan/jurnal, feed laporan terbaru, rilis pengumuman/sapaan pendamping, penambahan catatan pembinaan berjenjang, dan pengiriman pesan khusus satu arah. Tidak memiliki akses buat/hapus akun bruder atau kontrol sistem.
- **Super Admin**: Pengendali penuh sistem teknis dan manajemen pengguna (tambah akun baru dengan penetapan peran User/Admin, aktivasi/nonaktifkan, hapus akun, reset kata sandi, dan kelola peran).
- **Route Authorization Split**: Rute monitoring, direktori pengguna, sapaan, penambahan catatan pembinaan (`users.notes.*`), dan pengiriman pesan satu arah (`users.messages.*`) dapat diakses bersama oleh `role:admin,super_admin`. Hanya aksi berdampak tinggi (`users.create`, `users.store`, `users.status`, `users.destroy`) yang diisolasi eksklusif pada `role:super_admin`.

### Penyesuaian Formasi & Fitur Lanjutan Tahap 1 (Pesan Satu Arah, Catatan TPPBM, & Biodata Lengkap)
1. **Penetapan Peran (Role) oleh Super Admin**:
   - Super Admin dapat menentukan role saat membuat akun (`user` atau `admin`) dan dapat memperbarui peran di halaman kelola akun.
2. **Pesan Satu Arah Privat (Direct Messaging)**:
   - Super Admin dan Admin TPPBM dapat mengirimkan pesan arahan khusus satu arah (`direct_messages` table dengan `title`, `content`, `read_at`).
   - Sisi user menampilkan lencana notifikasi dan kartu perhatian di Dashboard jika ada pesan belum terbaca (`read_at IS NULL`), dengan rute baca detail yang otomatis menandai pesan telah dibaca.
3. **Catatan Pembinaan TPPBM (Mockup Halaman 6)**:
   - Ditambahkan tombol aksi hijau `Tambahkan Catatan` pada tiap kartu bruder di daftar direktori.
   - Form catatan menyediakan dropdown kategori: *Catatan Hidup Pribadi*, *Catatan Hidup Rohani/Doa*, *Catatan Hidup Komunitas*, *Catatan Hidup Kerasulan*, *Catatan Hidup Triprasetia*, dengan textarea uraian catatan bebas tanpa batas karakter.
   - Catatan otomatis tersimpan ke tabel `bruder_notes` dan tampil pada halaman Track Record Individual bruder serta Raport Pendampingan.
4. **Penggantian / Penghapusan Foto Media pada Sapaan**:
   - Form ubah (edit) sapaan menampilkan pratinjau foto yang sedang aktif, opsi berkas baru untuk mengganti foto dengan kompresi otomatis (`SapaanImageCompressor`), serta checkbox eksplisit `remove_image` untuk menghapus foto lampiran jika ingin beralih ke teks murni.
5. **Ekspansi Profil Terstruktur via Kolom JSON**:
   - Untuk data keluarga, narahubung darurat, pendidikan berjenjang (SD, SMP, SMA/SMK, S1, S2), formasi religius (Postulat, Novisiat Kanonik/Apostolik, Prasetia Pertama, Pembaruan 1-6), dan riwayat penugasan komunitas (Tugas 1-6), simpan dalam kolom JSON (`family_data`, `education_data`, `formation_data`, `assignment_data`) dengan cast `array` di Eloquent.
   - Pertahankan sinkronisasi otomatis ke kolom flat ringkas (`parents_name`, `last_education`, `entry_year`) saat form profil disimpan untuk menjamin kompatibilitas mundur (*backward compatibility*).

### Otomatisasi Status Selesai pada Jadwal & Laporan Pembinaan
- Jadwal bimbingan rohani (`SpiritualGuidanceSchedule`) dan wawanhati (`WawanhatiSchedule`) awalnya berstatus `scheduled` ("Menunggu").
- Ketika bruder muda mengisi dan mengirimkan formulir laporan/renungan bimbingan atau wawanhati (`SpiritualGuidanceController::store` / `WawanhatiController::store`), sistem harus otomatis:
  1. Mencari jadwal pada tanggal pertemuan atau mentor/pimpinan terkait.
  2. Memperbarui status jadwal menjadi `completed` ("Selesai").
  3. Menghubungkan ID jadwal ke kolom `schedule_id` pada baris laporan baru.
- Pada `MonitoringQuery::row`, status `submitted` dipetakan sebagai `Selesai` (`status_done = true`), bukan `Menunggu`.
- Pada `MonitoringQuery::agendas`, kueri memeriksa apakah ada laporan tersimpan untuk tanggal pertemuan tersebut agar jadwal otomatis berstatus `Selesai` secara real-time.

### Filter Rentang Periode Kustom (1–12 Bulan)
- Form monitoring dan ekspor data menyediakan dua dropdown bulan: `Dari Bulan` (`bulan`) dan `Sampai Bulan` (`bulan_akhir`), berdampingan dengan `Tahun`.
- Gunakan kueri SQL tanggal portabel `whereBetween($column, [$start, $end])` dari tanggal 1 awal bulan pertama hingga akhir bulan kedua. Pendekatan ini aman dan optimal di SQLite, MySQL, dan PostgreSQL.
- Label periode otomatis beradaptasi: `Januari – Agustus 2026` jika memilih rentang jamak, atau `Oktober 2026` jika satu bulan.
- Nama file ekspor Excel/PDF otomatis mencantumkan slug rentang: `rekap-laporan-2026-01_sd_08.xls`.

### Pemisahan Modul Raport Resmi A4 vs Laporan Jurnal Eksisting (Dual-Tab Architecture)
- Pada modul monitoring evaluasi pembinaan, sediakan dua tab utama:
  1. **Tab 1: Raport Pendampingan Bruder Muda** (`/super-admin/monitoring/raport`):
     - Format dokumen resmi dinas Kongregasi FIC siap cetak (A4) berbasis tabel terstruktur:
       - KOP Resmi dengan logo FIC dan unit TPPBM.
       - Seksi A: Data Diri & Kredensial.
       - Seksi B: Data Keluarga & Kontak Darurat (Orang Tua, Saudara, Narahubung).
       - Seksi C: Riwayat Pendidikan Formal (SD, SMP, SMA/K, S1, S2).
       - Seksi D: Tahapan Formasi Religius FIC (Postulat s/d Pembaruan ke-6).
       - Seksi E: Komunitas Tinggal & Perutusan (Tugas 1 s/d 6).
       - Seksi F: Laporan Pelaksanaan Bimbingan Rohani per bulan dengan indikator visual `✓` (Hijau) / `✗` (Merah).
       - Seksi G: Laporan Pelaksanaan Wawanhati Pimpinan Lokal per bulan dengan indikator `✓` / `✗`.
       - Seksi H: Laporan Kegiatan Jurnal Pengembangan Diri (Pengembangan 01, 02...).
       - Seksi I: Catatan Pendamping TPPBM (5 pilar: Pribadi, Rohani/Doa, Komunitas, Kerasulan, Triprasetia).
       - Lembar Pengesahan & Tanda Tangan: Ketua TPPBM dan Administrator Data.
       - Tombol cetak langsung via `window.print()` dengan CSS `@media print` yang mengisolasi kertas raport dan menyembunyikan elemen UI dashboard.
  2. **Tab 2: Laporan Jurnal & Bimbingan** (`/super-admin/monitoring`):
     - Mempertahankan format eksisting: kartu feed kronologis, filter rentang bulan, pencarian per bruder, dan ekspor data Excel & PDF.

### Dokumentasi Arsitektur Sistem (`DESIGN.md`) & Distribusi Dokumen Native Media
- Untuk proyek aplikasi PWA berskala produksi, sediakan berkas `DESIGN.md` komprehensif pada akar repositori yang mencakup:
  1. Ringkasan Eksekutif & Instrumen Formatif.
  2. Arsitektur Teknologi & Dependensi (Laravel 11, SQLite, PWA, Caddy/Cloudflare).
  3. Design System (Mobile-first, palet warna resmi hex, tipografi, glassmorphism, avatar terpusat).
  4. Matriks Peran Pengguna & Hak Akses (Super Admin, Admin TPPBM, Bruder Muda).
  5. Skema Basis Data & Diagram Relasi Entity.
  6. Spesifikasi Format Raport Pendampingan A4 & Tanda Tangan Resmi.
  7. Otomatisasi Status & Filter Rentang Periode.
- Ketika pengguna meminta berkas fisik melalui antarmuka Telegram, kirimkan file secara native menggunakan format tag: `MEDIA:/path/absolut/ke/berkas`.

### Inventaris Akun & Otentikasi Seeder/UI
- Dokumentasikan pola kredensial akun sistem secara konsisten:
  - Super Admin: username `superadmin` / `SuperAdmin#FIC2026`
  - Admin TPPBM: username `admin` / `Admin#FIC2026`
  - Demo Seeder: username `userdemo`, `bruder_anton` / `User#FIC2026`
  - Akun Riil/Tambah Form UI: `poerw`, `brunofic`, `agsuparno`, `galihsih` / `123456`
  - Simpan dan sinkronkan akun riil ke `database/seeders/UserSeeder.php` dan `database/database_seed.sql` agar tidak hilang saat migrasi ulang.

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
