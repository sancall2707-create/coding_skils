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
- **Bottom Navigation Bar for Management Mobile Views**: Bilah menu bawah (*Bottom Nav*) untuk Super Admin/Admin harus mengakomodasi menu-menu vital (Beranda, Direktori, Raport, Monitoring, Sapaan) dengan desain *glassmorphic*. Jika ada tombol aksi mengambang (*FAB*), naikkan posisi tombol (`bottom: 80px`) agar tidak menumpuk dengan bilah navigasi bawah, dan sembunyikan navigasi bawah pada `@media print`.

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

## Support References
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
