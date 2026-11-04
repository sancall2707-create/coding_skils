# Pitfall Sesi: 419 Login, Urutan Agenda, Restyle Elegan, Harness Terminal

## 1. 419 Page Expired di halaman login (PWA di HP)
- Penyebab: token CSRF di HTML login basi (halaman dipulihkan dari cache/bfcache atau dibiarkan lama) + `SESSION_LIFETIME=120`. `trustProxies` sudah benar; jangan berhenti di situ.
- Perbaikan berlapis: (1) `AuthenticatedSessionController::create()` mengembalikan `response()->view('auth.login')` dengan header `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` + `Pragma: no-cache`; (2) JS login: `pageshow` + `event.persisted` => reload, `visibilitychange` tersembunyi >10 menit => reload; (3) handler ramah di `bootstrap/app.php`; (4) `SESSION_LIFETIME=720` di `.env` (cadangkan `.env` dulu, chmod 600, `config:clear`); (5) `sw.js` tidak `cache.put` respons `redirected` atau URL akhir `/login`.
- PITFALL KRUSIAL: `$exceptions->render(fn (TokenMismatchException $e) ...)` TIDAK PERNAH terpanggil. `Handler::prepareException()` mengubahnya menjadi `Symfony\Component\HttpKernel\Exception\HttpException(419)` lebih dulu. Tangkap `HttpException` lalu cek `getStatusCode() === 419`, hanya untuk tamu (`! auth()->check()`) dan bukan JSON; redirect ke `route('login')` + `withInput($request->only('username','remember'))` + `withErrors(['username' => 'Halaman login kedaluwarsa. ...'])`.
- Tes: header `no-store`; rute uji `Route::middleware('web')->post('/_uji-419', fn() => throw new TokenMismatchException)` => `assertRedirect(route('login'))` + `assertSessionHasErrors('username')`; login normal tetap berhasil.
- Verifikasi domain publik: skrip Python `urllib` + `CookieJar` (token `TOKEN_BASI` vs token hasil scrape `name="_token"`); jangan `curl -L -X POST`.

## 2. Urutan agenda "terdekat dulu"
- Di `AgendaController::index()` saja (jangan ubah `PersonalScheduleQuery::forUser()`, dipakai kalender/beranda): mendatang (`starts_at >= now()`) `sortBy` naik, lalu `concat` yang sudah lewat `sortByDesc`, `->values()`.
- Kolom model `PersonalAgenda` = `start_at`; objek item dari query = `starts_at`. Tes: `travelTo()` + data diacak + `assertSeeInOrder`.

## 3. Restyle elegan tanpa ubah fitur
- Alur lengkap: `visual-qa-pwa/references/elegant-restyle-css-layer-workflow.md`.
- Tautan `Teks →` diminta jadi tombol: pil `inline-flex` + ikon SVG, tanpa panah, di semua beranda (Super Admin dan Admin); tes `assertDontSee('Teks →', false)`.

## 4. Harness terminal
- Heredoc dengan karakter `&` (teks CSS/HTML) ditolak sebagai "backgrounding" dan tidak menulis apa pun. Tulis dengan `write_file` ke `/tmp/...` lalu `cat /tmp/x >> target`; cek `grep -c <penanda>` agar tidak menempel dua kali.
- Rangkaian curl `-L -X POST` + banyak grep sekaligus bisa diblokir parser; pakai satu skrip Python kecil.
