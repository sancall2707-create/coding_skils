# Membungkus PWA jadi TWA APK: Notifikasi, Keystore, & Digital Asset Links

Dipakai saat pengguna ingin notifikasi/lencana menempel pada ikon aplikasi sendiri, bukan menginduk ke ikon Chrome. Lanjutan dari `pwa-web-push-android-badging.md` §3 dan §3a — baca itu dulu untuk batas kejujuran yang wajib disampaikan.

## 1. Cacat Bisa Ada di Dalam APK, Bukan di Kode Web

Pelajaran terpenting sesi ini: **sistem Web Push bisa 100% benar di server dan tetap gagal** karena manifest APK kurang satu penanda.

Gejala khas yang menyesatkan:
- Server terbukti mengirim (`hasil kirim: 1 terkirim`, tanpa galat di log).
- Token ada di `push_subscriptions`.
- Tapi di HP, toggle notifikasi aplikasi di **Pengaturan Android mati dan tidak bisa dinyalakan**.

Godaan diagnosis yang **salah**: menyalahkan kebijakan launcher HP (ColorOS vs MIUI) lalu menyuruh pengguna mengubah pengaturan lencana. Itu membuang waktu pengguna karena akar masalahnya di berkas APK.

## 2. Bongkar `AndroidManifest.xml` di Dalam APK Tanpa Alat Android

APK adalah berkas zip. `AndroidManifest.xml` di dalamnya berbentuk AXML biner, tapi *string pool*-nya tersimpan UTF-16LE sehingga bisa dibaca tanpa `apktool`/JDK — penting di VPS dengan RAM terbatas.

```python
import zipfile, re

z = zipfile.ZipFile('Bruder FIC.apk')
teks = z.read('AndroidManifest.xml').decode('utf-16-le', errors='ignore')
kandidat = re.findall(r'[\x20-\x7e]{6,}', teks)

# daftar izin
for i in sorted(set(k for k in kandidat if 'permission' in k.lower())):
    print(' ', i)

# penanda kunci
for kunci in ['POST_NOTIFICATIONS', 'DELEGATE_NOTIFICATIONS',
              'DelegationService', 'customtabs.trusted', 'com.contoh.twa']:
    print(f'{kunci:24s}:', 'ADA' if kunci.lower() in teks.lower() else 'TIDAK ADA')
```

## 3. Penanda Wajib: `DELEGATE_NOTIFICATIONS`

Pada TWA, isi aplikasi dijalankan mesin Chrome. Saat Service Worker memanggil `showNotification()`, yang memunculkan notifikasi sebenarnya **Chrome**, bukan APK Anda. Agar notifikasi tampil atas nama aplikasi sendiri, manifest APK wajib memuat:

```xml
<meta-data
    android:name="android.support.customtabs.trusted.DELEGATE_NOTIFICATIONS"
    android:value="true" />
```

**Jebakan**: APK bisa punya `POST_NOTIFICATIONS`, `NotificationPermissionRequestActivity`, dan `DelegationService` — tampak lengkap — tapi **tanpa** `DELEGATE_NOTIFICATIONS`. Hasil nyata dari sesi ini:

```
POST_NOTIFICATIONS                    : ADA
NotificationPermissionRequestActivity : ADA
DelegationService                     : ADA
DELEGATE_NOTIFICATIONS                : TIDAK ADA   <-- penyebabnya
```

Rantai akibatnya: Android tak pernah melihat aplikasi mengirim notifikasi → saluran notifikasi tak pernah terbentuk → toggle di Pengaturan mati dan tak bisa dinyalakan.

**Petunjuk pembanding yang berguna**: aplikasi yang punya saluran notifikasi menampilkan teks seperti *"Aktifkan notifikasi aplikasi ini untuk menyesuaikan pengaturan"* dengan chevron. Aplikasi tanpa saluran hanya menampilkan toggle mati tanpa keterangan. Minta pengguna bandingkan baris aplikasi lain di layar yang sama.

