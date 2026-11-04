# Audit Sistem Runtime PWA: Metodologi Empiris & Format Laporan

Dipakai saat pengguna meminta **audit** sebuah subsistem yang sudah berjalan — misal "apakah alurnya sudah benar", "masih banyak errornya", "cek kredensial akun". Berbeda dari perbaikan bug biasa: hasilnya adalah laporan temuan + keputusan pengguna, bukan langsung tambal.

## Prinsip Inti

**Membaca kode saja tidak cukup.** Audit berbasis pembacaan kode menghasilkan laporan yang terlihat rapi tapi melewatkan cacat runtime. Setiap klaim temuan wajib didukung keluaran nyata.

Contoh nyata: cacat "izin `granted` tanpa objek `PushSubscription`" tidak terlihat dari kode mana pun. Baru tampak saat dijalankan di browser sungguhan:
```
Notification.permission : granted
getSubscription() null? : True
token terkirim ke server: []
```

## Urutan Pengumpulan Bukti

1. **Keadaan database** — kueri langsung, baca-saja:
   ```python
   c = sqlite3.connect('file:database/database.sqlite?mode=ro', uri=True)
   ```
   Lihat siapa yang terdaftar, apakah ada baris dobel, kapan dibuat.

2. **Log galat aplikasi** — `grep -iE "<kata kunci>" storage/logs/laravel.log | tail -20`.
   Sering di sini akar masalahnya ketemu. Controller yang dibungkus `try/catch` membuat UI melaporkan "berhasil" sementara log berisi `TypeError`.

3. **Bandingkan versi live dengan repo lokal**:
   ```bash
   curl -s https://domain/sw.js | grep -E "^const CACHE_VERSION"
   grep -E "^const CACHE_VERSION" public/sw.js
   ```
   Beda = pengguna masih memakai berkas lama, dan semua kesimpulan dari kode lokal keliru.

4. **Cakupan kode** — fitur sering hanya terpasang di sebagian layout/halaman:
   ```bash
   grep -rln "notifikasi.js" resources/views/
   grep -rl "layouts.super-admin" resources/views/ | wc -l
   ```

5. **Status endpoint publik** — `curl -s -o /dev/null -w "%{http_code}"` untuk rute kunci. Rute terlindungi harus 302, bukan 200.

6. **Uji runtime di browser sungguhan** — hanya setelah lima langkah di atas.

## Harness Uji Runtime yang Aman

Server uji di port terpisah dengan **salinan** database. Jangan pernah menguji di DB produksi.

```python
shutil.copy(f'{APP}/database/database.sqlite', TMP)
env = dict(os.environ, DB_DATABASE=TMP, APP_URL=BASE,
           SESSION_SECURE_COOKIE='false', APP_ENV='local', SESSION_DRIVER='file')
subprocess.Popen(['php', 'artisan', 'serve', '--host=127.0.0.1',
                  f'--port={PORT}', '--no-reload'], cwd=APP, env=env)
```

Bersihkan setelah selesai (`finally`): matikan server, hapus salinan DB, hapus profil Chrome sementara. Laporkan ke pengguna bahwa DB asli tidak disentuh.

### Pitfall Harness (semua pernah menghasilkan hasil palsu)

| Gejala | Penyebab | Perbaikan |
|---|---|---|
| Judul halaman jadi `127.0.0.1`, semua penanda kosong | `php -S` + `server.php` gagal diam | Pakai `php artisan serve --no-reload` |
| `SSL: UNEXPECTED_EOF_WHILE_READING` saat buka `/` | `APP_URL` produksi `https://` memicu `URL::forceScheme('https')` | Timpa `APP_URL=http://127.0.0.1:<port>` di env uji — **jangan** ubah kode aplikasi |
| Login selalu gagal, tetap di `/login` | Cookie sesi bertanda `secure` tak tersimpan di HTTP | `SESSION_SECURE_COOKIE=false` di env uji |
| Login gagal tanpa pesan jelas | Akun uji ter-soft-delete | Sertakan `AND deleted_at IS NULL` saat memilih akun uji |
| Uji logout "lulus" padahal tak terjadi apa-apa | Form logout tidak ada di halaman yang ditembak | Verifikasi dulu: `js("!!document.querySelector('form[action*=\"/logout\"]')")` |
| Izin browser selalu `default` | Dialog izin tak bisa diklik di headless | `cmd('Browser.grantPermissions', origin=BASE, permissions=['notifications'])` |

**Aturan emas**: kalau hasil uji tampak terlalu rapi (semua nol, semua kosong, semua `False`), **curigai harness lebih dulu** sebelum menyimpulkan tentang aplikasi. Verifikasi prasyarat — `location.pathname` setelah login, keberadaan elemen target — sebelum melaporkan cacat.

## Format Laporan Audit

Struktur yang terbukti diterima pengguna:

