---
name: pwa-web-push-twa
description: Web Push (VAPID/FCM) untuk PWA Laravel + pembungkus APK TWA (PWABuilder). Audit, pendaftaran token otomatis, rotasi token, panel admin, keystore/assetlinks, dan cara verifikasi nyata di Chrome headless dengan salinan DB.
---

# PWA Web Push + TWA (PWABuilder)

Berlaku untuk PWA Laravel (Minishlink WebPush) yang juga dibungkus APK TWA. Contoh nyata: PWA Bruder FIC.

## Aturan kerja
- Klaim teknis (dukungan API, opsi PWABuilder, penyebab toggle mati) WAJIB diverifikasi ke sumber nyata (MDN, docs.pwabuilder.com, bongkar APK) sebelum dinyatakan. Bila klaim terbukti salah, koreksi terbuka di jawaban.
- Jangan sentuh DB asli saat uji. Pakai salinan (`DB_DATABASE=/tmp/x.sqlite`, port acak) dan backup sebelum/sesudah.
- Pertanyaan user = jawab saja. Bila user minta "jelaskan dulu per opsi", beri tabel masalah/berkas/risiko/dampak, lalu `clarify` pilihan.

## Pola kode (sudah terbukti)
1. `syncSubscription()` di JS halaman: jika izin `granted` tapi belum ada langganan, BUAT langganan lalu kirim ke server. Izin `default`/`denied` jangan dipaksa. Tanpa ini perangkat kedua tidak pernah terdaftar.
2. Logout mencabut token; login akun lain di perangkat sama memindahkan pemilik endpoint (bukan dobel).
3. Rotasi token: handler `pushsubscriptionchange` di `sw.js` memanggil `POST /push/rotate`. Rute harus DI LUAR grup `auth`, dikecualikan CSRF (`bootstrap/app.php` `validateCsrfTokens(except)`), `throttle`, dan kepemilikan diambil dari baris endpoint lama di DB, bukan dari input. `GET /push/vapid-key` publik (kunci publik bukan rahasia).
4. Layout panel admin juga perlu `<meta name="csrf-token">` + skrip notifikasi supaya token admin terdaftar/dicabut (tanpa lonceng bila user tak ingin UI baru).
5. Tiap ubah `sw.js`/CSS: naikkan `CACHE_VERSION`, `PRECACHE_URLS ?v=`, dan `?v=` aset di layout.

## Fakta terverifikasi (MDN)
- Badging API `setAppBadge`: TIDAK didukung Chrome Android, Samsung Browser, WebView Android; ada di Chrome desktop 81+, Safari iOS 16.4+. Tersedia juga di `WorkerNavigator`. Angka/titik di ikon Android berasal dari notifikasi sistem + pengaturan launcher (ColorOS vs MIUI beda), bukan dari kode.

## TWA / PWABuilder
- Panel Google Play punya urutan: Splash fade, Settings shortcut, Include source code, Display mode, Notification delegation, Location delegation, Google Play billing, Signing key (New / Use mine), ChromeOS only, Meta Quest, Fallback. Panel "other Android stores" TIDAK punya Signing key. Cek kaki panel: "Google Play Store". Ada 3 tombol Generate Package: Windows, Google Play (kedua), iOS.
- Pakai "Use mine" + keystore lama agar SHA-256 sama dengan `assetlinks.json`; bila "New", sidik jari berubah dan harus digabung di server.
- Verifikasi hasil zip: package ID, SHA-256 (`unzip META-INF/*.RSA` lalu `openssl pkcs7 -inform DER -print_certs | openssl x509 -fingerprint -sha256`), bandingkan string manifest APK lama vs baru (`AndroidManifest.xml` decode utf-16-le).
- JANGAN klaim `DELEGATE_NOTIFICATIONS` hilang = penyebab toggle notifikasi mati. Itu tebakan yang terbantah: delegasi TWA memakai `DelegationService` yang sudah ada di APK lama. Mengaktifkan Location delegation menambah izin lokasi tak perlu. Penyebab toggle mati di Oppo Reno belum terbukti (dugaan: izin POST_NOTIFICATIONS Android 13+ belum pernah diminta/ditolak). Tanya: toggle bereaksi atau tidak, versi Android, buka via APK atau Chrome, teks lonceng.

## Keamanan keystore
`signing.keystore` dan `signing-key-info.txt` (berisi sandi) JANGAN dilacak git, terutama bila repo publik: SHA-256 keystore itu terdaftar di `assetlinks.json`, jadi pemegangnya bisa menandatangani APK yang tampil layar penuh sebagai aplikasi resmi. Simpan di luar repo (`~/backups/twa-kunci/`, chmod 600) + `.gitignore`. Rotasi kunci mengharuskan build ulang dan pasang ulang APK di semua HP; tawarkan sebagai pilihan, jangan paksa.

## Catatan tambahan
- APK baru dari PWABuilder yang dikirim user: bandingkan string manifest lama vs baru; bila hanya menambah izin lokasi dan tidak ada perubahan komponen notifikasi, sarankan jangan dipasang. Kedua zip bisa identik (cek md5).
- Alur kerja perubahan aman (backup, migrasi aditif, uji salinan DB): lihat skill `laravel-production-safe-change`.

## Navigasi panel PWABuilder (browser tool)
Halaman memakai Web Components; snapshot biasa nyaris kosong. Telusuri shadow DOM lewat `browser_console` (fungsi rekursif `querySelectorAll` + `el.shadowRoot`), klik "Package For Stores", lalu "Generate Package" indeks 1 (Google Play). Baca judul bagian dari `h3/label`. Jangan menyimpulkan panel "tidak punya opsi" dari screenshot user sebelum membandingkan kaki panel dan urutan opsi dengan panel yang benar.

## Verifikasi nyata
Lihat `references/verifikasi-chrome-headless.md` untuk resep uji ujung ke ujung (salinan DB, `artisan serve`, Chrome headless + CDP via websocket-client).
