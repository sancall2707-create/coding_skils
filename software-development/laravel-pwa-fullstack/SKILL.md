---
name: laravel-pwa-fullstack
description: Full-stack Laravel 11 + Vue 3 SPA + PWA development pattern with Sanctum auth, conflict detection, role-based dashboards, and production deployment.
tags: [laravel, vue3, pwa, sanctum, fullstack]
---

# Skill: Laravel PWA Full-Stack Development

Complete pattern for building production-ready PWA applications with Laravel 11 backend, Vue 3 SPA frontend, Sanctum authentication, and role-based access control.

## Scope
- Laravel 11 REST API with Sanctum token auth
- Vue 3 SPA frontend with Vue Router & Pinia state management
- PWA setup (manifest, service worker, install prompts)
- Business logic patterns (conflict detection, temporal/spatial constraints)
- Role-based multi-dashboard UI (Super Admin, Unit Admin, User)
- Production HTTPS deployment via Caddy or other reverse proxy

## Architecture Overview

### Backend (Laravel 11)
- **Database**: MariaDB with polymorphic relationships for flexible data modeling
- **Authentication**: Laravel Sanctum for API token-based auth
- **Authorization**: Policy-based gate system for resource-level permission checks
- **Business Logic**: Service classes (e.g., `BookingConflictService`) for complex validation
- **API Structure**: RESTful routes under `/api/*` with JSON responses

### Frontend (Vue 3)
- **Build Tool**: Vite (Laravel Vite plugin)
- **Routing**: Vue Router with protected routes via meta guards
- **State**: Pinia for auth store, booking store, and global state
- **UI**: Tailwind CSS responsive components
- **HTTP**: Axios with Bearer token injection for API calls

### PWA Essentials
- **Manifest**: `public/manifest.json` (standalone display, theme color, icons)
- **Service Worker**: `public/sw.js` (selective caching — **security critical**)
- **Install Button**: Floating UI component that triggers `beforeinstallprompt` event
- **HTTPS Requirement**: PWA features only work over HTTPS (mandatory for production)

## Critical Steps (Mandatory)

### 1. Setup & Project Structure
1. Create Laravel project: `composer create-project laravel/laravel app`
2. Install dependencies: Sanctum, Vite Vue plugin, Tailwind CSS
3. Create Vue app entry: `resources/js/app.js` with router, Pinia, and Vite CSS import
4. Create Blade host: `resources/views/welcome.blade.php` with `<div id="app"></div>` and Vite asset tags
5. Setup Caddy/nginx to reverse proxy PHP-FPM socket and serve public folder

### 2. Database & Models
1. Create migrations for business entities (avoid over-normalization; use polymorphic relationships where appropriate)
2. Seed initial data for testing (users with roles, demo fixtures)
3. Use soft deletes or status columns for audit trails (never hard-delete production data)

### 3. Authentication & Authorization
1. Add `HasApiTokens` trait to User model
2. Use `Sanctum` middleware for protected API routes
3. Create Policy classes for each resource (e.g., `BookingPolicy`, `VehiclePolicy`)
4. Use `Gate::authorize()` in controllers to enforce policies
5. Test token expiry, refresh logic, and logout token revocation

### 4. Business Logic (Service Classes)
1. Extract complex validation into dedicated service classes (e.g., `BookingConflictService`)
2. Service should be stateless and injectable via constructor
3. Write comprehensive test cases for boundary conditions (date overlaps, time ranges, constraints)
4. Call service consistently from both `store()` and `updateStatus()` endpoints

### 5. Frontend State & Routing
1. Create Pinia stores for auth (login/logout, user state, token storage) and domain logic (bookings, filters)
2. Setup Vue Router guards: `beforeEach` for auth checks, meta-based role restrictions
3. **IMPORTANT**: Store auth token in localStorage, not sessionStorage (survives page refresh for PWA)
4. Inject token into every API request via Axios interceptor

### 6. PWA Assembly
1. Create `public/manifest.json` with app name, icons (512x512 SVG/PNG), theme color, display mode `standalone`
2. Create `public/sw.js` with **strict caching rules** (see `references/service-worker-security.md`)
3. Add PWA meta tags to Blade host (apple-mobile-web-app, theme-color, icons)
4. Add Service Worker registration script + `beforeinstallprompt` handler to capture install event
5. Create floating Install Button component (`resources/js/components/InstallPwaButton.vue`)

### 7. Testing & Verification
1. **API**: Use curl or Python to test all endpoints (auth, CRUD, conflict scenarios)
2. **Build**: Run `npm run build` and verify no Vite/Vue compiler errors
3. **Permissions**: Check `public/manifest.json`, `public/sw.js`, icon files are world-readable
4. **Manifest**: Fetch and validate JSON structure (`curl http://localhost/manifest.json | jq .`)
5. **Conflict Logic**: Test boundary cases (same-day full-date conflict, overlapping time ranges)

