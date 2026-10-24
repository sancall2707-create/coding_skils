# Patterns & Pitfalls: Form Input, Bulk Delete & Testing pada Laravel PWA

Dokumen ini mencatat pola dan jebakan teknis nyata yang diverifikasi dalam proyek Laravel PWA:

## 1. Input Form: Jangan Beri Default Value Teks Contoh (Gunakan Placeholder Murni)
- **Problem:** Mengisi atribut `value="{{ old('field_name', 'Contoh Nama, FIC') }}"` membuat input otomatis terisi teks contoh. Ketika pengguna mengklik atau submit form, teks contoh dianggap data riil dan harus dihapus manual.
- **Pola yang benar:**
  ```blade
  <input
      type="text"
      id="mentor_name"
      name="mentor_name"
      value="{{ old('mentor_name', $editing ? $schedule->mentor_name : '') }}"
      placeholder="Contoh: Br. Yohanes Subagio, FIC"
      required
  >
  ```
- **Prinsip:** Kolom pembuatan data baru (`create`) wajib diawali dengan nilai kosong bersih. Teks contoh hanya ditaruh di atribut `placeholder`.

---

## 2. Fitur Pilih Semua (Select All), Hapus Massal (Bulk Delete) & Keamanan Berlapis
- **Pola UI (Mobile-First):**
  - Checkbox "Pilih Semua" ditaruh di toolbar atas yang informatif.
  - Tombol aksi massal berstatus `disabled` (opacity rendah) secara default dan dinamis berubah teksnya saat item diceklis (`Hapus 3 Terpilih`).
  - Modal konfirmasi interaktif muncul sebelum aksi destruktif dilakukan dengan teks peringatan tegas: *"Data yang dihapus tidak dapat dipulihkan"*.
- **Pola Controller & Keamanan Mutlak Data:**
  - **Larangan Keras:** Jangan pernah menjalankan `Model::whereIn('id', $ids)->delete()` tanpa scoping kepemilikan data!
  - **Sisi User biasa:** Batasi ketat dengan `where('user_id', auth()->id())` agar tidak dapat menghapus data pengguna lain via manipulasi ID request.
  - **Sisi Super Admin:** Batasi hanya boleh menghapus record yang berelasi dengan pengguna target (misal `whereHas('user', fn($q) => $q->where('role', 'user'))`), bukan data master/admin lain.
  ```php
  $ids = array_map('intval', $request->input('ids', []));
  $deleted = SelfDevelopmentJournal::whereIn('id', $ids)
      ->where('user_id', auth()->id())
      ->delete();
  ```

---

## 3. Pitfall Testing Laravel: Model dengan Trait SoftDeletes
- **Problem:** Dalam pengujian (`TestCase` / `RefreshDatabase`), assertion `$this->assertDatabaseMissing('table', ['id' => $id])` akan **FAIL** jika model menggunakan `use SoftDeletes;`. Eloquent soft-delete tetap menyimpan baris di database dan hanya mengisi kolom `deleted_at`.
- **Pola yang benar:**
  ```php
  // Gunakan assertSoftDeleted untuk model ber-SoftDeletes:
  $this->assertSoftDeleted('self_development_journals', ['id' => $j1->id]);

  // Untuk memastikan record orang lain tidak tersentuh sama sekali:
  $this->assertDatabaseHas('self_development_journals', [
      'id' => $jOther->id,
      'deleted_at' => null,
  ]);
  ```

---

## 4. Cache-Busting Avatar & Header No-Cache pada PWA
- **Problem:** Setelah upload foto profil baru, foto profil di beberapa tempat (misal navbar / header / beranda) masih menampilkan avatar lama karena browser / Service Worker meng-cache respon gambar statis.
- **Solusi:**
  1. Tambahkan parameter versi berbasis hash md5 atau timestamp pada URL: `route('profil.foto', ['v' => substr(md5($user->profile_photo), 0, 8)])`.
  2. Sajikan stream respon foto dengan header revalidasi:
     ```php
     'Cache-Control' => 'private, no-cache, must-revalidate',
     'ETag' => '"' . md5($path . $lastModified) . '"',
     ```
  3. Kecualikan rute `/foto` atau `/profil/foto` dari cache runtime Service Worker di `sw.js`.
