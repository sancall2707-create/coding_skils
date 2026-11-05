# Evaluasi hosting DomaiNesia lewat MCP (hanya baca)

## Akses MCP tanpa tool terpasang
Tool MCP bisa tidak muncul di sesi. Endpoint `https://mcp.formatio-fic.com/` adalah JSON-RPC via HTTP (protokol 2025-03-26) dengan OAuth.
- Token: `~/.hermes/profiles/coding/mcp-tokens/bruder-muda.json` (access_token berumur 1 jam, ada refresh_token), `bruder-muda.client.json` (client_id), `bruder-muda.meta.json` (token_endpoint).
- Access token kedaluwarsa: refresh dengan POST form `grant_type=refresh_token&refresh_token=...&client_id=...` ke `token_endpoint`, tulis balik `expires_at = now + expires_in`.
- Urutan: `initialize` -> notifikasi `notifications/initialized` -> `tools/list` -> `tools/call`. Header `Authorization: Bearer`, `Accept: application/json, text/event-stream`, simpan `Mcp-Session-Id`. Jangan cetak token; sensor sebelum melaporkan.

## Tool yang ada (8)
Baca: `list_domains`, `get_disk_usage`, `get_account_info`, `git_deploy_list`, `git_deploy_list_domains`, `git_deploy_log(id)`. Tulis: `git_deploy_add`, `git_deploy_deploy(confirm=true)`. Tidak ada shell, composer, artisan, cron, atau unggah berkas. `get_account_info` memuat token pihak ketiga (mis. sitejet); jangan salin ke laporan.

## Fakta paket nimbus_go (formatio-fic.com)
IP 202.155.137.49, cPanel + CloudLinux LVE: RAM 1 GB (`lve_pmem`), CPU 100% (1 core), 150 proses, disk 15 GB. Docroot utama `/home/formatio/public_html`, `mcp.formatio-fic.com` -> `/home/formatio/mcp`. Deploy Git id `4c4555f7` (branch main) terakhir 23 Okt, commit `1f16ba0`, tertinggal 44 commit; halaman utama masih "Hosted by DomaiNesia", `/login` 404, `/public/login` 500 (docroot bukan `public/`).

Uji hosting tanpa mengubah DNS: `curl --resolve formatio-fic.com:443:202.155.137.49 https://formatio-fic.com/...`.

## Kesimpulan yang sudah diberikan
Bukan peningkatan (1 core/1 GB < VPS 2 core/3,6 GB), PDF raport memakai `/usr/bin/google-chrome-stable` sehingga rusak di hosting bersama, data (SQLite, `storage/app`) tidak ikut repo. Cocok untuk situs statis / server MCP.
