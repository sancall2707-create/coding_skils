# TWA (Trusted Web Activity) / WebAPK Packaging & Android Badging

## Ringkasan Masalah & Solusi
Di Android, saat PWA diinstal lewat browser Chrome ("Tambahkan ke layar utama" atau WebAPK otomatis):
1. Proses induk notifikasi push tetap dipegang oleh paket Google Chrome (`com.android.chrome`).
2. Launcher Android (MIUI / HyperOS / Samsung / Pixel) menempelkan badge notifikasi (titik atau angka merah) ke **ikon induk (Chrome)** di dock, bukan ke shortcut PWA di layar utama.
3. Solusi definitif: Bungkus PWA menjadi APK mandiri berbasis **Trusted Web Activity (TWA)** dengan package ID tersendiri (misal: `com.formatio_fic.twa`).

---

## 1. Digital Asset Links (`.well-known/assetlinks.json`)
Agar TWA terbuka dalam mode **100% fullscreen** (tanpa bilah URL browser Chrome di atasnya), domain PWA wajib memverifikasi kepemilikan APK:

1. Buat direktori `public/.well-known/`.
2. Simpan file `assetlinks.json` dengan struktur:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "<package_id_anda>",
    "sha256_cert_fingerprints": [
      "<SHA256_FINGERPRINT_DARI_SIGNING_KEYSTORE>"
    ]
  }
}]
```
3. Pastikan endpoint dapat diakses publik dengan header `application/json`:
```bash
curl -sI https://domain.com/.well-known/assetlinks.json
# Wajib HTTP 200 OK
```

---

## 2. Alur Pembuatan APK Hemat Resource (Cloud PWABuilder vs Lokal)
- **Kondisi VPS Terbatas (RAM < 4GB, Swap > 1GB):**
  - JANGAN jalankan Gradle / Android SDK build di terminal VPS. Kompilasi Android memakan RAM 1.5–2GB dan rentan memicu OOM (Out of Memory) yang dapat mematikan proses web server (502 blank screen).
  - Gunakan **PWABuilder** (Microsoft / Google):
    1. Buka `https://www.pwabuilder.com`.
    2. Masukkan URL PWA (`https://domain.com`).
    3. Pilih *Package for Stores* -> *Android / Google Play*.
    4. Atur Package ID, nama app, download package `.zip`.
    5. Di dalam file zip terdapat:
       - `<App_Name>.apk` (siap instal di HP).
       - `signing.keystore` & `signing-key-info.txt` (simpan untuk update masa depan).
       - `assetlinks.json` (ambil fingerprint SHA-256 untuk dipasang di server).

---

## 3. Git Workflow untuk Build Artefak
- Jangan simpan file biner `.apk` dan `.aab` ke dalam git repository (bikin repo bengkak).
- Tambahkan ke `.gitignore`:
```gitignore
twa-release/*.apk
twa-release/*.aab
```
- Simpan file keystore dan info signing di branch fitur (`feat/twa-apk-notification`), jangan campur ke `main` sebelum disetujui.

---

## 4. Web Push + TWA Notification Routing
- Service Worker tetap menggunakan listener `push` dan `notificationclick`.
- Di `notificationclick`:
```javascript
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
            for (const c of list) {
                if (new URL(c.url).pathname === url && 'focus' in c) {
                    return c.focus();
                }
            }
            return clients.openWindow(url);
        })
    );
});
```
- Karena aplikasi terpasang sebagai TWA mandiri ber-package name sendiri, OS Android akan mengarahkan lencana notifikasi dan klik notifikasi langsung ke jendela TWA, bukan ke Chrome.
