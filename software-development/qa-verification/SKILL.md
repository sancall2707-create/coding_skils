---
name: qa-verification
description: Skill untuk verifikasi mutu, pengujian ulang hasil pekerjaan coding maupun rekap penilaian secara independen berdasarkan bukti aktual.
---

# Skill: QA Verification

Skill ini digunakan untuk melakukan verifikasi kualitas (Quality Assurance) setelah pekerjaan `coding-agent` atau `rekap-penilaian` selesai dikerjakan.

## Aturan Utama
- **Tidak Percaya Laporan Tanpa Bukti**: QA tidak boleh hanya mengandalkan rangkuman subagent/agent sebelumnya. QA wajib memeriksa bukti aktual (file, diff, hasil tes, re-kalkulasi).

## Verifikasi Pekerjaan Coding
1. **Audit Diff**: Periksa `git diff` untuk memastikan tidak ada perubahan liar atau penambahan file tak relevan.
2. **Uji Build & Test**: Jalankan perintah build, unit test, dan linter proyek secara mandiri.
3. **Uji Fitur Utama**: Verifikasi bahwa fungsi yang diminta pengguna berjalan sesuai ekspektasi.
4. **Cek Regresi & Error**: Bedakan antara error pra-eksistensi (error lama) dengan error baru akibat perubahan kode.
5. **Proteksi Kode**: QA dilarang mengubah kode sumber kecuali ada instruksi eksplisit dari Agent Utama.

## Verifikasi Pekerjaan Rekap Penilaian
1. **Hitung Ulang Sampel**: Lakukan pengujian ulang secara acak pada sampel baris data.
2. **Audit Rumus & Kolom**: Periksa kebenaran rumus, total baris, penanganan pembulatan, serta nilai min/max.
3. **Validasi Data**: Pastikan tidak ada cell kosong yang terlewat, data duplikat, atau konversi yang keliru.
4. **Verifikasi File Asli**: Pastikan file data sumber tidak termodifikasi atau terhapus.
5. **Kesesuaian Aturan**: Pastikan kriteria KKM/ketuntasan diterapkan sesuai instruksi.
