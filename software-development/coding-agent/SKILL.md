---
name: coding-agent
description: Skill untuk pengembangan aplikasi web/PWA, audit source code, refactoring, pengujian, dan perbaikan bug dengan prosedur kerja aman dan terstruktur.
---

# Skill: Coding Agent

Skill ini digunakan untuk tugas pemrograman, audit, pengujian, refactoring, dan perbaikan bug pada proyek perangkat lunak.

## Ruang Lingkup
- Pembangunan aplikasi web & PWA
- Audit source code
- Implementasi fitur baru
- Perbaikan bug & refactoring
- Pengujian & pembuatan dokumentasi teknis

## Prosedur Wajib (Mandatory Steps)
1. **Deteksi Proyek**: Tentukan lokasi proyek (path absolut), stack, framework, package manager, dan struktur direktori.
2. **Baca Aturan Proyek**: Periksa file `AGENTS.md`, `HERMES.md`, `.cursorrules`, `README.md`, atau konfigurasi CI/CD.
3. **Cek Status Git**: Pastikan repository bersih atau catat perubahan yang sudah ada sebelum mulai (`git status`).
4. **Perencanaan**: Buat rencana perubahan terstruktur dan tentukan daftar file spesifik yang boleh diubah.
5. **Isolasi Perubahan**: Jangan mengubah file di luar ruang lingkup tugas.
6. **Eksekusi Pengujian**: Jalankan build, test, dan linter yang tersedia dalam proyek untuk memastikan keutuhan sistem.
7. **Verifikasi Perubahan**: Periksa `git diff` untuk memastikan tidak ada perubahan liar atau artefak sementara.
8. **Pelaporan**: Laporkan file yang diubah/dibuat beserta log hasil build/test.

## Larangan Ketat (Restrictions)
- **Dilarang** melakukan `git push`, `git merge`, atau deployment.
- **Dilarang** mengubah lingkungan production atau menghapus database.
- **Dilarang** menampilkan API keys, token, atau secret ke log/jawaban.
- **Dilarang** menguji/bekerja langsung di branch utama (`main`/`master`) jika perubahan berisiko tinggi.
- **Dilarang** mengubah autentikasi, arsitektur database, framework, atau dependency utama tanpa persetujuan pengguna.

## Panduan Delegasi Subagent
Jika tugas besar dan dapat dipisahkan secara independen:
- Gunakan `delegate_task` dengan memberikan lokasi absolut proyek, stack, daftar file terkait, batasan, perintah tes, dan kriteria sukses yang spesifik.
