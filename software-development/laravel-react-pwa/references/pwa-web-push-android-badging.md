# Web Push Notifications & Badging Patterns in PWA (Android)

Pola dan kendala integrasi Web Push & App Icon Badging pada Progressive Web App (PWA) berbasis Laravel & Service Worker.

## 1. WebPush Library (minishlink/web-push v11) Signature Pitfall
Pada `minishlink/web-push` versi 11.x, urutan dan tipe parameter konstruktor berubah:
```php
// SALAH (pola v7-v8):
new WebPush($auth, [], 30, ['verify' => true]);
// Menyebabkan TypeError: Argument #3 ($client) must be of type ?Psr\Http\Client\ClientInterface, int given

// BENAR (v11):
$defaultOptions = ['TTL' => 86400]; // atau opsi default lain
new WebPush($auth, $defaultOptions);
```
Jika argument ketiga diisi integer timeout, Laravel akan menghentikan eksekusi push dengan warning/error di background tanpa sinyal ke klien.

**Cara mendeteksi signature yang benar tanpa menebak** — refleksi langsung ke library:
```bash
php -r 'require "vendor/autoload.php";
$ref = new ReflectionMethod(\Minishlink\WebPush\WebPush::class, "__construct");
foreach ($ref->getParameters() as $p) {
    echo $p->getName() . ": " . ($p->hasType() ? $p->getType() : "none") . "\n";
}'
```

**Gejala khas**: push "gagal senyap". Controller dibungkus `try/catch` sehingga user melihat "berhasil dikirim", tetapi `storage/logs/laravel.log` berisi warning. **Selalu `grep -iE "push" storage/logs/laravel.log` saat ada laporan notifikasi tidak masuk** — jangan percaya pesan sukses di UI.

## 2. In-App Notification vs Web Push (OS-level)
- **In-App Badges & Dropdown**:
  - Dikelola via polling ringan atau SSE / Fetch JSON baca-saja.
  - Status "sudah dibuka" dapat disimpan di `localStorage` klien untuk menghindari penulisan massal ke database, asalkan tidak melanggar konsistensi antar-perangkat.
  - Bekerja 100% di semua browser saat aplikasi terbuka.
