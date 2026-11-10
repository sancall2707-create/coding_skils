---
name: laravel-production-safe-change
description: "Alur aman mengubah aplikasi Laravel SQLite yang sudah live tanpa kehilangan data - backup, migrasi aditif dan backfill, uji di salinan DB, tes, cache-bust PWA, commit ke branch, plus jebakan tes dan regex yang pernah terjadi."
---

# Perubahan aman pada Laravel produksi (SQLite, PWA)

Dipakai untuk proyek seperti PWA Bruder FIC (`/home/ubuntu/PWA_Bruder-Muda`, live di formatio-fic.com via `artisan serve` port 8022). User: nol toleransi data loss, jangan ubah fitur/alur lain, bahasa Indonesia.

## Urutan kerja
1. Baca kode nyata dulu (controller, view, query service). Jangan menebak penyebab "belum aktif"; uji di Chrome headless dengan salinan DB bila perilaku UI diragukan.
2. Backup: `/home/ubuntu/backups/backup-pwa-bruder.sh` + `cp database/database.sqlite /home/ubuntu/backups/db_sebelum_<fitur>_<ts>.sqlite`.
3. Perubahan skema HANYA aditif (kolom baru, default aman). Tidak ada `migrate:fresh`, drop, atau ubah isi lama selain backfill yang bisa dibuktikan.
4. Backfill data lama dengan pola yang bisa diverifikasi (contoh: tandai agenda siaran = kelompok judul+waktu+lokasi dengan jumlah salinan >= jumlah akun aktif).
5. Uji migrasi di SALINAN: `cp database.sqlite /tmp/x.sqlite && DB_DATABASE=/tmp/x.sqlite php artisan migrate --force`, lalu bandingkan jumlah baris dan isi kolom lama (harus identik) dan hasil backfill.
6. Tulis tes fitur (RefreshDatabase). Jalankan `php artisan test` penuh.
7. Backup lagi, `php artisan migrate --force` di DB asli, cek `pragma integrity_check` + jumlah baris, `php artisan optimize:clear`.
8. Aset statis/SW berubah: naikkan `CACHE_VERSION` di `public/sw.js`, `?v=` pada aset, dan PRECACHE.
9. Commit deskriptif + push ke branch kerja (bukan `main` kecuali diminta). Cek domain publik (HTTP 200).
10. Laporan ke user: apa yang berubah, bukti uji, status DB, commit. Tanpa emoji.

Kerangka verifikasi Chrome headless + salinan DB siap pakai (login per role, cek/foto/ukur): `scripts/chrome_verify_template.py`. Selalu: catat md5 DB sebelum, pembuktian tes sensitif (cabut perbaikan sementara, tes harus gagal), bersihkan proses uji, lalu laporkan jujur bila md5 produksi berbeda karena aktivitas user.

## Jebakan yang sudah terjadi
- `re.sub(pat, "string berisi \\App\\Models", s)` menggagalkan skrip (bad escape). Pakai `re.subn(pat, lambda m: baru, s)`; skrip gagal sebelum menulis, jadi cek `git status` sebelum mengulang.
- Helper tanggal yang mengembalikan string (mis. `combineDateAndTime(): string`) tidak punya `->format()`. Bungkus `Carbon::parse(...)`.
- Tes yang menghitung `substr_count($html, 'Judul')` salah hitung bila flash message sukses dari POST di tes yang sama memuat judul. Hitung pada penanda kartu (`margin-top: 2px;">Judul</div>`) atau lakukan GET di request terpisah.
- Edit lewat patch/sed pada blok panjang: periksa `git diff --stat` dan pastikan hanya method yang dituju berubah (mis. `admin()` dan `superAdmin()` berubah, `user()` tidak).
- Tool terputus ("Orphan recovery"): periksa `git status` dan proses sisa (`pgrep -af "artisan serve.*1810"`), jangan asumsikan status.
- Pencarian dropdown yang hanya menyaring option terasa "tidak aktif": tampilkan hasil sebagai daftar terbuka (`select.size`) dan Enter memilih hasil pertama lalu `form.submit()`. Uji dengan nama nyata dari DB, bukan nama tebakan.
- Ganti logo: backup file lama, hasilkan PNG persegi (canvas putih + LANCZOS 512), tambah `?v=N` di view dan PRECACHE, naikkan `CACHE_VERSION`.