## 4. PWABuilder: Panel yang Benar & Letak Opsinya

PWABuilder punya **3 tombol `Generate Package`** berurutan. Pengguna mudah tersesat karena ketiga panel berpenampilan mirip.

| Urutan | Toko | Punya `Signing key` & `Notification delegation`? |
|---|---|---|
| 1 | Microsoft Store (Windows) | tidak relevan |
| 2 | **Google Play (Android)** | **ya — pakai ini** |
| 3 | Experimental App Store (iOS) | tidak |

Tab **"Other Android"** terlihat mirip tapi **tidak punya `Signing key`**, jadi tidak bisa memakai keystore lama.

**Cara pengguna memastikan panel yang benar** — baca teks di kaki panel:
- Benar: *"...instructions on how to submit to **the Google Play Store**."*
- Salah: *"...instructions on how to submit to **other Android stores**."*

**Urutan opsi panel Google Play** (diverifikasi langsung dari DOM situs, bukan dari dokumentasi):
```
Splash fade out duration (ms)
Settings shortcut
Include source code
Display mode              <-- Standalone / Fullscreen / Fullscreen sticky
Notification delegation   <-- DI SINI, tepat setelah Display mode
Location delegation
Google Play billing
Signing key               <-- New / Use mine
ChromeOS only
Meta Quest compatible
Fallback behavior
```

**Cara mendiagnosis dari tangkapan layar pengguna**: hitung opsi yang hilang. Kalau pengguna melihat `Display mode → Meta Quest compatible → Fallback behavior`, berarti **lima opsi terlewat** — mustahil pada panel yang sama, jadi pasti panel yang berbeda. Jangan menyimpulkan "opsi itu tidak ada".

### Dokumentasi PWABuilder bisa tertinggal dari antarmuka
`Meta Quest compatible` muncul di situs tapi tidak terdaftar di dokumentasi mana pun. Jadi **verifikasi ke DOM situs**, jangan hanya percaya dokumentasi:

```js
// telusuri shadow DOM — PWABuilder memakai Web Components,
// sehingga querySelector biasa dan snapshot aksesibilitas tidak menemukannya
function cariSemua(sel, akar = document, kedalaman = 0, keluar = []) {
  if (kedalaman > 12) return keluar;
  for (const el of akar.querySelectorAll(sel)) keluar.push(el);
  for (const el of akar.querySelectorAll('*')) {
    if (el.shadowRoot) cariSemua(sel, el.shadowRoot, kedalaman + 1, keluar);
  }
  return keluar;
}
const gp = cariSemua('button, a').filter(b => /Generate Package/i.test(b.textContent || ''));
gp[1].click();   // indeks 1 = Google Play
```
Untuk memetakan tombol ke tokonya, naik ke elemen induk (termasuk `getRootNode().host`) dan baca `textContent`-nya.

## 5. Keystore & Digital Asset Links: Kontinuitas Sidik Jari

Android membandingkan sidik jari SHA-256 APK dengan yang terdaftar di `/.well-known/assetlinks.json`. Tidak cocok = muncul bilah alamat Chrome di atas layar, atau aplikasi gagal dibuka.

Ambil nilai acuan sebelum membangun ulang:
```bash
curl -s https://domain/.well-known/assetlinks.json | python3 -c "
import json,sys
t = json.load(sys.stdin)[0]['target']
print('package :', t['package_name'])
print('SHA-256 :', t['sha256_cert_fingerprints'][0])"
```

### Dua jalur, dan konsekuensi jangka panjangnya

| | A: `Use mine` (keystore lama) | B: `New` lalu gabung sidik jari |
|---|---|---|
| Ubah server | tidak | ya (`assetlinks.json`) |
| Unggah berkas & sandi | ya | tidak |
| Pasang menimpa APK lama | bisa | **tidak** — `INSTALL_FAILED_UPDATE_INCOMPATIBLE` |
| Jumlah kunci dijaga | 1 | 2, mudah tertukar nanti |
| Siap ke Play Store | ya | menyulitkan (Play mengikat 1 aplikasi : 1 kunci) |