- **OS-Level Web Push**:
  - Wajib memiliki tabel database penyimpan langganan (`push_subscriptions`: `user_id`, `endpoint`, `p256dh`, `auth`).
  - Memerlukan pasang kunci VAPID (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`).
  - Handler di `sw.js` via event `push`, `notificationclick`, dan `pushsubscriptionchange`.

## 3. PWA Badging API vs Android Launcher Behavior
- **`navigator.setAppBadge()`**:
  - Hanya didukung di desktop Chrome/Edge dan browser tertentu. Di Chrome Android, Badging API tidak didukung secara penuh untuk standalone shortcut.
- **PWA Shortcut vs Browser Host di Android**:
  - PWA yang diinstal melalui browser Chrome berjalan di bawah container package Chrome (`com.android.chrome`).
  - Notifikasi push sistem dikirim melalui Google Play Services (FCM) dan diterima oleh induknya (`Chrome`).
  - Launcher Android (misalnya MIUI/HyperOS, OneUI) akan menempelkan badge/lencana angka merah pada **ikon induk (Chrome di dock)**, bukan pada ikon shortcut PWA di layar utama.
- **Solusi untuk Badge Murni pada Ikon Aplikasi**:
  - Bungkus PWA menjadi **TWA (Trusted Web Activity)** atau **Capacitor** menjadi `.apk` mandiri yang memiliki `applicationId` Android tersendiri.

### 3a. Batas Kejujuran yang Wajib Disampaikan ke User soal TWA
Saat user meminta notifikasi "mandiri, tidak menginduk ke browser", **jangan menjanjikan lebih dari yang bisa diberikan TWA**. Sampaikan terus terang:
- TWA **tidak** menghilangkan ketergantungan pada Chrome. Isinya tetap mesin Chrome; Chrome wajib terpasang.
- Yang **berubah**: identitas aplikasi jadi package sendiri, sehingga notifikasi/lencana *seharusnya* menempel di ikon app.
- Yang **tidak berubah**: penampilan lencana angka tetap bergantung kebijakan launcher HP.
- Kemandirian penuh dari Chrome butuh native/Capacitor + FCM native — proyek terpisah yang jauh lebih besar.

Menjanjikan "APK akan menyelesaikan masalah badge" lalu gagal membuat user kehilangan kepercayaan. Lebih baik sebut batasnya di awal.

## 4. Multi-User Device & Push Token Session Cleanup (Logout Pitfall)
- **Masalah Kebocoran Notifikasi Antar-Akun**:
  - Saat User A login di HP dan mengaktifkan Web Push, endpoint/token FCM perangkat tersimpan di database dengan relasi `user_id = A`.
  - Jika User A melakukan Logout tetapi aplikasi hanya memanggil `Auth::logout()` dan `session()->invalidate()`, token push di tabel `push_subscriptions` **tetap aktif dan masih terhubung ke User A**.
  - Jika perangkat tersebut kemudian dipakai login sebagai akun lain, lalu ada yang mengirim pesan ke User A, **notifikasi User A tetap berdering di HP tersebut**, menciptakan ilusi pesan salah sasaran.
- **Solusi Wajib**:
  1. **Backend Logout Cleanup (`AuthenticatedSessionController@destroy`)**:
     ```php
     $user = Auth::user();
     if ($user) {
         PushSubscription::where('user_id', $user->id)->delete();
     }
     Auth::guard('web')->logout();
     ```
  2. **Frontend Unsubscribe Hook**: Pada saat form logout disubmit, panggil `sub.unsubscribe()` pada Service Worker klien.
  3. **Transfer kepemilikan di endpoint subscribe**: endpoint yang sama bisa sebelumnya milik user lain. Hapus kaitan lama sebelum menyimpan:
     ```php
     PushSubscription::where('endpoint', $data['endpoint'])
         ->where('user_id', '!=', $currentUser->id)
         ->delete();
     ```

## 5. AKAR MASALAH TERSERING: Izin `granted` ≠ Punya PushSubscription
Ini penyebab paling sering dari keluhan **"notifikasi tidak masuk sama sekali"**, dan paling sulit dilihat karena semua indikator tampak normal.

**Salah paham yang fatal**: `Notification.permission === 'granted'` **TIDAK** berarti objek `PushSubscription` sudah ada. Keduanya hal berbeda:
- `Notification.permission` = izin OS/browser untuk menampilkan notifikasi.
- `PushSubscription` = objek langganan berisi endpoint FCM, dibuat **hanya** oleh `pushManager.subscribe()`.

Perangkat bisa punya izin `granted` (misal dari sesi lama, atau izin situs diberikan sekali) tetapi **tanpa** objek langganan. Akibatnya token tidak pernah terkirim ke server, server tidak punya alamat tujuan, dan notifikasi tidak pernah tiba — tanpa satu pun pesan galat.

**Bukti empiris (Chrome DevTools Protocol):**
```
Notification.permission : granted
getSubscription() null? : True      <-- tidak ada objek langganan
token terkirim ke server: []        <-- DB kosong
```

**Pola `syncSubscription()` yang SALAH** — hanya mengirim ulang langganan yang sudah ada:
```js
reg.pushManager.getSubscription().then(function (sub) {
    if (sub) { kirimKeServer(...); }
    else     { /* diam — INI BUG-nya */ }
});
```

**Pola BENAR** — buat langganan sendiri kalau izin sudah ada:
```js
function syncSubscription() {
    if (!pushDidukung()) { return; }
    navigator.serviceWorker.ready.then(function (reg) {
        return reg.pushManager.getSubscription().then(function (sub) {
            if (sub) {
                var k = sub.toJSON();
                // kirim ulang agar kepemilikan pindah ke akun yang login sekarang
                return kirimKeServer(URL_SUBSCRIBE, {
                    endpoint: k.endpoint,
                    keys: { p256dh: k.keys.p256dh, auth: k.keys.auth }
                }).then(function () { updateTombolPush(true); });
            }
            // Izin sudah ada tapi belum ada langganan: buat sendiri.
            // Tidak memunculkan dialog izin baru karena izin sudah 'granted'.
            if (Notification.permission === 'granted') { return buatLangganan(); }
            updateTombolPush(false);
        });
    }).catch(function () { /* diam: penanda tak boleh mengganggu halaman */ });
}
```

**Gejala di lapangan (kronologi 2 HP)** yang menunjuk ke bug ini:
- HP A pernah klik tombol "Aktifkan" → punya token → notifikasi masuk.
- HP B izin sudah `granted` tapi tak pernah klik tombol → **tak punya token** → notifikasi tak masuk sama sekali.
- Setelah HP A logout (token terhapus), tabel langganan jadi **kosong** → notifikasi tak masuk ke HP mana pun.

Jangan pernah menggantungkan pendaftaran token pada klik tombol manual. Tombol hanya untuk **meminta izin pertama kali**; pendaftaran harus otomatis tiap halaman dimuat.

## 6. Handler `pushsubscriptionchange` + Endpoint Rotasi yang Aman
Browser/FCM memutar (rotasi) langganan secara berkala. Tanpa handler ini, notifikasi **berhenti mendadak beberapa hari kemudian** tanpa sebab yang terlihat — gejala paling membingungkan karena tak ada perubahan kode.

**Audit cepat di `sw.js`:**
```bash
grep -nE "addEventListener\('(push|notificationclick|pushsubscriptionchange)'" public/sw.js
```
Kalau `pushsubscriptionchange` tidak ada, sistem push Anda punya bom waktu.

**Tantangan khusus**: handler ini berjalan saat **tidak ada halaman terbuka**, jadi **tidak ada token CSRF dan bisa tidak ada sesi login**. Jangan pakai endpoint `subscribe` biasa yang butuh `auth`.

**Pola endpoint rotasi yang mengamankan diri sendiri** — tiga lapis:
```php
public function rotate(Request $request): JsonResponse
{
    $data = $request->validate([
        'endpoint_lama' => ['required', 'string', 'max:500'],
        'endpoint' => ['required', 'url', 'max:500'],
        'keys.p256dh' => ['required', 'string'],
        'keys.auth' => ['required', 'string'],
    ]);

    // Lapis 1: wajib menyertakan endpoint lama yang sudah terdaftar.
    // Nilainya URL acak panjang dari FCM, hanya diketahui perangkat pemilik.
    $lama = PushSubscription::where('endpoint', $data['endpoint_lama'])->first();
    if (! $lama) {
        return response()->json(['ok' => false, 'alasan' => 'langganan lama tidak dikenal'], 404);
    }

    // Lapis 2: kepemilikan diambil dari BARIS LAMA di database,
    // BUKAN dari auth()->id() maupun masukan pemanggil.
    $pemilik = $lama->user_id;

    PushSubscription::where('endpoint', $data['endpoint_lama'])->delete();
    PushSubscription::where('endpoint', $data['endpoint'])->delete();
    PushSubscription::create([
        'user_id' => $pemilik,
        'endpoint' => $data['endpoint'],
        'p256dh' => $data['keys']['p256dh'],
        'auth' => $data['keys']['auth'],
    ]);

    return response()->json(['ok' => true]);
}
```

Rute di luar grup `auth`, + **Lapis 3** throttle:
```php
// routes/web.php
Route::post('/push/rotate', [PushSubscriptionController::class, 'rotate'])
    ->middleware('throttle:20,1')
    ->name('push.rotate');

// VAPID public key BUKAN rahasia (memang disiarkan ke browser) dan harus
// terbaca Service Worker tanpa sesi, jadi keluarkan dari grup `auth`.
Route::get('/push/vapid-key', [PushSubscriptionController::class, 'vapidKey'])
    ->name('push.vapid');
```

Pengecualian CSRF di `bootstrap/app.php` (Laravel 11):
```php
$middleware->validateCsrfTokens(except: ['push/rotate']);
```

**Tes keamanan yang wajib ada** — akun lain yang sudah login mencoba mengklaim token korban:
```php
$this->actingAs($penyerang)->postJson(route('push.rotate'), [
    'endpoint_lama' => $endpointKorban, /* ... */
])->assertOk();
// Token HARUS tetap milik korban karena pemilik diambil dari baris lama
$this->assertDatabaseHas('push_subscriptions', ['endpoint' => $baru, 'user_id' => $korban->id]);
$this->assertDatabaseMissing('push_subscriptions', ['user_id' => $penyerang->id]);
```

Handler di `sw.js`:
```js
self.addEventListener('pushsubscriptionchange', (event) => {
    event.waitUntil((async () => {
        try {
            const lama = event.oldSubscription
                || await self.registration.pushManager.getSubscription();
            const res = await fetch('/push/vapid-key', { credentials: 'same-origin' });
            if (!res.ok) { return; }
            const { key } = await res.json();
            if (!key) { return; }
            const baru = event.newSubscription
                || await self.registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: base64ToUint8Array(key),
                });
            if (!lama) { return; }
            const k = baru.toJSON();
            await fetch('/push/rotate', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    endpoint_lama: lama.endpoint,
                    endpoint: k.endpoint,
                    keys: { p256dh: k.keys.p256dh, auth: k.keys.auth },
                }),
            });
        } catch (e) { /* diam: rotasi gagal tak boleh mematikan SW */ }
    })());
});
```

## 7. `setAppBadge` Tidak Tersedia di Konteks Service Worker
Badging API milik konteks `window`, **bukan** Service Worker. Memanggilnya di `sw.js` adalah kode mati yang tampak benar:
```js
// SALAH — di dalam sw.js, navigator.setAppBadge tidak tersedia.
// Juga dipanggil tanpa argumen sehingga tak ada angka.
if (navigator.setAppBadge) { return navigator.setAppBadge().catch(() => {}); }
```

**Pola benar** — SW memberi tahu halaman, halaman yang mengatur lencana:
```js
// sw.js, di dalam handler 'push' setelah showNotification()
return self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    .then((list) => { list.forEach((c) => c.postMessage({ jenis: 'notifikasi-baru' })); })
    .catch(() => {});