### 8. Deployment to HTTPS
1. Use domain-based SSL (Caddy auto-renews Let's Encrypt via DNS challenge)
2. Or use internal SSL for testing (Caddy `tls internal` for self-signed certs)
3. Update Laravel `.env`: `APP_URL=https://your-domain.com`
4. Verify PWA installable via Chrome DevTools Application → Manifest tab
5. Test on mobile (iOS Safari or Android Chrome) to ensure install prompt appears

## Pitfalls & Common Issues

### Vue 3 Compilation
- **Error**: `v-else has no adjacent v-if` → Check template structure; `v-else` must directly follow `v-if` in same element/parent
- **Error**: Multiple root elements in `<template>` → Wrap multiple sections in `<template v-if>` or single root `<div>`
- **Fix**: Use `<template v-if="condition">` block elements to group logically without adding DOM wrapper

### Service Worker & Caching
- **Pitfall**: Caching HTML pages with old Vite asset hashes → After deployment, browser renders HTML with `<script src="...app-OldHash.js">` but SW cache cleared old hash. Blank page.
- **Pitfall**: Service Worker registration waiting for `load` event → Event may already fire before script registers. Browser does not activate SW until next reload.
- **Fix**: Register SW immediately (no `addEventListener('load')`). Append version query: `/sw.js?v=1` to bypass HTTP browser cache on SW.js itself.
- **Fix**: HTML navigation MUST be Network-First (`event.request.mode === 'navigate'`). Only Vite build hashed assets (`/build/assets/*`) are Cache-First.
- **Rule**: Evict ALL old cache versions immediately in `activate` event (`if (cache !== CACHE_NAME)`). No gradual migration.
- **Test**: Deploy new SW version, check browser DevTools Application tab → Service Worker shows `activated` state. Check Cache Storage → old cache names gone.

### Reverse Proxy & HTTPS Detection
- **Pitfall**: Laravel Error 419 (CSRF / Page Expired) or Mixed Content behind Cloudflare Tunnel / Reverse Proxy → Laravel running on HTTP behind tunnel sends HTTP session cookies / mismatched CSRF origin.
- **Fix 1**: In `bootstrap/app.php` (Laravel 11/12): Add `$middleware->trustProxies(at: '*');` so Laravel inspects `X-Forwarded-Proto` and `X-Forwarded-Host`.
- **Fix 2**: In `app/Providers/AppServiceProvider.php`: Call `URL::forceScheme('https')` when `HTTP_X_FORWARDED_PROTO === 'https'` or `APP_URL` contains `https://`.
- **Fix 3**: In `.env`: Set `APP_URL=https://<your-tunnel-domain>` and use `SESSION_DRIVER=file` (if DB session table is not migrated or schema mismatch).
- **Pitfall**: HTTP redirect loop (`ERR_TOO_MANY_REDIRECTS`) behind Cloudflare Tunnel → Caddy configured with `:443` or `tls internal` but receives HTTP from tunnel. Sends 308 redirect back, infinite loop.
- **Fix**: Use `:80` in Caddyfile (no TLS directives) when behind reverse proxy. Let tunnel handle SSL termination.
- **Pitfall**: Mixed Content error (HTTPS page + HTTP Vite assets) → Laravel running on HTTP port 80 generates `http://` URLs for assets. Browser blocks mixed content.

### Mobile PWA UI & Typography Hygiene
- **Pitfall**: Missing back button (`←`) in sub-page headers → User gets stuck on inner views (`/super-admin/users`, `/monitoring`) without intuitive navigation back to main dashboard.
- **Fix**: Every sub-page header MUST include a clear back button (`←` or `← Kembali`) in the top navigation bar, linking back to the parent dashboard or list view.
- **Pitfall**: Inconsistent system font fallbacks (e.g. mobile browser falling back to cursive/handwritten/monospace system fonts) or misaligned floating buttons on small screens.
- **Fix**: Explicitly preload Google Fonts (`Plus Jakarta Sans` & `Inter`) in `<head>`, use standard mobile shell container (`max-width: 480px; margin: 0 auto;`), and ensure action buttons use full width (`width: 100%`) with proper padding and icon alignment rather than small absolute/floating blocks.
- **Avoid Duplicate Action Icons and Literal Symbols in Buttons**: Jangan menggabungkan ikon visual (seperti SVG plus `+` atau ikon tong sampah) dengan karakter simbol teks yang sama di dalam label tombol (misal: `<svg>plus</svg> + Tambah Agenda`). Hal ini menyebabkan tampilan ganda yang janggal di mata pengguna (`+ + Tambah Agenda`). Gunakan **hanya** ikon SVG atau simbol teks, tidak keduanya secara bersamaan: `<svg>...</svg> <span>Tambah Agenda</span>`.
- **User review pattern**: When a user marks/circles a UI element in a screenshot, treat it as targeted feedback on that component. Fix the specific visual problem first (size, positioning, alignment, tap target, whitespace) before broad redesign.
- **Profile Avatar Centering in Forms**: Jangan pernah menaruh thumbnail foto profil / avatar di tepi kiri formulir. Posisikan avatar tepat di tengah secara horizontal (`margin: 0 auto 10px; display: block; border-radius: 50%`) dengan bingkai rapi, diikuti nama dan username terpusat di bawahnya.
- **Consistent Back Navigation in Subpages**: Jangan menaruh tombol teks kembali melayang di pojok kanan kartu konten (seperti `← Ke Beranda`). Gunakan layout subheader standar PWA dengan tombol panah kembali (`<` back button) yang konsisten di baris navigasi atas.
- **Bottom Navigation Conflict on Long Forms**: Pada halaman pengisian atau penyuntingan formulir panjang, sembunyikan bilah navigasi bawah (`$hideBottomNav = true`) atau beri margin dasar minimal `100px` agar tombol aksi simpan tidak tertutup oleh navigasi bawah saat keyboard virtual terbuka.
- **Role Session Mismatch in Testing**: When switching between User and Admin test links in the same browser, active session cookies can trigger `403 Access Denied`. Remind user to logout or use clear account switching.

### Phase-Gated Feature Delivery for User-Reviewed PWAs
- **Preference**: For large Laravel/PWA builds, implement one phase at a time and stop for user review. Do not continue to the next phase until the user explicitly approves the current phase.
- **Required deliverable after each phase**: Provide a live HTTPS check link (Cloudflare Tunnel link if available), test credentials if needed, and a concise list of changed files + executed verification commands.
- **Implementation pattern**: For backend-only phases, create a small read-only verification route/page such as `/super-admin/fase-1-check` or `/super-admin/fase-2-check` that demonstrates the new backend/model/service output without prematurely building later-phase UI.
- **Scope control**: If a plan says “Fase 1: database/model” or “Fase 2: backend services,” avoid sneaking in full UI/UX work from later phases. Minimal diagnostic pages are allowed only to let the user check the phase.
- **Git Push & Fast-Forward Synchronization**: When collaborating across external agents (e.g. Cursor agent) and VPS, check `git status` and `git fetch origin` before starting work. If commits exist remotely, run `git pull origin main` (fast-forward) and verify tests/caches (`php artisan optimize:clear && php artisan test`) before making local modifications.
- **Multi-Branch & Cursor Feature Branch Detection**: When the user asks "ambil perubahan baru" or notes that changes (e.g. logo, icons, UI adjustments) are missing after `git pull origin main`, check active remote branches with `git for-each-ref --sort=-committerdate refs/remotes/`. Cursor Agent frequently pushes to topic branches like `origin/cursor/<feature-name>-<id>` instead of `main`. Use `git log --all --grep="<keyword>"` to find the commit, merge the topic branch into `main` (resolving conflicts in favor of the newer feature files if needed), run `php artisan migrate`, and clear view/route caches.
- **Runtime User Data & SQLite / Storage Git Synchronization**: When users test features and add entities (e.g. new users, provincial messages, test reports) via the web interface on VPS, Laravel's `.gitignore` ignores `*.sqlite*` and `storage/app/public/*`. Consequently, `git status` displays `working tree clean` and the user's manual records are absent from GitHub. To preserve these changes:
  1. Inspect runtime records via Tinker (`User::withTrashed()`, `ProvincialMessage::all()`, etc.).
  2. Back-port newly registered users and records into `database/seeders/UserSeeder.php` and domain seeders (e.g. `PembinaanDataSeeder.php`), wired into `DatabaseSeeder.php`.
  3. Export a clean SQLite dump (`database/database_seed.sql`) using a Python script (`sqlite3.connect().iterdump()`) so the database state is tracked in git.
- **Language Policy**: Always explain and report deployment, sync, git actions, and verification links strictly in Indonesian for this user. Avoid reverting to English even in terse/system output.
- **Operational Admin vs Super Admin Separation**: In multi-stakeholder PWA formations, distinguish system management (Super Admin: create/delete users, password resets) from operational monitoring (Admin: viewing reports, calendar/agenda, formation notes, one-way direct messaging). Share monitoring views across both roles while scoping destructive actions.
- **Direct One-Way Messaging & In-App Alerts**: Implement sender-to-recipient direct messaging (`direct_messages` table with `read_at`) for private leadership directives. Surface an unread alert banner on the PWA dashboard with direct navigation to the message reader.
- **Structured Biographical Data via JSON Columns**: Avoid dozens of flat columns for complex profile histories (family, emergency contacts, multi-tier education, religious formation stages, community assignment history). Store grouped arrays cast to `array` in Eloquent while maintaining synced legacy summary strings (`parents_name`, `last_education`, `entry_year`) for backward compatibility.
- **Media Replacement & Removal in Edit Views**: When editing media-rich posts (e.g. sapaan/announcements), provide a clear image preview, an upload field to replace with compressed output, and an explicit checkbox (`remove_image`) to allow reverting to text-only mode.
- **Indonesian UI Terminology (Beranda vs Dashboard)**: Ganti kata serapan bahasa Inggris "Dashboard" menjadi kata baku bahasa Indonesia **"Beranda"** pada seluruh teks antarmuka (*Beranda Bruder Muda*, *Beranda Super Admin*, *Beranda TPPBM*, *Kembali ke Beranda*). Label navigasi, breadcrumb, header, dan tooltip wajib konsisten memakai "Beranda".
- **Dedicated Profile Management for Administrators**: Sediakan halaman dan menu khusus bagi Super Admin dan Admin untuk mengedit profil mereka sendiri (`/super-admin/profil`: avatar, nama, email, nomor telepon, komunitas, bio, serta formulir ganti kata sandi mandiri), terpisah dari fitur kelola akun bruder/pengguna lain. Sediakan tombol kembali (*Kembali ke Beranda Super Admin / TPPBM*) saat admin mengakses tampilan PWA.
- **Direct Message Retraction (Tarik Pesan)**: Fitur pesan khusus satu arah dari pimpinan/admin ke pengguna wajib dilengkapi fungsi tarik/hapus pesan (*retract message*) yang dapat dilakukan langsung dari riwayat kirim form maupun dari halaman rekam jejak (*track record*) untuk mengantisipasi kesalahan kirim.
- **Super Admin Complete Profile Management**: Pada menu kelola akun bruder (`/super-admin/users/{user}/kelola-akun`), jangan batasi hanya pada email dan sandi. Sediakan form penyuntingan lengkap mencakup data pokok, tempat/tanggal lahir, kontak, data keluarga & narahubung, pendidikan formal SD–S2, tahapan formasi religius, dan riwayat penugasan komunitas. Pastikan pengujian kompatibilitas tetap lolos dengan menyertakan penanda `update_biodata`.
- **Ephemeral Venv for PDF Extraction**: Bila sistem tidak memiliki pustaka ekstraksi dokumen biner (`pypdf`/`pymupdf`), gunakan venv sementara (`python3 -m venv /tmp/pdfvenv && /tmp/pdfvenv/bin/pip install pymupdf`) agar teks dan lampiran visual dokumen PDF dapat dibaca secara akurat tanpa mencemari sistem global.
- **Formation Report Status Automation**: Saat bruder mengirimkan laporan renungan (`SpiritualGuidanceReport` / `WawanhatiReport`), otomatis perbarui status jadwal agenda terkait menjadi `completed` ("Selesai") dan hubungkan `schedule_id`. Pada `MonitoringQuery`, petakan status `submitted` menjadi `Selesai` secara real-time.
- **Custom Month Range Filter (1–12 Bulan)**: Sediakan filter rentang `bulan` ke `bulan_akhir` dengan kueri `whereBetween` pada tanggal awal dan akhir bulan agar aman dan kompatibel lintas database (SQLite, MySQL, Postgres), serta sinkronkan penamaan file ekspor.
- **Dual-Tab Architecture: Raport A4 vs Laporan Jurnal**: Pisahkan modul evaluasi pembinaan menjadi dua tab: Tab 1 untuk dokumen resmi Raport Pendampingan (tabel formal A s/d I, logo institusi, indikator bulanan centang/silang, dan lembar tanda tangan dengan CSS `@media print`), dan Tab 2 untuk Laporan Jurnal & Bimbingan dengan format kartu feed kronologis eksisting.
- **PWA Mobile Shell Container Expansion for A4 Print**: Pada PWA mobile-first yang membatasi kontainer shell (`.container` / `.sa-container` dengan `max-width: 480px`), saat mencetak atau mengekspor PDF, kontainer akan tetap menciut menjadi kolom sempit selebar 480px (sekitar 12,7 cm) di tengah kertas A4. Pada `@media print`, wajib override kontainer induk: `.sa-container { max-width: 100% !important; width: 100% !important; margin: 0 !important; padding: 0 !important; }` dan `.sa-body { padding: 0 !important; width: 100% !important; }`. Di layar preview desktop, sediakan flag layout lebar (`$wideLayout = true`) agar kontainer melebar hingga `880px` di atas resolusi `860px`.
- **Continuous Flow vs Artificial Page Breaks in Formal Reports**: Jangan memaksa `<div class="page-break"></div>` di antara setiap seksi jika jumlah data dinamis (misal jumlah bulan bimbingan/wawanhati fleksibel 1–12 bulan), karena akan meninggalkan ruang kosong besar di bagian bawah kertas cetak. Biarkan seluruh seksi (A s/d I dan pengesahan) mengalir alami (*continuous document flow*). Gunakan `tr { page-break-inside: avoid; }`, `.raport-log-card { page-break-inside: avoid; }`, dan `.raport-signatures { page-break-inside: avoid; }` agar baris atau kartu tidak terpotong di tengah kalimat, serta `.raport-section-title { page-break-after: avoid; }` agar judul seksi tidak tertinggal sendirian di dasar halaman.
- **Print Color Adjustment for Status Badges**: Browser (Chromium, Brave, Safari) menonaktifkan pencetakan warna latar belakang (*background graphics*) secara default. Agar badge status hijau (`✔ TELAH TERLAKSANA`) dan merah (`✘ BELUM / TIDAK TERLAKSANA`) tetap tercetak berwarna, tambahkan deklarasi CSS `-webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important;` pada elemen badge dan sel tabel, serta lengkapi dengan garis tepi (*border*) berwarna kontras sebagai pengaman.
- **Dual-Logo Formal Header (Kop Surat Instansi)**: Dokumen formal raport seringkali menuntut dua logo identitas: Logo induk kongregasi di sisi kiri (`logo-fic.png`) dan Logo unit/tim di sisi kanan (`logo-tppbm.png`) dengan judul instansi rata tengah dan garis pembatas ganda (*double rule*). Ekstrak langsung logo dari lampiran PDF resmi menggunakan `pymupdf` dan daftarkan path logo baru ke dalam cache Service Worker (`public/sw.js`).
- **Standard A4 Margin Alignment**: Atur margin dokumen resmi via `@page { size: A4 portrait; margin: 1.5cm 1.5cm 1.5cm 2.0cm; }` (Atas 1,5cm, Kanan 1,5cm, Bawah 1,5cm, Kiri 2,0cm untuk batas jilid). Semua tabel dan kartu di dalamnya wajib memiliki `width: 100%` agar pas dengan lebar bidang cetak A4.
- **Role-Based Dynamic Signatures for Formal Documents**: Jangan pernah melakukan hardcode nama penandatangan (Ketua / Administrator Data) pada template cetak atau view Blade. Buat peran khusus di sistem RBAC (`admin_ketua_tppbm` dan `super_admin`), wariskan hak akses di middleware (`RoleMiddleware`), dan ambil nama penandatangan secara dinamis dari user aktif yang memegang role tersebut (`User::where('role', 'admin_ketua_tppbm')->first()`). Nama di lembar pengesahan otomatis sinkron saat akun memperbarui profilnya.
- **Differentiated User Directory Controls (Members vs Admins)**: Saat halaman manajemen akun (`/super-admin/users`) diperluas menampilkan akun staf/admin (`admin`, `admin_ketua_tppbm`, `super_admin`) berdampingan dengan anggota (`user`), pisahkan menu aksinya: anggota reguler memiliki kontrol pembinaan (`Track Record`, `Tambahkan Catatan`, `Kirim Pesan`), sedangkan admin/ketua/superadmin HANYA memiliki kontrol akun (`Kelola Akun`, `Nonaktifkan`, `Hapus`), dengan proteksi tombol hapus/nonaktif pada akun yang sedang login sendiri.
- **Guidance Notes Retract (Tarik) & Edit Lifecycle**: Modul catatan pembinaan wajib menyediakan riwayat inline dengan aksi Edit (mengubah kategori dan teks catatan) serta aksi Tarik/Hapus berdialog konfirmasi agar catatan yang salah input dapat langsung dibatalkan dari sistem dan hilang dari lembar cetak raport.
- **No Dummy/Fallback Notes in Official Reports**: Jangan pernah menampilkan teks contoh/dummy (*placeholder text*) pada seksi evaluasi resmi raport saat evaluasi belum diinput oleh pembimbing. Jika admin belum menuliskan catatan untuk aspek terkait, biarkan kosong atau tampilkan tanda hubung bersih (`-`). Teks contoh bawaan akan disalahpahami sebagai hasil evaluasi sungguhan yang difabrikasi oleh sistem.
- **Strict Disallowance of Future Dates on Retrospective Forms**: Pada formulir pencatatan kegiatan lampau (seperti laporan bimbingan rohani, wawanhati, notulensi), cegah pemilihan tanggal masa depan secara ganda: di sisi frontend batasi kalender dengan atribut HTML `max="{{ date('Y-m-d') }}"` dan di sisi backend validasi dengan aturan `'before_or_equal:today'`.
- **Formation Quota Metrics (Max Monthly & Annual Targets)**: Pada dashboard pembinaan religius, bedakan kegiatan pendampingan wajib (Bimbingan Rohani 1x + Wawanhati 1x = maksimal 2 kali sebulan, atau 24 kali setahun) dengan kegiatan refleksi mandiri (jurnal pengembangan diri). Tampilkan persentase pencapaian berbasis kuota pembinaan bulanan (`[N] / 2`) serta akumulasi tahun berjalan (`[M] / 24`).
- **Interactive Formation Checklist on Member Dashboard**: Selain angka persentase ringkas, sediakan kartu checklist interaktif di Beranda yang merinci status setiap instrumen bulan berjalan (misal: Bimbingan, Wawanhati, Jurnal) lengkap dengan tombol aksi langsung (`+ Isi Laporan` jika belum, atau `Lihat &rarr;` jika sudah terlaksana).
- **Mobile Long-Form Section Jump Bar vs Exclusive Tab Panes**: Untuk formulir profil/biodata panjang pada mobile PWA, hindari membiarkan seluruh seksi tetap bersambung ke bawah jika user meminta navigasi tab. Gunakan **Exclusive Tab Panes** (`.tab-pane { display: none; } .tab-pane.active { display: block; }`) sehingga hanya satu seksi yang tampil pada satu waktu, didukung tombol navigasi seksi bawah (*Lanjut ke seksi berikutnya*, *Kembali ke seksi sebelumnya*) dan penanganan event `invalid` otomatis untuk membuka tab yang belum valid saat submit.
- **Symmetrical Dashboard Checklist Row Layout**: Pada kartu checklist berkala di mobile dashboard, seluruh tombol aksi sisi kanan wajib memiliki dimensi fixed yang seragam (`width: 76px; height: 32px`) dengan tata letak flex center agar posisi tombol sejajar lurus simetris dari atas ke bawah, serta teks judul/subjudul diberi `min-width: 0; text-overflow: ellipsis; white-space: nowrap` agar tidak mendesak tombol aksi.
- **Strict Suppression of Future Years in Historical & Assignment Records**: Pada laporan resmi/raport, sembunyikan tahapan formasi atau riwayat penugasan komunitas yang bertahun di masa depan (tahun > tahun berjalan `now()->year`). Jika penugasan masih berlangsung ke masa depan, sajikan label mengalir sebagai `[Tahun Mulai] - Sekarang`.
- **Custom Clean Pagination View for Mobile PWA**: Jangan gunakan render default `$paginator->links()` mentah dari Laravel karena akan memuat ikon panah SVG raksasa dan teks panjang yang merusak layout mobile. Daftarkan custom pagination view (`Paginator::defaultView('vendor.pagination.custom')`) dengan tombol nomor halaman kotak kompak (`34px x 34px`), lencana info ringkas, dan panah terisolasi.
- **Universal Submit Button Loading State**: Pasang skrip pencegah klik ganda (*double-submit*) otomatis pada layout utama: saat formulir disubmit, tombol submit langsung dinonaktifkan (`disabled = true`) dan label tombol berganti menjadi animasi putar (*spinner*) bertuliskan *"Menyimpan..."*.
- **Bottom Navigation Bar for Management Mobile Views**: Bilah menu bawah (*Bottom Nav*) untuk Super Admin/Admin harus mengakomodasi menu-menu vital (Beranda, Direktori, Raport, Sapaan, Profil) dengan desain *glassmorphic* dan ikon navigasi yang konsisten. Hindari memasukkan menu ganda atau duplikatif (misalnya memisahkan Raport dan Monitoring menjadi dua tombol terpisah yang membuka controller/filter yang sama); sediakan akses sub-modul melalui tab view atas. Sertakan menu **Profil** langsung di navigasi bawah agar pengguna dapat mengakses pengaturan akun secara instan tanpa harus membuka menu hamburger. Jika ada tombol aksi mengambang (*FAB*), naikkan posisi tombol (`bottom: 80px`) agar tidak menumpuk dengan bilah navigasi bawah, dan sembunyikan navigasi bawah pada `@media print`.
- **Dual Horizontal Circular Progress Indicators for Multi-Tier Progress Tracking**: Saat menampilkan metrik kepatuhan berkala (misal: target akumulasi tahunan 24 vs target bulanan 2), jangan menaruh hanya satu lingkaran atau menyisakan ruang kosong besar asimetris di kartu dashboard. Letakkan dua circular SVG progress indicator (`width: 68px`) berdampingan secara horizontal di sisi kiri: lingkaran kiri untuk akumulasi tahun berjalan (1 Januari s.d. tanggal saat ini, tidak ter-reset saat ganti bulan), lingkaran kanan untuk capaian bulan berjalan (otomatis reset ke 0/2 tiap ganti bulan baru). Sisi kanan kartu menampung label metrik, angka detail, penjelasan instrumen wajib, dan rekapitulasi.
- **Collection Merge vs Concat with Transformed stdClass Objects**: Pada Laravel, pemanggilan `->merge()` pada instans `Illuminate\Database\Eloquent\Collection` mengecek primary key model via `getKey()`. Jika koleksi telah dipetakan (`->map()`) menjadi objek generic (`stdClass`), pemanggilan `merge()` akan memicu fatal error 500: `Call to undefined method stdClass::getKey()`. **Solusi**: Gunakan `collect()->concat($a)->concat($b)->values()` untuk menggabungkan beberapa koleksi objek generic secara aman.
- **Domain Mapping, cPanel AAAA IPv6 Conflict & Auto-HTTPS via Caddy**:
  1. *Shared Hosting vs VPS*: Bila aplikasi membutuhkan binary sistem seperti `google-chrome-stable` (untuk cetak raport headless PDF) dan isolasi storage Laravel, aplikasi wajib tetap berjalan di VPS, bukan di-deploy via cPanel Git shared hosting.
  2. *DNS Configuration*: Arahkan A record domain (`@` dan `www`) di Zone Editor registrar/cPanel ke IP publik VPS (`43.173.9.113`).
  3. *Bahaya AAAA (IPv6) Bawaan cPanel*: cPanel secara default menyertakan record `AAAA` ke IP shared hosting. Browser modern (Brave, Chrome) memprioritaskan IPv6 (Happy Eyeballs algorithm). Jika `AAAA` masih ada, browser akan mencoba membuka IP shared hosting dan gagal dengan `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`. **Wajib menghapus record AAAA** di Zone Editor jika VPS hanya memiliki IPv4.
  4. *Caddy Reverse Proxy*: Di `/etc/caddy/Caddyfile`, tambahkan blok domain dengan `reverse_proxy 127.0.0.1:<port>`. Caddy akan otomatis menyelesaikan tantangan ACME (TLS-ALPN-01/HTTP-01) dan menerbitkan sertifikat Let's Encrypt resmi. Update `.env` dengan `APP_URL=https://<domain>` dan jalankan `php artisan config:clear`.

### SPA Routing & Direct Page Reloads
- **Pitfall**: `404 Not Found` when reloading directly on SPA routes (`/login`, `/vehicles`, `/bookings`) → Laravel has no route definition for `/login`, returns 404. Vue Router never loads.
- **Fix**: Add `Route::fallback(function() { return view('welcome'); })` in `routes/web.php` after all other routes. This serves the SPA Blade host for any unmatched web route. Vue Router renders the correct component client-side.
- **Test**: `curl -s -w "%{http_code}" https://your-domain/login` should return `200`, not `404`.

### Sanctum Token Management
- **Pitfall**: Token stored in `sessionStorage` → Lost on page refresh, breaks PWA offline experience
- **Fix**: Use `localStorage` for token persistence; clear on logout
- **Test**: Logout, refresh page, verify redirected to login (token must be gone)

### Permissions & File Serving
- **Error**: `manifest.json` returns HTML (Caddy 403) → Check `public/` file permissions
- **Fix**: `chmod 644 public/manifest.json public/sw.js public/icons/*`

### Conflict Detection Complexity
- **Pitfall**: Only checking date overlap for time-based items → Misses edge cases (same-start, end-at-start)
- **Pattern**: Use minute-based overlap logic; test with: (start1 < end2) AND (start2 < end1)
- **Real**: Tested with 08:00-12:00 vs 10:00-14:00 (overlap at 10:00-12:00) ✓

### Multi-Tier PWA Asset & Photo Caching Optimization
- **Pitfall**: App feels heavy/sluggish ("tampilan masih berat") especially on mobile after users upload high-res photos (5MB–10MB camera shots) for avatars or posts.
- **Root Cause**:
  1. Profile avatars and post images are stored in their raw uploaded resolution (e.g. 1MB–5MB per image).
  2. Image streaming controllers default to `'Cache-Control' => 'private, no-store'`, forcing the browser to re-download megabytes of images on every single page navigation.
  3. Reverse proxying all requests to single-threaded `php artisan serve` puts static assets (`.css`, `.js`, logos) in the same queue as heavy dynamic requests and PDF rendering.
- **Fix 1: Backend Image Compression on Upload**:
  - Implement a dedicated compressor (e.g. `ProfileImageCompressor`) using PHP GD.
  - Scale avatars to a sensible bounding box (e.g. max `400x400` px for avatars, `1280x1280` px for article banners) and compress at quality 80%.
  - Guard against degrading already-tiny test fixtures: if image dimensions are within limits and file size is already light (<80KB), preserve original bytes.
  - Yields an immediate 85%–98% reduction in asset weight (e.g. 1MB down to ~20KB).
- **Fix 2: Direct Static File Serving & Long Caching in Caddy**:
  - In `Caddyfile`, configure `root * /path/to/public` and use `file_server` with `@static` matcher:
    ```caddy
    @static {
        file
        path *.ico *.css *.js *.gif *.webp *.avif *.jpg *.jpeg *.png *.svg *.woff *.woff2 *.webmanifest
    }
    header @static {
        Cache-Control "public, max-age=31536000, immutable"
        X-Content-Type-Options "nosniff"
    }
    file_server
    @notStatic {
        not file
    }
    reverse_proxy @notStatic 127.0.0.1:<port>
    ```
  - Static assets bypass PHP entirely, serving from memory/disk in ~50ms.
- **Fix 3: HTTP Cache Headers & ETags on Dynamic Image Endpoints**:
  - In photo controllers, compute an ETag (e.g. `md5($path . filemtime($fullPath))`) and send `'Cache-Control' => 'private, max-age=86400, must-revalidate'`.
  - Return `304 Not Modified` when `If-None-Match` matches, eliminating data transfer on repeat visits.
- **Fix 4: PHP OPcache & Laravel View Pre-compilation**:
  - Enable OPcache in CLI (`opcache.enable_cli=1` in `/etc/php/8.3/cli/php.ini`) when running artisan serve.
  - Run `php artisan optimize` to cache config, routes, and pre-compile Blade templates.

### Asset Cache Busting & PWA Maskable Branding Replacement
- **Pitfall**: Replacing brand logos or favicons does not update on client browsers ("di domain belum berubah tampilan logonya") due to immutable HTTP headers or Service Worker asset caching.
- **Root Cause**: Browsers cache static images aggressively if served with `max-age=31536000, immutable`, and Service Worker precaches static URLs. Even hard refreshing may not immediately replace all sub-resources.
- **Fix 1 (Query String Cache Busting)**: In Blade views, append version tags to static asset URLs: `<img src="/images/logo-fic.png?v=2">`, `<link rel="icon" href="/favicon.ico?v=2">`. The browser treats this as a new URL and fetches the updated asset immediately.
- **Fix 2 (Service Worker Activation)**: Bump `CACHE_VERSION` in `public/sw.js` (e.g. from `20261023b` to `20261023c`). The Service Worker's `activate` event then purges all stale cache buckets automatically.
- **PWA Multi-Format Emblem Generation**:
  1. *Web & In-App Logo*: 500x500 RGBA PNG with antialiased transparent circular mask.
  2. *Android PWA Icons*: 192x192 and 512x512 with ~12-16px padding safe zone. In `manifest.webmanifest`, register both `"purpose": "any"` and `"purpose": "maskable"` so adaptive launchers (squircle, circle, rounded rect) do not cut off perimeter text or borders.
  3. *Apple Touch Icon (`apple-touch-icon.png`)*: iOS does not support transparent alpha in home screen icons and renders transparent pixels as solid black. Always composite the emblem over a clean white background (`#FFFFFF`) before saving.

### Fatal Production Database Wipe: Config Cache Collision with RefreshDatabase & Mitigation
- **Critical Hazard**: Running `php artisan test` after `php artisan optimize` or `php artisan config:cache` on an application using SQLite completely wipes the production SQLite database (`database/database.sqlite`)!
- **Root Cause Analysis**:
  1. `php artisan optimize` compiles and writes `bootstrap/cache/config.php`.
  2. When this cached file is present, PHPUnit / Laravel test bootstrap ignores `<env name="DB_DATABASE" value=":memory:"/>` from `phpunit.xml`. It instead boots using the compiled production configuration pointing to `database/database.sqlite`.
  3. Feature test classes that use the `RefreshDatabase` trait (`use RefreshDatabase;`) execute `migrate:fresh` at the start of each test suite.
  4. Because the active connection is the physical SQLite database file, `migrate:fresh` drops all physical tables and wipes all runtime production data (e.g. user-registered accounts, submitted forms, uploaded logs).
  5. Subsequent `php artisan db:seed` only restores static fixture accounts, permanently deleting any unseeded runtime data!
  6. Furthermore, session state is cleared, producing widespread `419 Page Expired` (CSRF) errors across test suites.
- **Mandatory Prevention & Code-Level Guard**:
  1. *Hard Guard in `tests/TestCase.php`*: Add an explicit safety check in `setUp()` to abort execution immediately if running against a physical database:
     ```php
     abstract class TestCase extends BaseTestCase
     {
         protected function setUp(): void
         {
             parent::setUp();
             $db = config('database.connections.sqlite.database');
             if (config('database.default') === 'sqlite' && $db !== ':memory:' && ! str_ends_with((string) $db, ':memory:')) {
                 throw new \RuntimeException("BAHAYA: Pengujian dilarang berjalan pada database fisik ({$db})! Hapus cache config terlebih dahulu.");
             }
         }
     }
     ```
  2. *Production Destructive Command Block (`AppServiceProvider.php`)*: In `boot()`, call `DB::prohibitDestructiveCommands($this->app->isProduction());` so commands like `migrate:fresh`, `migrate:reset`, and `db:wipe` are physically blocked by Laravel in production.
  3. *Automated Hourly SQLite Snapshot & Backup Cron*: Setup automated snapshot script (`/home/ubuntu/backups/backup-pwa-bruder.sh`) triggered hourly via `crontab` (`0 * * * * ...`), archiving timestamped copies to an external backup directory with 48-hour hourly and 30-day daily retention.
  4. *Runtime User Seeder Mirroring*: Every official user registered manually must be back-ported into `database/seeders/UserSeeder.php` using `firstOrNew(['username' => ...])` so subsequent database seeding never drops existing production users.
  5. *Command Hygiene*: NEVER run `php artisan test` while config is cached. Always run `php artisan optimize:clear` or `php artisan config:clear` before running test suites.
  6. *Database Backup Before Testing*: On single-database environments (VPS with SQLite), create a snapshot copy (`cp database/database.sqlite database/database.sqlite.bak`) before running maintenance commands.

### Domain Mapping & cPanel IPv6 AAAA Conflict (ERR_SSL_VERSION_OR_CIPHER_MISMATCH)
- **Pitfall**: After changing the A record of a custom domain to point to the VPS IP, browsers (especially Brave/Chrome) still display `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` or fail to connect.
- **Root Cause**: When a domain is registered or previously parked on cPanel shared hosting (e.g. Domainesia, RapidPlex), cPanel automatically provisions an **AAAA (IPv6)** record pointing to the shared hosting server (`2001:...`). Modern browsers use the Happy Eyeballs algorithm and prioritize IPv6 connections. Even if the A (IPv4) record points to the VPS, the browser connects to the cPanel shared hosting IPv6 which lacks a valid SSL certificate for the domain.
- **Fix**:
  1. Open cPanel **Zone Editor** -> **Manage** -> filter by **AAAA**.
  2. Delete any `AAAA` records for `@` (`domain.com`) and `www`.
  3. Ensure only the `A` record points to the VPS IPv4 (`43.173.9.113`).
  4. In Caddy, configure `domain.com, www.domain.com { ... }`. Caddy will automatically pass ACME challenge and issue Let's Encrypt / ZeroSSL certs immediately.
  5. If user's local ISP or browser holds stale DNS cache (due to previous 14400s TTL), advise switching Brave/Chrome to "Use Secure DNS: Cloudflare (1.1.1.1)" or running `ipconfig /flushdns`.

### Bulk Delete Multi-Select with Layered Security (Hapus Massal Berlapis)
- **Pattern**: When the user requests "pilih semua / pilih sebagian / hapus massal" on a list page (e.g. journals, reports), implement the following full pattern:
  1. *Route*: Add a named `DELETE /resource/bulk-delete` route **before** the `{model}` wildcard route so Laravel's router doesn't try to bind the literal string `"bulk-delete"` to a model ID.
  2. *Controller method `destroyBulk(Request $request)`*: Validate that `$ids` is a non-empty array. Always append `.where('user_id', auth()->id())` (or equivalent ownership scope) to the `whereIn` query — this ensures IDs injected from a tampered form cannot delete another user's records.
  3. *Toolbar UI*: A persistent toolbar with a "Pilih Semua" checkbox + disabled-by-default red delete button. Enable the button and update its label (`Hapus N Terpilih`) only when at least one item is selected. Use `indeterminate` state on the master checkbox when some (not all) items are checked.
  4. *Per-card checkbox*: Position the checkbox at `position: absolute; top: 14px; right: 14px` so it overlays without displacing card content.
  5. *Modal konfirmasi*: A single shared modal handles both single-item delete and bulk delete. Show item name for single, show count for bulk. Include a red warning "Data yang dihapus tidak dapat dipulihkan." Dismiss on outside click. Block body scroll while open.
  6. *Hidden form injection*: For bulk delete, dynamically inject `<input type="hidden" name="ids[]" value="...">` into a dedicated hidden form via JavaScript before calling `.submit()`. Never send IDs in URL query strings.
- **Pitfall**: Placing the `bulk-delete` route after the `{journal}` route wildcard causes Laravel to try resolving `"bulk-delete"` as a model ID, resulting in 404 or 500. **Always register the specific static route first.**
- **Security note**: Even with JavaScript guards, always enforce ownership in `destroyBulk` at the database level — a user could craft a POST with arbitrary IDs.

### Form Creation Field Cleanliness (Placeholders vs Pre-filled Values)
- **Pitfall**: Hardcoding sample names or example data into the `value` attribute on creation views (e.g. `value="{{ old('mentor_name', 'Br. Yohanes Subagio, FIC') }}"`). When a user opens the form to log a report or schedule an agenda, the field is pre-populated with dummy text that they must manually erase ("nama pembimbing, pimpinan lokal dll. jangan diisi otomatis").
- **Fix**: Use clean placeholders for examples (`placeholder="Contoh: Br. Yohanes Subagio, FIC"`), and leave `value="{{ old('mentor_name') }}"` (or on unified create/edit templates: `value="{{ old('mentor_name', $editing ? $schedule->mentor_name : '') }}"`). Never place example strings in the `value` attribute on creation forms.

### Dynamic Profile Avatar Cache Desynchronization
- **Pitfall**: A user uploads a new avatar/profile photo on their account page; the upload succeeds and updates the database, but the top header and profile card continue displaying the old photo while other views (like user directory lists) show the new one.
- **Root Cause**:
  1. The profile image URL (e.g. `/profil/foto`) has no unique identifier or hash query parameter, so the browser serves the stale file from disk/memory cache.
  2. The endpoint sends a long `max-age` (e.g. `max-age=86400`) instead of requiring ETag revalidation.
  3. Service Worker caches image requests via stale-while-revalidate if dynamic photo endpoints aren't explicitly exempted in `isPrivateAsset()`.
- **Fix**:
  1. *Versioned Cache Buster*: In Blade templates, always append a version/hash query string to dynamic avatar routes: `<img src="{{ route('profil.foto', ['v' => $user->profile_photo ? substr(md5($user->profile_photo), 0, 8) : '0']) }}">`. As soon as a new photo is saved, the filename and MD5 change, forcing the browser to fetch the new image immediately.
  2. *Revalidation HTTP Header*: In photo streaming controllers, send `'Cache-Control' => 'private, no-cache, must-revalidate'` with an `ETag` (hash of path + filemtime). The browser will always check if the photo has changed, returning `304 Not Modified` when unchanged and `200` with fresh bytes when updated.
  3. *Service Worker Exemption*: In `sw.js`, ensure `isPrivateAsset(pathname)` matches dynamic photo routes (`pathname === '/profil/foto' || pathname.endsWith('/foto')`) so the Service Worker lets requests hit the network directly.

### Service Worker HTTP Cache Locking & Caddy Static Directives Conflict
- **Critical Hazard**: If Caddyfile serves `*.js` with aggressive static caching (e.g. `Cache-Control "public, max-age=31536000, immutable"` under `@static`), `sw.js` gets permanently cached by the client browser for 1 year!
- **Symptom**: User updates application on server, but browser still displays old UI even after multiple hard refreshes, while opening on another browser shows the new UI ("tampilannya kok nggak berubah ya padahal aku dah hapus cache tapi kalo di browser lain bisa berubah").
- **Root Cause**:
  1. The browser obeys the HTTP `Cache-Control: max-age=31536000` header on `/sw.js` and never fetches a new byte check from the server.
  2. The browser never discovers that `CACHE_VERSION` was incremented, so the old Service Worker remains active indefinitely.
- **Mandatory Caddyfile Rule**: In Caddyfile, explicitly exclude `/sw.js` from the immutable static file matcher, and give it zero cache:
  ```caddy
  @sw {
      path /sw.js
  }
  header @sw {
      Cache-Control "no-cache, no-store, must-revalidate"
      Expires "0"
  }

  @static {
      file
      path *.ico *.css *.js *.gif *.webp *.avif *.jpg *.jpeg *.png *.svg *.woff *.woff2 *.webmanifest
      not path /sw.js
  }
  header @static {
      Cache-Control "public, max-age=31536000, immutable"
      X-Content-Type-Options "nosniff"
  }
  ```
- **CSS Version Tagging in Blade Layouts**: Never load bare `<link rel="stylesheet" href="/css/app.css">`. Always append an explicit cache-busting version query parameter: `<link rel="stylesheet" href="/css/fic-pwa.css?v=20261024b">` to guarantee instant client updates upon CSS modification.

### Service Worker HTML Caching on Dynamic Management Dashboards (Bypass SW for Admin Routes)
- **Pitfall**: Admin or Super Admin reports that a newly added feature, button, or column is missing / not visible ("belum ada fiturnya", "fitur masih belum bisa digunakan") even after deployment, testing, and artisan view/route clears.
- **Root Cause**:
  1. The PWA `public/sw.js` fetch handler intercepts document navigations (`request.mode === 'navigate' || acceptsHtml(request)`) and serves HTML pages from a client-side Service Worker Cache (`PAGE_CACHE`) using a network-first or stale-while-revalidate strategy.
  2. If the user had opened the admin page recently on mobile, the browser serves the cached HTML snapshot from SW storage before or without replacing it, masking newly deployed server-side Blade changes.
  3. Hard refresh on mobile PWA is non-trivial for non-technical users.
- **Fix 1: Exempt Administrative Routes from Service Worker Handling**:
  - In `public/sw.js`, expand `isPrivateAsset(pathname)` (or a dedicated `isAdminRoute(pathname)`) to immediately bail out of the Service Worker entirely:
    ```javascript
    function isPrivateAsset(pathname) {
        return pathname.startsWith('/super-admin')
            || pathname.startsWith('/admin')
            || pathname === '/profil/foto'
            || pathname.endsWith('/foto')
            || pathname.includes('/bukti');
    }
    ```
  - When `isPrivateAsset(url.pathname)` returns true, the SW `fetch` listener simply returns early without calling `event.respondWith(...)`. The browser handles the request via normal network navigation without any Service Worker caching layer.
- **Fix 2: Bump Service Worker Version on Every Feature Deploy**:
  - Every time an administrative view or PWA feature is updated, increment `CACHE_VERSION` in `public/sw.js` (e.g. `20261023d` → `20261023e`).
  - In `activate` listener, purge stale cache stores: `caches.delete(PAGE_CACHE)`.
- **Fix 3: Git Push Synchronization Before User Review**:
  - Never announce a feature as complete while code changes are only staged or unpushed locally. Always commit, run full test suite, verify clean tree, and execute `git push origin <branch>` so remote servers, tunnels, and user browsers receive the latest code immediately.

### Heterogeneous Multi-Model Bulk Deletion Pattern (Monitoring Laporan Multi-Jenis)
- **Pattern**: When a dashboard aggregates distinct Eloquent models (e.g. `SpiritualGuidanceReport`, `WawanhatiReport`, `SelfDevelopmentJournal`) into a unified timeline view and requires unified bulk deletion:
  1. *Composite Identifier*: Render checkboxes with a composite key: `value="{{ $report->category }}:{{ $report->id }}"` (e.g. `"bimbingan:12"`, `"wawanhati:5"`, `"jurnal:8"`).
  2. *Single Controller Endpoint*: The bulk delete endpoint splits each item by `:` into category and integer ID, groups them by target model, and executes scoped queries with role/ownership enforcement:
     ```php
     match ($cat) {
         'bimbingan' => $bimbinganIds[] = $id,
         'wawanhati' => $wawanhatiIds[] = $id,
         'jurnal'    => $jurnalIds[] = $id,
     };
     ```
  3. *Scoped Authorization*: Each model deletion query MUST enforce ownership or role filtering (e.g. `->whereHas('user', fn ($q) => $q->where('role', 'user'))`) to prevent cross-privilege destruction.
  4. *SoftDeletes Assertion in Tests*: If models implement `SoftDeletes`, feature tests must use `$this->assertSoftDeleted('table_name', ['id' => $id])` instead of `$this->assertDatabaseMissing(...)`.
- **Pitfall: Filter Relasi yang Menyaring Akun Trashed/Demo**:
  - Saat menghapus data laporan (misal bimbingan/wawanhati/jurnal) menggunakan `whereHas('user', fn ($q) => $q->where('role', 'user'))`, jika user pemilik data berstatus *soft-deleted* (`deleted_at IS NOT NULL`, contohnya akun demo yang dinonaktifkan atau dihapus saat testing), kueri `whereHas('user')` default Eloquent akan **mengecualikan** user trashed tersebut.
  - Akibatnya query delete menghasilkan `0 row deleted` dan memunculkan feedback membingungkan bagi admin: *"0 laporan berhasil dihapus"*.
  - **Solusi**: Gunakan `withTrashed()` pada relasi user:
    ```php
    ->whereHas('user', fn ($q) => $q->withTrashed()->where('role', 'user'))
    ```
    atau jika otorisasi sudah dijamin di level middleware rute admin/super admin, hapus langsung record berdasarkan ID terverifikasi (`$model::whereIn('id', $ids)->delete()`).

### Git Remote Topic Branch Merge Workflow for Cursor/External Collaboration
- **Pattern**: Ketika user menginstruksikan *"ambil perubahan di github"* atau *"apakah semua perubahan sudah diambil?"*:
  1. Jalankan `git fetch --all --prune` untuk mengambil semua branch remote terbaru.
  2. Periksa seluruh branch remote (`git branch -r`). Sering kali kontributor eksternal atau Cursor agent bekerja pada topic branch spesifik seperti `origin/cursor/<fitur>-<hash>`, bukan langsung di `origin/main`.
  3. Bandingkan commit setiap branch terhadap branch aktif:
     ```bash
     for b in $(git branch -r | grep -v 'HEAD' | sed 's/origin\///'); do
       echo "=== $b ==="
       git log main..origin/$b --oneline
     done
     ```
  4. Jika ada commit tertinggal pada topic branch aktif, lakukan fast-forward merge ke `main`:
     ```bash
     git merge origin/cursor/<fitur>-<hash>
     ```
  5. Jalankan suite pengujian lengkap (`php artisan test`) untuk memastikan integrasi tidak merusak fitur eksisting.
  6. Push hasil merge ke `origin/main` agar branch utama di remote selalu menjadi single source of truth.
  7. Bersihkan cache aplikasi (`php artisan optimize:clear`) dan restart service/worker yang relevan.

### Broadcast Agenda Pattern (Penyebaran Agenda Massal dari Admin/Super Admin ke Seluruh Akun User)
- **Requirement**: Admin atau Super Admin perlu menambahkan kegiatan bersama (misal: Retret Tahunan, Pertemuan Akbar, Hari Komunitas) yang secara otomatis harus masuk dan terlihat pada jadwal dan kalender seluruh akun pengguna/anggota (`role = 'user'`).
- **Pattern**:
  1. *Formulir Terpusat*: Sediakan form tambah agenda khusus admin (`/super-admin/monitoring/agenda/tambah`) mencakup judul, tanggal, waktu, lokasi, dan deskripsi, lengkap dengan notice box transparan yang menginformasikan bahwa agenda akan otomatis masuk ke seluruh akun user.
  2. *Fan-Out ke Database*: Saat formulir disubmit, ambil seluruh akun anggota aktif (`User::where('role', 'user')->where('is_active', true)->get()`). Buat satu entri `PersonalAgenda` untuk masing-masing user:
     ```php
     foreach ($users as $user) {
         PersonalAgenda::create([
             'user_id' => $user->id,
             'title' => $validated['title'],
             'start_at' => $startAt,
             'location' => $validated['location'],
             'description' => $validated['description'] ?? null,
             'status' => 'scheduled',
         ]);
     }
     ```
  3. *Umpan Balik Eksplisit (Flash Message)*: Berikan pesan flash yang secara gamblang menyebutkan jumlah akun yang menerima agenda (misal: `"Agenda '...' berhasil ditambahkan ke 22 akun Bruder Muda."`) agar admin yakin 100% bahwa distribusi ke seluruh user telah tereksekusi tanpa ragu.
  4. *Konsistensi Kalender User & Admin*:
     - Di sisi user (`PersonalScheduleQuery`), agenda dibaca dari entri `PersonalAgenda` miliknya sehingga langsung muncul di menu Kalender (`/kalender`), Agenda (`/agenda`), dan Beranda (`/dashboard` jadwal mendatang).
     - Di sisi admin (`MonitoringQuery::agendas()`), kueri mengagregasi seluruh `PersonalAgenda` dan menampilkan indikator titik (*calendar dots*) pada tanggal pelaksanaan di kalender rekapitulasi monitoring.
  5. *Aksi Hapus Terisolasi*: Sediakan tombol hapus per baris agenda di `_agenda-list.blade.php` (`/monitoring/agenda/{category}/{id}`) agar admin dapat membatalkan agenda sewaktu-waktu.

### Context-Specific Action Toolbar Swapping (Penggantian Tombol Aksi Kontekstual)
- **Pattern**: Pada halaman rekapitulasi multi-tab yang menggunakan toolbar bersama (`_toolbar.blade.php`), kebutuhan tombol aksi seringkali berbeda antar tab (misal tab "Laporan" membutuhkan tombol ekspor Excel & PDF, sedangkan tab "Agenda" membutuhkan tombol aksi utama `+ Tambah Agenda` dan tidak memerlukan ekspor).
- **Implementasi**: Bedakan tampilan tombol aksi berdasarkan parameter konteks (`$exportKind`):
  ```blade
  @if($exportKind === 'agenda')
      <div style="margin-top:12px;">
          <a href="{{ route('superadmin.monitoring.agenda.create') }}" class="btn-primary-agenda">
              + Tambah Agenda
          </a>
      </div>
  @else
      <div style="display:flex; gap:8px; margin-top:12px;">
          <a href="{{ ...export excel... }}">Excel</a>
          <a href="{{ ...export pdf... }}">PDF</a>
      </div>
  @endif
  ```
  Hal ini menghemat ruang vertikal layar mobile dan menjaga antarmuka tetap bersih tanpa tombol berlebih yang jarang digunakan.

### Bottom Navigation Streamlining & Direct Profile Integration
- **Pattern**: Hindari duplikasi item pada bilah navigasi bawah (*Bottom Nav*). Jika sub-halaman sudah terintegrasi rapi di dalam tab navigasi atas (seperti tab *Raport*, *Laporan*, *Agenda*, dan *Jurnal* di dalam modul pemantauan), jangan membuat tombol terpisah untuk *Raport* dan *Monitoring* di navigasi bawah karena keduanya membingungkan pengguna.
- **Solusi**: Satukan di bawah satu ikon utama (*Raport*), lalu gunakan slot navigasi yang kosong untuk menu penting yang sering diakses langsung, seperti **"Profil"** (`/super-admin/profil`). Hal ini memungkinkan pengguna mengakses pengaturan akun, avatar, dan kata sandi secara instan tanpa harus membuka drawer menu samping.

## Session Patterns (Quick Reference)
| Sesi | Teknik | Lokasi |
|------|--------|--------|
| 2026-10 | Cegah simbol ganda pada tombol aksi: jangan gabungkan SVG icon plus dengan karakter teks `+` (`+ + Tambah`) | Pitfalls → Mobile PWA UI & Typography Hygiene |
| 2026-10 | Broadcast agenda massal dari Admin/Super Admin ke seluruh akun bruder via batch `PersonalAgenda` | Pitfalls → Broadcast Agenda Pattern |
| 2026-10 | Toolbar kontekstual: ganti tombol ekspor Excel/PDF menjadi `+ Tambah Agenda` pada tab Agenda | Pitfalls → Context-Specific Action Toolbar Swapping |
| 2026-10 | Reduksi duplikasi Bottom Nav (hapus Monitoring redundant, ganti langsung dengan Profil) | Pitfalls → Bottom Navigation Streamlining |
| 2026-10 | Caddyfile: exclude `/sw.js` dari immutable cache + set `no-cache, no-store` agar SW selalu update | Pitfalls → SW HTTP Cache Locking & Caddy Static Directives Conflict |
| 2026-10 | Bypass SW fetch handler untuk seluruh rute admin (`/super-admin`, `/admin`) agar view Blade selalu realtime | Pitfalls → SW HTML Caching on Dynamic Management Dashboards |
| 2026-10 | Heterogeneous bulk delete via composite key (`category:id`) dengan scoped query per model | Pitfalls → Heterogeneous Multi-Model Bulk Deletion Pattern |
| 2026-10 | Penanganan akun trashed/soft-deleted pada `whereHas('user')` saat hapus data relasional | Pitfalls → Heterogeneous Multi-Model Bulk Deletion Pattern |
| 2026-10 | Alur verifikasi & merge komprehensif seluruh topic branch remote (`git fetch --all --prune`) | Pitfalls → Git Remote Topic Branch Merge Workflow |
| 2026-10 | Bulk delete multi-select + modal konfirmasi + `destroyBulk` scoped ownership | Pitfalls → Bulk Delete |
| 2026-10 | Cache-busting `?v=md5hash` pada avatar profil + `no-cache, must-revalidate` header | Pitfalls → Dynamic Profile Avatar Cache |
| 2026-10 | Form `value` kosong pada create view — gunakan `placeholder` bukan hardcode nama contoh | Pitfalls → Form Creation Field Cleanliness |

## Support References
- `references/production-sqlite-safeguards.md` — SQLite production safeguards: RefreshDatabase wipe prevention, kill-switch, automated hourly crontab backup script, and disaster recovery.
- `references/bruder-fic-phase-delivery.md` — Phase-gated delivery, Cloudflare proxy session fixes, mobile UX header back buttons, profile fields, character counters
- `references/service-worker-security.md` — SW caching rules, Network-first vs Cache-first patterns, security verification, versioned SW registration
- `references/tunnel-proxy-troubleshooting.md` — Cloudflare Tunnel / Reverse Proxy HTTPS config, Caddyfile patterns, Laravel trusted proxies, SPA route fallback
- `references/conflict-detection-pattern.md` — Temporal & spatial conflict logic, test cases, integration pattern
- `templates/manifest.json.template` — PWA manifest boilerplate (copy to public/manifest.json)
- `scripts/verify-pwa-readiness.sh` — Automated check for manifest, icons, SW presence, permissions, security rules

## Quick Start Checklist (New Project)
1. Copy `templates/manifest.json.template` → `public/manifest.json` and customize
2. Copy `references/service-worker-security.md` example → `public/sw.js`
3. Run `scripts/verify-pwa-readiness.sh` after build
4. Follow Critical Steps 1-8 in SKILL.md

## Verification Checklist (Pre-Deployment)
- [ ] All API endpoints tested with tokens (admin & user roles)
- [ ] Conflict service tested on boundaries (same-day, overlapping ranges)
- [ ] Vue build passes without errors (`npm run build` exit code 0)
- [ ] PWA manifest valid JSON, icons present, theme color set
- [ ] Service Worker console logs show "Registered successfully"
- [ ] HTTPS enabled and Let's Encrypt cert valid
- [ ] Install prompt appears on mobile browser
- [ ] Login/register pages excluded from SW cache
- [ ] Role-based dashboards render correct data for each role
- [ ] Git commits clean, no lingering debug code or secrets

## Related Skills
- `coding-agent` (generic development procedures)
- Delegatable subtasks: database migrations, API testing, PWA icon generation, CI/CD setup