- Terminal menolak perintah foreground yang memuat `&` (mis. teks Blade "Hari &amp;" di heredoc python): tulis skrip ke `/tmp/x.py` lewat write_file lalu jalankan.
- Tes berulang per role: bersihkan data antar iterasi (`User::query()->delete()`, `forceDelete()`), kalau tidak jumlah akun penerima akumulatif dan assertion meleset.
- `assertSee('X')` gagal bila X hanya ada di atribut `value="X"`: pakai `assertSee('value="X"', false)`. Bila gagal, cetak potongan HTML lewat tes sementara (hapus setelahnya), jangan menebak.
- Jumlah baris DB asli naik tak terduga: cek `created_at` dulu; bisa data baru dari user, bukan efek uji.

- Prompt tuning/infrastruktur generik dari user (Nginx, Redis, Supervisor, k6): jangan dijalankan apa adanya. Audit kenyataan server dulu dan uji beban di salinan; lihat skill `laravel-vps-capacity-audit`.
- Ganti teks label di model/query (mis. nama penulis agenda provinsi jadi TPPBM): ubah satu sumber, perbarui assertion tes yang memakai teks lama, jalankan tes penuh.

- Sebelum `git push`/git deploy ke tempat lain, audit rahasia terlacak: `git ls-files | grep -i -E "keystore|\.env|\.sqlite|\.pem|secret"` dan cek repo publik via API GitHub. Temuan nyata: keystore TWA + file sandi terlacak di repo publik. Cabut dengan `git rm --cached` + `.gitignore` (berkas lokal tetap, backup di luar repo), jalankan tes, push, lalu laporkan bahwa riwayat lama masih memuatnya dan rotasi kunci = keputusan user.
- Memasang/mengganti proses produksi (systemd untuk `artisan serve`): nyalakan unit dalam satu rantai; jangan mematikan proses lama lewat tool proses yang menjadi induk perintah berjalan (perintah ikut putus, situs 502 ~1 menit). Detail: skill `laravel-vps-capacity-audit`.
- Situs produksi 502 di tengah pekerjaan lain: periksa dulu `ss -ltn | grep 8022` dan log Caddy sebelum menyalahkan perubahan sendiri; backup DB sebelum menyalakan ulang.

## Pola perubahan kecil tanpa menyentuh DB (sesi 6 Nov 2026)
- **Halaman pertama saat buka aplikasi**: `start_url` PWA/TWA = `/`. Ubah `match ($user->role)` pada `Route::get('/')` di `routes/web.php` (user -> `/sapaan-provinsial`); login sudah lewat `redirectByRole`. Tanpa route cache, aktif tanpa restart. Notifikasi dengan URL spesifik tidak terpengaruh. Uji: tes redirect per role + Chrome headless (tamu, login, `/` ulang, tombol MASUK KE BERANDA, super admin tetap).
- **Ganti teks yang SUDAH tersimpan di DB** (mis. "Provinsial" -> "Provinsi" pada `author_role`): jangan UPDATE data. Tambah konstanta baru + konstanta lama + `normalizeRole()` di model, pakai saat TAMPIL dan saat SIMPAN; validasi `Rule::in` tetap menerima nilai lama (form ter-cache); form admin memilih opsi baru untuk data lama. Tes wajib menegaskan nilai di DB tidak berubah (`assertSame(lama, $m->fresh()->kolom)`). Tanyakan user hanya bila ingin seragamkan DB.
- Ubah HANYA yang dilingkari/disebut user; judul fitur ("Sapaan Provinsial") dan label form lain dilaporkan sebagai opsi terpisah, bukan diubah diam-diam.
- `md5sum database.sqlite` produksi berubah antar sesi itu wajar (aktivitas user); sebelum curiga, bandingkan jumlah baris tiap tabel dengan backup per jam dan cek `max(updated_at)`; tabel `users` tidak berubah = bukan ulah kita.
- Tes Chrome `innerText` mengikuti CSS uppercase: bandingkan dengan `.toLowerCase()`/`.toUpperCase()`.