```
```js
// notifikasi.js (konteks halaman) — pakai angka NYATA, bukan panggilan kosong
var total = baruPesan + baruAgenda.length + baruSapaan.length;
if (navigator.setAppBadge) {
    (total > 0 ? navigator.setAppBadge(total) : navigator.clearAppBadge()).catch(function () {});
}
```
Ingat: lencana yang benar-benar muncul di ikon HP Android berasal dari **notifikasi sistem**, bukan dari Badging API.

## 8. Pitfall Cakupan Layout: Sistem Notifikasi Hanya Terpasang di Sebagian Layout
Proyek dengan beberapa layout Blade (misal `layouts/user-app.blade.php` untuk user dan `layouts/super-admin.blade.php` untuk admin) mudah memasang skrip notifikasi **hanya di satu layout**.

Akibatnya pada layout yang terlewat: token tak pernah diselaraskan, dan **token tak dicabut saat logout** sehingga notifikasi bocor antar-akun.

**Audit cakupan:**
```bash
grep -rln "notifikasi.js" resources/views/      # layout mana yang memuat skrip
grep -rln "csrf-token"    resources/views/layouts/
grep -rl  "layouts.super-admin" resources/views/ | wc -l   # berapa view terdampak
```

**Versi minimal untuk layout admin** (hormati permintaan user "jangan tambah fitur/tampilan"): pasang `<meta name="csrf-token">` + `<script src=".../notifikasi.js" ...>` **tanpa** elemen lonceng. Skrip tetap menyelaraskan & mencabut token, tetapi tampilan panel admin tidak berubah sama sekali.

Kunci tes agar regresi tampilan tertangkap:
```php
$this->assertStringContainsString('/js/notifikasi.js', $html);
$this->assertStringContainsString('csrf-token', $html);
// Tampilan panel admin TIDAK boleh berubah
$this->assertStringNotContainsString('id="notifBell"', $html);
$this->assertStringNotContainsString('id="notifPanel"', $html);
```

Catatan: `meta csrf-token` sering belum ada di layout lama yang hanya memakai form Blade biasa. Tanpa meta ini, semua `fetch` POST dari JS akan kena 419.

## 9. Checklist Audit Sistem Notifikasi PWA
Jalankan berurutan saat user melaporkan "notifikasi masih banyak error":

1. **Token di DB** — siapa saja yang terdaftar, apakah endpoint dobel:
   ```sql
   SELECT s.id, s.user_id, u.username, u.role, substr(s.endpoint,1,45), s.created_at
   FROM push_subscriptions s LEFT JOIN users u ON s.user_id = u.id;
   ```
2. **Log galat push** — `grep -iE "push" storage/logs/laravel.log | tail -20`
3. **Versi live vs lokal** — `curl -s https://domain/sw.js | grep -E "^const CACHE_VERSION"` dibanding file lokal. Beda = HP user masih memakai berkas lama.
4. **Handler SW lengkap** — `push`, `notificationclick`, `pushsubscriptionchange` (lihat §6).
5. **Cakupan layout** — lihat §8.
6. **Manifest** — `id`, `scope`, `start_url`, `display: standalone` ada.
7. **assetlinks.json** (bila TWA) — `curl -s -o /dev/null -w "%{http_code}" https://domain/.well-known/assetlinks.json` harus 200.
8. **Header `sw.js`** — wajib `no-cache, no-store`; kalau kena `max-age` panjang, SW user tak akan pernah ter-update.
9. **Rute terlindungi** — `curl` ke `/super-admin` tanpa login harus 302, bukan 200.
10. **Uji kirim nyata** ke token yang benar-benar ada di DB, dan laporkan jumlah terkirim.

