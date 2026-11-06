---
name: app-user-manual-book
description: Membuat manual book / panduan pengguna bergambar (PDF) untuk PWA/aplikasi web - teks diambil dari kode nyata, tangkapan layar Chrome headless dari SALINAN DB yang namanya disamarkan, audit kebocoran data pribadi, dan cetak PDF A4 dengan Chrome. Dipakai untuk PWA Bruder FIC (Laravel).
---

# Manual book aplikasi (PDF bergambar, data disamarkan)

Dipakai saat user minta "buatkan manual book / panduan pengguna agar mudah dipahami". Balas Bahasa Indonesia, singkat. Jangan sentuh DB asli.

## Alur
1. **Kumpulkan fakta dari kode, jangan menebak**: `php artisan route:list --except-vendor` (opsi `--columns` tidak ada), `grep` label tombol di layout/navbar (`user-app.blade.php`, `sa-bottom-nav.blade.php`, `sa-menu.blade.php`), aturan validasi di controller (`min:`, `max:`, `mimes:`, `before_or_equal`), pilihan `<select>`, redirect per role (`redirectByRole`), batas login (RateLimiter), SESSION_LIFETIME.
2. **Tangkapan layar**: salin DB ke `/tmp`, samarkan SEMUA nama (user, admin, pesan sapaan `author_name`, catatan, jurnal narasumber, formasi_data, foto, bukti), set password uji (hash bcrypt di salinan saja), jalankan `artisan serve` port uji dengan `DB_DATABASE`, `LARAVEL_STORAGE_PATH`, `SESSION_SECURE_COOKIE=false`, ambil foto lewat Chrome headless + CDP (websocket-client): viewport 430px, `deviceScaleFactor=2`, `captureScreenshot`. Skrip acuan: `scripts/manual_shots.py`.
3. **Audit kebocoran 3 lapis (wajib)**: (a) scan semua kolom teks salinan DB untuk pola nama asli; (b) di skrip, sebelum tiap foto cek `document.body.innerText` + nilai `input/textarea` terhadap daftar nama asli (outerHTML terlalu berisik, nilai bawaan form dan default di kode ikut bocor, mis. `author_name` default di Blade dan penandatangan raport); koreksi lewat `js()` sebelum foto; (c) ekstrak teks PDF akhir dan cari lagi. Vision hanya pelengkap, bukan satu-satunya audit.
4. **Cek tiap foto dengan vision**: halaman 404/kosong (ukuran file kecil ~20 KB = curiga). Penyebab nyata 404: memakai id user yang soft-deleted; pilih `where is_active=1 and deleted_at is null`. Akun penyamaran bentrok `UNIQUE username`: set dulu `username='tmp_'||id` untuk non-user, baru isi ulang.
5. **Tulis HTML manual** (sampul + daftar isi + bab per peran + aturan/batas + FAQ + keamanan + istilah). Pakai fakta dari kode; verifikasi klaim ragu-ragu ke kode sebelum dicetak (contoh koreksi: sapaan tampil SETIAP login bruder, bukan hanya saat ada pesan baru; label logout "LOGOUT DARI APLIKASI"; hint foto profil "5 MB" walau validasi 10 MB).
6. **Cetak**: `google-chrome-stable --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=out.pdf file:///.../manual.html`. Footer/nomor halaman pakai `@page { @bottom-center { content: counter(page) } }`; tanpa `--no-pdf-header-footer` Chrome menyisipkan tanggal dan path.
7. **Periksa hasil PDF nyata**: pasang pymupdf di venv sementara (`uv venv /tmp/pdfv; uv pip install pymupdf`), hitung halaman, ukur halaman longgar (blok terbawah / area cetak), render halaman ke PNG untuk vision, lalu hapus venv. Pratinjau HTML TIDAK sama dengan pemisahan halaman cetak.

## Pitfall tata letak (sudah terjadi)
- Gambar mengambang kanan (`float:right`) harus diletakkan SEBELUM teks di DOM; kalau sesudah, teks tidak mengalir di sisi kirinya dan halaman separuh kosong. Pola `.row > figure` lalu `.txt`.
- Flexbox dengan `break-inside` membuat gambar tinggi terdorong ke halaman baru (halaman hampir kosong). Pakai float + `max-height` ~138mm.
- Potong gambar panjang pada rasio tinggi:lebar terkontrol, jangan memotong di tengah kartu/tombol Simpan; sertakan tombol aksi yang dirujuk langkah.
- Bab 9+10 pendek: jangan `break-before: page` untuk semuanya; hanya bab utama.
- Hasil akhir yang dicapai: 30 halaman A4, 3 MB, hanya 1 halaman longgar. Teks di dalam foto HP kecil; akui keterbatasan itu ke user.

## Hal yang dilaporkan ke user
Setelah perilaku aplikasi berubah (mis. halaman pertama bruder = Sapaan setiap buka aplikasi, istilah "Provinsi" menggantikan "Provinsial", header Admin: lencana "TPPBM", judul "Beranda", subjudul "Tim Pemantap Panggilan Bruder Muda", tombol "+ Isi" jadi ikon +, Agenda Provinsi tanpa Edit/Hapus untuk bruder), cek apakah teks dan foto manual masih cocok; ulang `scripts/manual_shots.py` dan cetak ulang bila foto lama sudah berbeda dari aplikasi. Manual edisi 5 Nov 2026 sudah ketinggalan pada butir-butir ini (bab 4.1 masih menyebut tombol "+ Isi", bab 5.1 menyebut "Beranda TPPBM" dan lencana lama, bab 4.4 belum menyebut agenda provinsi read-only); tawarkan revisi ke user, jangan diam-diam.
Jumlah halaman, lokasi berkas (`/home/ubuntu/manual-book/`: PDF, `manual.html`, `img/`), kirim PDF lewat `MEDIA:`, apa yang diverifikasi (md5 DB asli tidak berubah, nama asli 0), keterbatasan (foto kecil, bagian yang belum teruji seperti toggle notifikasi Reno).

Skrip penyamaran/foto: `scripts/manual_shots.py` (sesuaikan tabel/kolom dan daftar `ASLI`).
