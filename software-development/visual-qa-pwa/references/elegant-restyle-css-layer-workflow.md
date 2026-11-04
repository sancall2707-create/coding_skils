# Perapian Tampilan "Elegan, Tidak Kaku" Tanpa Ubah Fitur (CSS Layer + Tangkapan Layar)

Dipakai saat user minta: "rapikan tampilan agar elegan/profesional, jangan ubah fitur/struktur/database".

## Aturan lingkup (wajib)
- Hanya sentuh gaya: `public/css/*.css`, blok `<style>` di Blade, penanda versi. JANGAN sentuh `app/`, `routes/`, `config/`, `database/`.
- Bukti sebelum commit: `git diff --stat -- app routes database config` harus kosong; hitung baris tabel inti sebelum/sesudah; `PRAGMA integrity_check` = ok; seluruh tes lulus.
- Cadangkan CSS + layout dulu ke `/home/ubuntu/backups/css/<nama>.sebelum-<tema>.<timestamp>`.

## Pola: satu lapisan di AKHIR berkas CSS
Tambahkan blok `TAMPILAN ELEGAN vN` di ujung CSS (bukan edit tersebar) agar mudah dicabut. Isi yang terbukti berguna:
- Token: `--fic-ink`, `--fic-line`, bayangan berlapis `0 1px 2px ..., 0 8px 20px -8px ...`, `--fic-ease: cubic-bezier(.2,.7,.2,1)`.
- Kepala halaman: gradasi 3 titik, `border-radius` bawah 26px, padding bawah lebih besar.
- Kartu: latar hampir solid (`rgba(255,255,255,.9)`) bukan kaca transparan; border `#DCE6F6`.
- Tab aktif bottom-nav: pil latar `#E4EDFF` pada SVG (`box-sizing:content-box; padding:4px 16px`).
- Kartu statistik menumpuk: `@media screen { .sa-body > .progress-stat-card:first-child { margin-top:-34px; position:relative; z-index:2 } }` (padding atas `.sa-body` = 20px, jadi tumpang 14px; -22px terlalu tipis, kartu tampak menempel).
- Animasi masuk hanya dalam `@media screen and (prefers-reduced-motion: no-preference)`.
- Untuk gaya inline lama gunakan selektor atribut + `!important`: `[style*="color: #98A2B3"]`, `.sa-body [style*="box-shadow: 0 2px 4px rgba(16,24,40,0.02)"]`.
- Tombol aksi destruktif: tonal (`#FEF3F2` + border `#FECDCA`), bukan merah solid; tombol sekunder bergaris tepi; tinggi sentuh 40px.

## Pitfall
- Definisi kelas ganda di `<style>` Blade (mis. `.btn` ditulis dua kali): yang di bawah menang. Hapus duplikat lama, jangan hanya menambah yang baru.
- `patch` yang mengganti blok berkomentar bisa menelan komentar penanda; baca ulang diff.
- Setiap perubahan CSS: seragamkan `?v=<versi>` di SEMUA `<link rel=stylesheet>` (cek `grep -rn 'fic-pwa.css' resources/views`, termasuk halaman mandiri tanpa layout), `PRECACHE_URLS` di `sw.js`, dan naikkan `CACHE_VERSION`. Halaman mandiri yang memuat CSS tanpa `?v=` bisa menahan gaya lama (Caddy memberi `immutable` 1 tahun).
- Kurung CSS: cek `css.count("{") == css.count("}")` setelah tambah blok.

## Alur tangkapan layar offline (tanpa login web, tanpa tulis DB)
1. Skrip PHP: `auth()->login(User::find($id))`, `Request::create($path)`, `$req->setLaravelSession($app['session']->driver())`, `Http\Kernel::handle()`, simpan HTML dengan `<base href="http://127.0.0.1:8022/">` disisipkan setelah `<head>`.
2. `google-chrome-stable --headless=new --no-sandbox --window-size=430,1500 --virtual-time-budget=4000 --screenshot=out.png file:///tmp/x.html`.
3. Ambil set "sebelum" dan "sesudah" (beranda admin, beranda user, daftar bruder, agenda, monitoring); nilai dengan `vision_analyze` minta daftar cacat konkret. Ulangi 2-3 putaran sampai cacat berat habis.
4. Artefak render offline: gambar `/profil/foto` & foto sapaan tampil rusak di tangkapan karena rute berotentikasi tidak dimuat dari `file://`. Verifikasi terpisah lewat kernel: rute itu 200 `image/jpeg` saat login, 302 tanpa sesi. Jangan "memperbaiki" ini di CSS.

## Hal di luar lingkup yang sebaiknya DILAPORKAN, bukan diubah
Inisial avatar memakai gelar "Br." (jadi "BA" semua), jumlah tombol aksi per kartu, penyebut target tahunan vs label bulan, urutan pengingat per jam, ejaan data. Sebutkan di akhir, tanya user.

## Tombol dari tautan teks bertanda panah
Permintaan "beri card agar jelas itu tombol dan hapus tanda panah": ganti `Teks →` dengan pil `inline-flex` (latar `#EFF4FF`, border `#B2CCFF`, radius 999px) + ikon SVG kalender + `<span>Teks</span>`; terapkan ke SEMUA beranda yang memuat tautan sama (Super Admin dan Admin), tes `assertDontSee('Teks →', false)`. Tautan lain ber-panah jangan diubah tanpa diminta.
