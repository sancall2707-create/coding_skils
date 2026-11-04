# PWA Web Push & Notification Badges (Laravel + Service Worker)

Catatan implementasi dan pitfall nyata dari penambahan Web Push (notifikasi Android di luar PWA) dan lencana lonceng di dalam PWA.

---

## 1. Web Push vs App Badging API

### Masalah
- Pengguna meminta: *"Notifikasi / angka belum dibuka muncul di ikon aplikasi di beranda HP"*.
- `navigator.setAppBadge()` (Badging API) **TIDAK DIDUKUNG** oleh Chrome Android maupun Samsung Internet (hanya Windows/macOS Chrome, Edge, Safari iOS 16.4+).
- Di Android, angka/titik di ikon aplikasi di beranda HP **hanya muncul jika ada notifikasi sistem (Web Push)** yang dikirim melalui Service Worker (`showNotification`).

### Solusi Berlapis
1. **Di dalam PWA**:
   - Ikon lonceng di header dengan angka badge total notifikasi belum dibuka.
   - Panel drop-down berisi daftar ringkas yang bisa langsung diklik.
   - Badge angka pada tab Profil (pesan masuk), kartu Agenda, dan kartu Sapaan.
2. **Di luar PWA (Homescreen HP)**:
   - Web Push via Google FCM / VAPID.
   - Saat ada push masuk, SW memicu `showNotification` yang menghasilkan notifikasi push di status bar Android dan titik/badge di ikon launcher HP.

---

## 2. Pitfall minishlink/web-push v11 Konstruktor

### Gejala
Push subscription tersimpan di DB, izin browser `granted`, tetapi HP tidak pernah menerima notifikasi. Log Laravel mencatat:
```
local.WARNING: Push gagal: Minishlink\WebPush\WebPush::__construct(): Argument #3 ($client) must be of type ?Psr\Http\Client\ClientInterface, int given
```

### Penyebab
Dokumentasi lama atau library versi 7/8/9 sering mencontohkan konstruktor:
```php
// SALAH (pola v8/v9 yang rusak di v11)
new WebPush($auth, $defaultOptions, 30, ['verify' => true]);
```
Di `minishlink/web-push` **v11**:
- Parameter #1: `array $auth` (berisi key VAPID)
- Parameter #2: `array $defaultOptions` (opsi TTL, urgency, dll.)
- Parameter #3: `?Psr\Http\Client\ClientInterface $client` (bukan integer timeout!)
- Parameter #4+: PSR request/stream factories.

### Pola Benar (v11)
```php
use Minishlink\WebPush\WebPush;

$auth = [
    'VAPID' => [
        'subject' => config('app.url'),
        'publicKey' => config('services.vapid.public_key'),
        'privateKey' => config('services.vapid.private_key'),
    ],
];

// Opsi default seperti TTL (dalam detik) ditaruh di parameter #2
$webPush = new WebPush($auth, ['TTL' => 86400]);
```

---

## 3. Menghasilkan Kunci VAPID via PHP CLI

Tidak perlu menginstal `web-push-libs` global / node global. Gunakan bawaan pustaka:
```bash
php -r '
require "vendor/autoload.php";
$keys = Minishlink\WebPush\VAPID::createVapidKeys();
echo "VAPID_PUBLIC_KEY=" . $keys["publicKey"] . PHP_EOL;
echo "VAPID_PRIVATE_KEY=" . $keys["privateKey"] . PHP_EOL;
'
```
Simpan di `.env` dan daftarkan di `config/services.php`:
```php
'vapid' => [
    'public_key' => env('VAPID_PUBLIC_KEY'),
    'private_key' => env('VAPID_PRIVATE_KEY'),
],
```

---

## 4. Skema Database `push_subscriptions`

Simpan token perangkat pengguna:
```php
Schema::create('push_subscriptions', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->text('endpoint')->unique();
    $table->string('p256dh');
    $table->string('auth');
    $table->timestamps();
});
```
- Gunakan `updateOrCreate(['endpoint' => $endpoint], [...])` pada controller subscribe agar pendaftaran berulang dari browser yang sama tidak memicu error duplicate entry.
- Saat pengiriman gagal (`$report->isSuccess() === false`), periksa apakah langganan expired (HTTP 410 Gone / 404 Not Found), lalu hapus dari DB:
```php
if (!$report->isSuccess()) {
    $endpoint = $report->getRequest()->getUri()->__toString();
    PushSubscription::where('endpoint', $endpoint)->delete();
}
```

---

## 5. Service Worker Push Handler

Di `public/sw.js`:
```javascript
self.addEventListener('push', (event) => {
    let data = { title: 'PWA Title', body: 'Ada notifikasi baru', url: '/', icon: '/images/icon.png' };
    try { data = Object.assign(data, event.data.json()); } catch (e) {}

    event.waitUntil(
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: data.icon,
            badge: '/images/icons/badge-72.png',
            tag: data.tag || 'default-tag',
            renotify: true,
            data: { url: data.url },
        })
    );
});

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

---

## 6. Penanda Belum Dibaca Tanpa Menulis Database

Untuk entitas yang belum memiliki kolom `read_at` (misalnya agenda mendatang atau sapaan umum), jangan mengubah struktur tabel yang sudah ada jika ada batasan ketat:
1. Endpoint backend `/notifikasi/ringkasan` bersifat **baca-saja**:
   - Mengembalikan daftar ID + timestamp entri aktif.
   - Header `Cache-Control: no-store, no-cache, must-revalidate`.
2. Di browser / HP:
   - Simpan ID yang sudah pernah dibuka di `localStorage.getItem('fic_dibuka_' + uid)`.
   - Saat pengguna mengunjungi halaman `/agenda`, simpan semua ID agenda ke `localStorage`.
   - Angka badge adalah selisih antara ID dari server yang belum ada di `localStorage`.
   - Entri yang lebih tua dari 3 hari otomatis dianggap sudah dilihat pada pemakaian pertama agar tidak membanjiri angka badge.

---

## 7. Pembersihan Token Push saat Logout (Cegah Notifikasi Nyasar Lintas Akun)

### Masalah
Saat pengguna logout (misal dari akun Bruder) lalu login sebagai Admin atau orang lain di perangkat yang sama:
- Token Web Push di tabel `push_subscriptions` masih mengaitkan perangkat tersebut dengan `user_id` lama.
- Ketika Admin mengirim pesan ke akun Bruder yang lama tadi, notifikasi push tetap terkirim ke perangkat tersebut! Pengguna merasa *"sudah logout kenapa masih terima notifikasi akun lama?"*.

### Solusi Ganda (Server + Klien)
1. **Di Server (`AuthenticatedSessionController@destroy`)**:
   Hapus entri langganan push milik user yang sedang logout:
   ```php
   public function destroy(Request $request): RedirectResponse
   {
       $user = Auth::user();
       if ($user) {
           PushSubscription::where('user_id', $user->id)->delete();
       }

       Auth::guard('web')->logout();
       $request->session()->invalidate();
       $request->session()->regenerateToken();

       return redirect()->route('login');
   }
   ```
2. **Di Browser Klien (`notifikasi.js`)**:
   Dengarkan pengiriman form logout dan panggil `pushManager.getSubscription().then(sub => sub.unsubscribe())` agar registrasi push lokal di browser juga di-reset.