**Sarankan A** bila aplikasi akan diperbarui berkali-kali. `sha256_cert_fingerprints` berupa senarai, jadi B tetap sah — tambahkan sidik jari baru di samping yang lama agar APK lama tetap jalan.

Nilai yang perlu disiapkan untuk `Use mine` (ada di `signing-key-info.txt` dalam zip PWABuilder): berkas `signing.keystore`, *key store password*, *key alias*, *key password*. Sarankan pengguna **menempel**, bukan mengetik, karena sandinya acak campur huruf besar-kecil.

**Cara memastikan pengguna benar memilih `Use mine`**: begitu dipilih, kolom *Key full name*, *Key organization*, *Key organizational unit* **hilang** dan berganti tombol unggah berkas. Kalau kolom itu masih ada, pilihannya masih `New`.

## 6. Isi Paket PWABuilder & Penanganannya

```
Bruder FIC.apk          # pasang langsung ke HP (sideload)
Bruder FIC.aab          # untuk unggah ke Play Store
signing.keystore        # WAJIB disimpan, dipakai ulang tiap build
signing-key-info.txt    # sandi & alias — jangan di-commit mentah ke repo publik
assetlinks.json         # taruh di public/.well-known/assetlinks.json
Readme.html
```

Pasang asset links di Laravel — cukup berkas statis, tanpa rute:
```bash
mkdir -p public/.well-known
# tulis assetlinks.json dari zip ke public/.well-known/assetlinks.json
curl -sI https://domain/.well-known/assetlinks.json | head -5   # harus 200, content-type application/json
```

Abaikan `.apk`/`.aab` di git (berkas besar), tapi simpan `signing.keystore`:
```gitignore
twa-release/*.apk
twa-release/*.aab
```

## 7. Naikkan Versi Tiap Build Ulang
`App version` (mis. `1.0.0` → `1.0.1`) dan `App version code` (`1` → `2`). Tanpa ini Android menganggapnya bukan pembaruan.

## 8. Pisahkan Peringatan Opsional dari Kerusakan
PWABuilder menampilkan penghitung: error merah, warning kuning, info biru. Saran seperti *"Add screenshots to showcase your app"* hanya untuk tampilan etalase Play Store — **tidak** memengaruhi fungsi APK maupun notifikasi. Bila error merah `0`, sampaikan bahwa peringatan kuning aman diabaikan beserta alasannya, supaya pengguna tidak panik.

## 9. Urutan Diagnosis Saat Notifikasi Gagal di TWA
1. Token ada di `push_subscriptions`? (jika kosong, lihat `pwa-web-push-android-badging.md` §5)
2. Uji kirim nyata dari server — berapa terkirim? Cek `storage/logs/laravel.log`.
3. **Bongkar manifest APK** — ada `DELEGATE_NOTIFICATIONS`? (§2, §3)
4. `assetlinks.json` 200 dan sidik jarinya cocok dengan APK terpasang? (§5)
5. Baru setelah itu, pengaturan lencana di launcher HP.

Langkah 3 paling sering terlewat dan paling sering jadi penyebabnya.

## 10. Verifikasi Sebelum Pengguna Memasang APK
Minta pengguna mengirim zip hasil build, lalu periksa **sebelum** mereka pasang:
1. `DELEGATE_NOTIFICATIONS` ada di manifest.
2. Package ID masih sama persis.
3. SHA-256 cocok dengan yang live di server — kalau beda, perbarui `assetlinks.json`.

Katakan eksplisit "jangan dipasang dulu sebelum saya periksa". Memasang APK dengan sidik jari tak cocok memaksa pengguna menghapus-pasang ulang.