## Pola mengunci aksi untuk role tertentu (Agenda Provinsi read-only untuk bruder)
- **Teks Menu Card Beranda User (Perubahan Bertahap)**: Saat user merevisi judul/deskripsi card beranda (mis. Bimbingan Rohani -> Pembimbing Rohani, subteks Laporan & Jadwal -> Laporan bimbingan; Wawanhati -> Pemimpin Lokal, subteks Pimpinan Lokal -> Laporan wawanhati), ubah HANYA teks di Blade `dashboard/user.blade.php`. Jangan ubah rute, fungsi controller, maupun skema DB.
- **Android Native Time Picker Inconsistency (<input type="time">)**: Di berbagai vendor Android (Oppo/Xiaomi/Realme), input `type="time"` memicu dialog clock-face modal bawaan OS yang jarumnya sulit diputar presisi dan tombol `Set/Simpan` terpotong di tepi layar pada font/display scaling non-standar. Solusi paling stabil: ganti dengan dua dropdown terpisah (`Jam` 00-23 dan `Menit` interval 5/15 menit) yang menggabungkan nilai ke hidden input `HH:mm`, sehingga controller backend dan validasi regex `^\d{2}:\d{2}$` tetap 100% kompatibel tanpa modifikasi backend.
- **Symmetrical Close Buttons (SVG vs HTML Entity `&times;`)**: Jangan gunakan karakter mentah `×` (`&times;`) pada tombol modal/drawer close karena font bawaan ponsel sering membuat garis silangnya miring, tipis, atau tidak di tengah. Gunakan inline SVG cross (`stroke-width="2.5"`) di dalam container flexbox centered (`display: inline-flex; align-items: center; justify-content: center;`).
- **Resilient Mobile Card Header & Status Badge Layout (Preventing Pill Wrapping)**: Ketika meletakkan nama/judul di sebelah status pill badge di card mobile, berikan `white-space: nowrap; flex-shrink: 0;` pada badge dan `flex: 1; min-width: 0; word-break: break-word;` pada judul/nama. Ini mencegah kata seperti `Terkirim` terpotong/patah menjadi dua baris (`Terkiri` / `m`) saat nama pengguna sangat panjang.
- **Jebakan `config:cache` pada Pengujian Laravel SQLite In-Memory**: Pada proyek Laravel yang tesnya memakai `RefreshDatabase` dengan `:memory:`, menjalankan `config:cache` akan mengunci database target ke file fisik `database.sqlite`, yang dapat memicu eksekusi tes di DB produksi jika proteksi tidak dicegah. Jangan pasang `config:cache` jika suite test dijalankan di server yang sama; gunakan `view:cache` dan `event:cache` saja.
- **PWA/TWA Image Caching Strategy (Menghindari Download Berulang Foto Profil)**:
  - Jangan mengecualikan foto profil dari Service Worker (`sw.js`). URL foto profil Laravel yang sudah dilengkapi query string versi hash (mis. `/profil/foto?v=hash` dari md5 berkas) aman 100% menggunakan strategi `staleWhileRevalidate` di SW.
  - Di backend controller / StreamedResponse, ubah header dari `private, no-cache, must-revalidate` menjadi `private, max-age=86400, stale-while-revalidate=604800`.
  - Ketika pengguna mengganti foto, hash URL berubah seketika, memaksa browser mengambil foto baru tanpa tertahan cache lama. Saat membuka TWA/PWA, gambar muncul instan (0 detik) dari memori lokal HP tanpa download ulang.
  - Setiap perubahan aturan SW, wajib menaikkan string konstanta `CACHE_VERSION` di `public/sw.js` agar seluruh perangkat klien memperbarui Service Worker secara otomatis.

- Kunci di SERVER, bukan hanya sembunyikan tombol: pada helper kepemilikan (`ownedSchedule()` di `User\AgendaController`) tambah `abort_if($model instanceof PersonalAgenda && $model->is_provincial && auth()->user()->role === 'user', 403, 'pesan jelas')`. Satu titik menutup edit/update/destroy sekaligus, tanpa ubah rute/middleware dan tanpa menyentuh DB.
- Teruskan penanda ke tampilan lewat objek item (`PersonalScheduleQuery::item(... bool $provincial=false)` -> `'provincial'`), lalu bungkus blok Edit/Hapus dengan `@unless($agenda->provincial && auth()->user()->role === 'user')` di `user/agenda/index` DAN `user/kalender/index` (cari `route('agenda.edit'` di semua view). Admin/super_admin yang membuka akunnya sendiri tidak terkunci; mereka kelola lewat Monitoring.
- Bukti tes: tes 403 untuk edit/update/destroy + agenda pribadi tetap bisa + tombol tersembunyi. Lalu SEMENTARA nonaktifkan perlindungan (`false && ...`, `@unless(false)`), pastikan tes gagal (4 gagal), pulihkan dari `cp` backup, jalankan suite penuh. Di Chrome kirim DELETE/PUT dengan token CSRF SAH (ambil `input[name=_token]` dari form agenda pribadi) dan harapkan 403 (token palsu menghasilkan 419 yang menyamarkan hasil); cek baris DB salinan tidak berubah.
- `&` di dalam isi skrip yang dijalankan foreground memicu penolakan \"backgrounding\": tulis skrip dengan write_file, gabungkan parameter body fetch dengan `[...].join(String.fromCharCode(38))`.