## 10. Pola Verifikasi Empiris via Chrome DevTools Protocol
Audit notifikasi **tidak boleh** berhenti di pembacaan kode. Banyak cacat (seperti §5) hanya terlihat saat dijalankan.

Pola yang terbukti: jalankan server uji di port terpisah dengan **salinan** database, lalu kendalikan Chrome headless lewat CDP.

```python
# SALINAN DB — jangan pernah menguji di DB produksi
shutil.copy(f'{APP}/database/database.sqlite', TMP)
env = dict(os.environ, DB_DATABASE=TMP, APP_URL=BASE,
           SESSION_SECURE_COOKIE='false', APP_ENV='local', SESSION_DRIVER='file')
subprocess.Popen(['php', 'artisan', 'serve', '--host=127.0.0.1',
                  f'--port={PORT}', '--no-reload'], cwd=APP, env=env)
```

Beri izin notifikasi tanpa dialog:
```python
cmd('Browser.grantPermissions', origin=BASE, permissions=['notifications'])
```

Periksa keadaan nyata langganan dari dalam halaman:
```python
js("navigator.serviceWorker.ready.then(r=>r.pushManager.getSubscription()).then(s=>!!s)")
js("Notification.permission")
```

### Pitfall harness uji (semua pernah menghasilkan hasil palsu)
- **`php -S` + `server.php` gagal diam** → judul halaman jadi `127.0.0.1` dan semua penanda kosong. Pakai `php artisan serve --no-reload`.
- **`APP_URL` produksi `https://`** memicu `URL::forceScheme('https')` di `AppServiceProvider`, sehingga `/` me-redirect ke HTTPS dan uji HTTP lokal gagal (`SSL: UNEXPECTED_EOF_WHILE_READING`). Timpa `APP_URL=http://127.0.0.1:<port>` di env uji — **jangan** ubah kode aplikasi.
- **`SESSION_SECURE_COOKIE`** harus `false` untuk uji HTTP, kalau tidak cookie sesi tak tersimpan dan login selalu gagal.
- **Akun uji ter-soft-delete** → login gagal tanpa pesan jelas. Selalu sertakan `AND deleted_at IS NULL` saat memilih akun uji.
- **Form logout tidak ada di semua halaman.** Terbukti hanya ada di `/profil` untuk bruder; `/dashboard`, `/agenda`, `/sapaan-provinsial` tidak punya. Uji logout yang menembak halaman salah akan "lulus" secara palsu. Verifikasi dulu: `js("!!document.querySelector('form[action*=\"/logout\"]')")`.

**Prinsip**: kalau hasil uji tampak terlalu rapi (semua nol, semua kosong), curigai harness-nya dulu sebelum menyimpulkan tentang aplikasi. Hasil kosong pada uji pertama sesi ini ternyata cacat harness, bukan temuan.