1. **Metode** — satu baris: apa yang diperiksa dan dengan apa, plus jaminan DB asli tidak disentuh.
2. **Ringkasan verdict** — sesuai keinginan pengguna atau belum, plus jumlah temuan. Sebutkan juga kabar baiknya (fondasi mana yang sudah benar) agar pengguna tidak panik.
3. **Temuan berkode per keparahan** — `K1`, `K2`, `S1` dst. Kode penting supaya pengguna bisa merujuk singkat di diskusi lanjutan.
4. **Bukti keluaran nyata** di tiap temuan, dalam blok kode. Bukan narasi.
5. **Tabel "Yang Sudah Benar"** — kolom komponen + status.
6. **Pelurusan harapan** bila ada batas teknologi yang tak bisa dilampaui.
7. **Rencana perbaikan bernomor** dengan kolom risiko.
8. **Minta keputusan pengguna** lewat `clarify` sebelum eksekusi.

### Saat Pengguna Minta Rincian Sebelum Memutuskan
Uraikan tiap perbaikan dengan kerangka tetap: masalah yang diperbaiki → berkas yang diubah → mengapa aman → risiko → dampak ke pengguna.

Lalu tutup dengan tabel perbandingan:

| # | Perbaikan | Berkas | Ubah Tampilan | Ubah DB | Risiko | Dampak |
|---|---|---|---|---|---|---|

**Tandai eksplisit** mana yang mengubah tampilan atau menambah fitur. Bila ada, tawarkan **"versi minimal"** yang mencapai tujuan teknis tanpa mengubah tampilan, dan sebutkan bahwa versi penuh menunggu izin. Kunci kontrak itu dengan tes negatif:
```php
$this->assertStringNotContainsString('id="notifBell"', $html);
```

## Pisahkan Error dari Saran
Jangan laporkan peringatan opsional sebagai kerusakan. Periksa penghitung error/warning alat (mis. error `0`, warning `2`) dan sampaikan mana yang wajib diperbaiki dan mana yang aman diabaikan beserta alasannya.

## Perbaikan Bisa Berada di Luar Repo
Audit yang hanya menyisir repo akan melewatkan cacat pada artefak di luarnya: berkas APK, berkas konfigurasi web server, berkas statis `.well-known/`, atau pengaturan di layanan pihak ketiga. Saat semua bukti sisi server sudah bersih (tes lulus, log bersih, pengiriman nyata berhasil) tetapi pengguna tetap melaporkan gagal, **geser pencarian ke artefak di luar repo** sebelum menyimpulkan "ini batas platform" atau menyalahkan pengaturan perangkat pengguna. Lihat `twa-apk-packaging-notifications.md` §1 untuk kasus nyatanya.

## Koreksi Diri Saat Klaim Terbukti Salah
Audit yang panjang hampir pasti memuat satu-dua klaim yang kemudian terbantah oleh bukti baru. Sesi ini menghasilkan dua:
- "`setAppBadge` adalah API `window`, tidak tersedia di Service Worker" — MDN ternyata mencantumkan `WorkerNavigator.setAppBadge()`. Keputusan memindahkannya tetap benar, tapi **alasannya** berbeda (pemanggilan tanpa argumen tidak menghasilkan angka).
- "Panel itu tidak punya opsi notifikasi" — pemeriksaan DOM membuktikan opsinya ada, hanya di panel berbeda.

Pola yang dihargai pengguna: sebut eksplisit **"saya perlu mengoreksi diri"**, tunjukkan bukti barunya, lalu nyatakan apakah keputusan sebelumnya tetap berlaku atau ikut berubah. Menutupi kekeliruan lebih merugikan daripada mengakuinya — terutama saat pengguna sedang menguji di perangkat nyata dan akan menemukannya sendiri.

Turunannya: **dokumentasi resmi bisa tertinggal dari antarmuka/perilaku nyata**. Kalau urutan atau nama opsi di dokumentasi tidak cocok dengan laporan pengguna, verifikasi ke sumber hidup (DOM situs, refleksi library, bongkar berkas) sebelum menyalahkan pengguna salah lihat.

## Saat Pengguna Ingin Tahu Sebelum Memilih
Pengguna ini biasanya minta tahap **"jelaskan dulu"** sebelum menyetujui. Jangan lewati dengan langsung eksekusi. Untuk tiap opsi, pakai kerangka tetap: cara kerja → keuntungan → risiko → dampak nyata ke pengguna, lalu tabel perbandingan, lalu rekomendasi **beserta alasan jangka panjang** (bukan hanya mana yang paling cepat hari ini).

Sertakan juga **jalan keluar bila pilihan utama gagal** ("kalau ditolak, beralih ke B, saya tangani sisi server"). Itu mencegah pengguna terhenti di tengah jalan saat bekerja sendiri di perangkatnya.

## Urutan Eksekusi Setelah Disetujui
1. Backup DB + verifikasi `PRAGMA integrity_check`.
2. Kerjakan perbaikan per butir, dari yang paling berdampak.
3. Tes baru per perbaikan, termasuk **tes keamanan** bila ada endpoint tanpa autentikasi.
4. Jalankan seluruh suite lama — laporkan selisih jumlah tes (mis. 117 → 123) sebagai bukti tak ada regresi.
5. Uji runtime di browser dengan salinan DB.
6. Uji pengiriman/efek nyata pada data produksi bila aman dan relevan.
7. Naikkan versi cache aset statis.
8. Verifikasi domain publik.
9. Backup DB lagi + hitung ulang semua tabel.
10. Commit deskriptif (daftar temuan + perbaikannya) lalu push **ke branch yang diminta**, bukan `main`. Tutup dengan menunjukkan `main` masih di commit lama.