## Pola ganti tombol teks jadi ikon
Tombol \"+ Isi\" Checklist Formasi (`dashboard/user.blade.php`, 3 tautan inline-style) diganti lingkaran 34px berisi SVG plus (`<path d=\"M12 5v14M5 12h14\"/>`); warna, tujuan tautan tetap; tambah `aria-label`/`title`; tombol \"Lihat →\" untuk yang sudah terisi tidak diubah. Ganti dengan Python `assert s.count(lama)==1` per tombol. Uji Chrome: 34x34, radius 50%, tengah vertikal baris (selisih <1,5px), tinggi tombol <= tinggi baris-14, tanpa scroll horizontal di 320px, klik menuju form. Halaman network-first: `CACHE_VERSION` tidak perlu naik bila CSS/JS tak berubah. Akun uji \"belum mengisi\" dipilih dari salinan DB dengan kolom benar (`meeting_at`, `activity_date`, bukan `meeting_date`).

## Preferensi user (Yohsan) yang berulang pada perubahan UI/teks
- Permintaan sering berupa screenshot HP dengan **coretan merah**: ubah HANYA elemen yang dilingkari/disebut; sisanya (judul fitur, label form lain, tombol terkait) dilaporkan sebagai opsi, jangan diubah diam-diam. Akhiri laporan dengan satu pertanyaan tindak lanjut bila ada temuan sampingan (bug laten, teks lama tersisa).
- Awal pesan sering memuat batas keras: "jangan mengubah fungsi fitur lain", "jangan hapus database", "jika harus menyentuh database tanyakan dulu". Jawab dulu apakah DB tersentuh (biasanya TIDAK: tampilkan/normalkan di kode) dan tulis di laporan.
- Pertanyaan murni ("apakah memungkinkan?", "untuk kebutuhan ini cukup?") = jawab/periksa baca-saja, jangan eksekusi; bila perintah jelas ("tolong ubah...") langsung kerjakan lengkap sampai live.
- **Jebakan Tool Clarify di Telegram**: Hindari memanggil `clarify` (multiple-choice popup) untuk kalimat ambigu yang pendek seperti "Tampilan itu ada Branda admin" atau saat alur tanya-jawab biasa. Di aplikasi Telegram, rendering pilihan tombol interaktif membuat pengguna mengira asisten macet/stuck ("Ini kenapa stak di sini ya"). Gunakan teks klarifikasi biasa atau langsung paparkan opsi di badan pesan.
- Format laporan yang disukai: ringkas, tabel sebelum/sesudah, bagian "Yang tidak berubah", "Pembuktian" (jumlah tes, hasil Chrome nyata, status produksi), lalu "Hal yang perlu Anda ketahui". Tanpa emoji. Bahasa Indonesia.
- Perubahan tampilan di halaman yang didesain mobile: "rapikan susunan" berarti ukur dulu (getBoundingClientRect) dan perbaiki ketidaksejajaran nyata (mis. 38px vs 40px), bukan redesain.

## Pola label mengikuti penanda data (Agenda Provinsi vs pribadi)
Label subjudul kartu bruder dibuat di SATU tempat: `PersonalScheduleQuery` (`person:`). Dulu tertulis tetap 'Agenda pribadi', jadi agenda provinsi (disalin ke tiap akun) ikut berlabel pribadi. Perbaikan: `person: $agenda->is_provincial ? 'Agenda Provinsi' : 'Agenda pribadi'`. Satu baris menutup daftar Agenda, Kalender, dan pengingat Beranda. Cari sumber label dengan `grep -rn "Agenda pribadi" app resources` sebelum menyentuh view. Tes: ambil potongan HTML 700 karakter setelah judul kartu (`substr($html, strpos($html,$judul), 700)`) lalu `assertStringContainsString/NotContains`; buktikan sensitif dengan mengembalikan baris lama (3 tes harus gagal).
- Bug laten yang ketemu lewat screenshot user: kartu kalender (`user/kalender/index.blade.php`) kurang satu `</div>` (blok `item-card-meta`) sehingga kartu kedua pada tanggal yang sama tampak bersarang. Hitung `<div` vs `</div>` pada blok `@forelse` untuk mendeteksi. Laporkan dan TANYA user dulu bila di luar permintaan.

