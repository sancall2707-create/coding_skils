# Agenda Provinsi: pola, edit/hapus, dan jebakan uji

Proyek: PWA Bruder FIC (`/home/ubuntu/PWA_Bruder-Muda`).

## Model data
- `personal_agendas.is_provincial` (bool) + `broadcast_key` (md5 `judul|Y-m-d H:i:s|lokasi`), migrasi aditif + backfill agenda siaran lama (kelompok judul+waktu+lokasi dengan jumlah salinan >= jumlah akun user aktif).
- Siaran dari Monitoring (`agendaStore`) menyalin agenda ke tiap akun `role=user` aktif dengan `is_provincial=true` dan `broadcast_key` sama.
- Agenda "lainnya" yang ditulis role `admin`/`super_admin` lewat `AgendaController@store` otomatis `is_provincial=true`.

## Tampilan
- Beranda Admin/Super Admin: `PersonalAgenda::upcomingForOverview($now, 5)` menggabungkan per `broadcast_key` jadi satu kartu, label "Agenda Provinsi", warna navy `#0E3366`, nama penulis **TPPBM** (user menolak "Seluruh Bruder Muda"). Agenda pribadi tetap per bruder (label emas `#B57900`).
- Tab Agenda Monitoring: `MonitoringQuery::collapseProvincial()` untuk daftar/kalender; teks "Diterima N akun bruder". Ekspor Excel/PDF tetap per baris.
- Hanya method `admin()` dan `superAdmin()` di `DashboardController` yang berubah; `user()` (beranda bruder) tidak.

## Edit / hapus
- Rute (grup `role:admin,super_admin`): `GET/PUT/DELETE /super-admin/monitoring/agenda/provinsi/{key}`, `->where('key','[a-f0-9]{32}')`, nama `superadmin.monitoring.agenda.{edit,update,destroy}`.
- Update: validasi sama dengan tambah, perbarui semua salinan, hitung ulang `broadcast_key`. Hapus: soft delete semua salinan + `confirm()` menyebut jumlah akun.
- Form `agenda-create.blade.php` dipakai ulang (`$editing = isset($agenda)`, `@method('PUT')`).

## Jebakan uji
- `substr_count($html,'Judul')` salah hitung karena flash sukses dari POST di tes yang sama; hitung pada penanda kartu.
- Tes loop role: bersihkan `User::query()->delete()` dan `forceDelete()` agenda antar iterasi.
- Form: judul ada di `value="..."`; pakai `assertSee('value="X"', false)`.
- Chrome CDP: `getAttribute('href')` sudah absolut (`go(href)`), akses lewat `getElementById`, verifikasi lewat query DB salinan.
- DB asli bertambah baris tak terduga: cek `created_at`; bisa siaran baru dari user (agenda "Test").
- Terminal menolak perintah foreground berisi `&` (mis. "Hari &amp;" dalam heredoc): tulis skrip ke `/tmp/*.py` lewat write_file lalu jalankan.
