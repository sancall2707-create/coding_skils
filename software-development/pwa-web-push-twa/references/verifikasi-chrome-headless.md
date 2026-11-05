# Uji nyata di Chrome headless (salinan DB)

Browser tool tidak bisa membuka HTTP lokal, jadi pakai Chrome sendiri + CDP.

Kerangka (python3, paket `websocket-client`):
1. `shutil.copy(database.sqlite, /tmp/x.sqlite)`; env `DB_DATABASE=/tmp/x.sqlite APP_URL=http://127.0.0.1:PORT SESSION_SECURE_COOKIE=false SESSION_DRIVER=file`.
2. `php artisan serve --host=127.0.0.1 --port=PORT --no-reload` (port bebas, mis. 181xx).
3. Atur sandi uji akun via `php artisan tinker --execute='User::where("id",N)->update(["password"=>Hash::make("ujiuji123")]);'` (pada salinan, bukan DB asli).
4. `google-chrome-stable --headless=new --no-sandbox --disable-gpu --remote-debugging-port=194xx --user-data-dir=/tmp/... about:blank`; ambil `webSocketDebuggerUrl` dari `/json`.
5. Fungsi `cmd(method, **params)` kirim JSON, tunggu id sama; `js(expr)` = `Runtime.evaluate` returnByValue awaitPromise.
6. Login: isi form via JS lalu `form.submit()`; `Page.navigate` untuk halaman lain.
7. Cek: elemen ada, nilai DOM, isi tabel `push_subscriptions` pada salinan.
8. `finally`: terminate Chrome dan server.

Pitfall:
- Nama dummy di uji pencarian harus diambil dari DB nyata (mis. "saptono"), bukan nama tebakan.
- Skrip yang terputus: cek `git status` dan proses sisa dulu, baru ulang.
- Uji kirim nyata ke FCM boleh pada DB produksi hanya baca token dan kirim 1 pesan; jangan ubah data.
- Halaman PWABuilder memakai shadow DOM: telusuri rekursif `el.shadowRoot` lewat `browser_console` untuk membaca label opsi.