## Pola ganti teks header panel Admin (layout bersama)
Header `.sa-header` (lencana `.sa-badge`, `.sa-title`, `.sa-subtitle`) ada di `layouts/super-admin.blade.php`; judul/subjudul diisi per halaman lewat `$headerTitle/$headerSubtitle`, lencana peran ditentukan di layout (role `admin`, `admin_ketua_tppbm`, `super_admin`). Mengubah lencana = berubah di SEMUA halaman admin (9 view memakai layout); itu wajar, tapi WAJIB dilaporkan. Cari teks lama di `app resources tests`, ubah di sumber, sesuaikan tes yang memeriksa teks lama (tambah `assertSeeInOrder(['sa-badge',...,'sa-title',...,'sa-subtitle',...], false)`).
- Bukti sebelum/sesudah yang adil: rekam header SEMUA halaman x peran x lebar (412 dan 320 px) ke JSON dengan Chrome headless pada salinan DB; versi "sebelum" direkam dari `git worktree add /tmp/pembanding HEAD` (symlink `vendor`, salin `.env`) agar kode lama berjalan berdampingan; bandingkan teks, posisi, tinggi header, jumlah baris judul, scroll horizontal. Hapus worktree (`git worktree remove --force` + `prune`) setelahnya.
- Ukur dulu, baru "rapikan": mis. avatar 38px vs tombol menu 40px -> samakan 40px. Jangan menebak. Subjudul yang sudah 2 baris di 320px sebelum perubahan = bukan akibat kita (bandingkan dengan rekaman sebelum).
- Tulisan lama yang tersisa di luar permintaan (nama penulis bawaan form, teks halaman catatan, tombol "Kembali ke Beranda TPPBM") dilaporkan sebagai opsi, tidak diubah diam-diam.

## Pola Agenda Provinsi (referensi)
Kolom `personal_agendas.is_provincial` + `broadcast_key`; `PersonalAgenda::upcomingForOverview()` menggabungkan agenda provinsi per `broadcast_key` jadi satu kartu berlabel "Agenda Provinsi" dengan nama penulis **TPPBM** (user menolak "Seluruh Bruder Muda"), agenda pribadi tetap per bruder. Agenda "lainnya" yang ditulis role admin/super_admin otomatis `is_provincial=true`. Edit/hapus agenda provinsi berbasis `{key}` di tab Agenda Monitoring: detail di `references/agenda-provinsi-edit-hapus.md`.

## Infrastruktur & Audit Keamanan (referensi)
- Split DNS Web VPS vs Email cPanel (DomaiNesia), Cron backup DB ke Telegram (`no_agent: true` + Python zipfile + `MEDIA:`), dan penanganan temuan celah keamanan inspect browser (`APP_DEBUG=true`, header `X-Powered-By`, serta false positive CSRF/VAPID): rincian di `references/split-dns-email-dan-security-audit.md`.

## Prosedur Mode Pemeliharaan (Maintenance Mode 503) & Hardening
- **Protokol Komunikasi Pengguna**: Sebelum mengaktifkan `artisan down`, selalu buat draf tampilan teks `503` terlebih dahulu dan mintakan persetujuan user. Salam wajib santun biara/pengguna ("Berkah Dalem, Para Bruder yang Terkasih"), minta maaf atas ketidaknyamanan, dan nyatakan alasan sebagai "pemeliharaan sistem & peningkatan performa berkala". **Dilarang keras menyebut perbaikan celah/keamanan kepada pengguna** agar tidak menimbulkan kepanikan.
- **Perintah Eksekusi**: `php artisan down --render="errors.503" --secret="<kunci-bypass>" --refresh=60`. Opsi `--refresh=60` otomatis me-refresh browser pengguna tiap 60 detik sehingga begitu `php artisan up` dijalankan, layar aplikasi di HP pulih tanpa intervensi manual.
- **Jebakan Pengujian saat Mode Pemeliharaan**: File penanda `storage/framework/down` menyebabkan seluruh request HTTP pada suite tes (`php artisan test`) menerima status 503 (bukan 200). Selalu angkat sementara (`php artisan up`), jalankan tes 100%, lalu kunci kembali (`php artisan down ...`).
- **Hardening Dependensi Tanpa Breaking Changes**: Perbarui spesifik paket yang terkena advisory CVE dengan `composer update "symfony/*" "league/commonmark" --with-dependencies`. Selalu uji dry-run lebih dulu, cek `composer audit` (harus 0 advisories), dan pastikan seluruh test suite pass sebelum service di-restart.
- **Content-Security-Policy (CSP) Aman untuk PWA**: Pasang di reverse proxy (Caddy):
  `Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self';"`
- **Proteksi Crawling Portal Internal**: Pasang `Disallow: /` di `public/robots.txt` dan sisipkan `<meta name="robots" content="noindex, nofollow, noarchive">` di partial icon/layout bersama (`partials/fic-icons.blade.php`).


