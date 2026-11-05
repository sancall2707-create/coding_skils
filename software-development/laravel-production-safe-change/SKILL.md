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

## Pola Agenda Provinsi (referensi)
Kolom `personal_agendas.is_provincial` + `broadcast_key`; `PersonalAgenda::upcomingForOverview()` menggabungkan agenda provinsi per `broadcast_key` jadi satu kartu berlabel "Agenda Provinsi" dengan nama penulis **TPPBM** (user menolak "Seluruh Bruder Muda"), agenda pribadi tetap per bruder. Agenda "lainnya" yang ditulis role admin/super_admin otomatis `is_provincial=true`. Edit/hapus agenda provinsi berbasis `{key}` di tab Agenda Monitoring: detail di `references/agenda-provinsi-edit-hapus.md`.
