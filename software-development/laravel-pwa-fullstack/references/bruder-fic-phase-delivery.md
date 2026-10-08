# Bruder FIC PWA Phase-Gated Delivery Notes

Session-derived reference for Laravel/PWA work with Yohsan/Sandi, especially mobile-reviewed admin/user dashboards.

## Durable Patterns

### Phase-gated implementation
- When user requests “fase/tahap”, implement exactly that phase and stop.
- Provide a live HTTPS link after each phase.
- For backend-only phases, create a lightweight read-only check page (e.g. `/super-admin/fase-1-check`, `/super-admin/fase-2-check`) rather than building full later-phase UI.
- Keep phase check pages mobile-first and visually polished because user verifies on a phone.

### Laravel + Cloudflare Tunnel session fixes
Use these before asking user to test login:
- `.env`: `APP_URL=https://<tunnel-or-domain>`.
- `.env`: use `SESSION_DRIVER=file` if `sessions` table is not ready.
- `bootstrap/app.php`: `$middleware->trustProxies(at: '*');`.
- `AppServiceProvider`: `URL::forceScheme('https')` when `HTTP_X_FORWARDED_PROTO === 'https'` or `APP_URL` is HTTPS.
This prevents common `419 | PAGE EXPIRED` and cookie/CSRF mismatches.

### Role testing pitfall
If user sees `403` while testing admin/user pages, first check active browser session role. Switching from `userdemo` to `superadmin` in the same mobile browser requires logout/session reset. Do not assume route/middleware is broken until session role is verified.

### Mobile UX corrections
- Every sub-page/form needs a clear back button in header (`←`) or a full-width “Kembali” button.
- Use `Plus Jakarta Sans` + `Inter` explicitly in standalone Blade pages; mobile browsers may otherwise show ugly fallback fonts.
- Full-width bottom actions are preferred over small floating squares unless intentionally using FAB.
- Screenshot markups/circles are targeted feedback: fix that exact component first.

### User profile/account forms
For religious/community PWA user management, account creation may need identity fields beyond credentials:
- `birth_date`
- `parents_name`
- `last_education`
- `entry_year`
- `community_location`
- `phone`
- `bio`
Add DB columns, model `$fillable`, casts (`birth_date` date, `entry_year` int), validation, and show these fields in track record.

### Report/reflection forms
For formation/reflection modules:
- Enforce 200–500 character limit both backend and frontend.
- Add live character counters with red (<200 or >500) and green (within range).
- Support logbook/proof uploads: JPG/PNG/PDF max 5MB, stored under `storage/app/public/logbooks/...`.

## Verification Checklist
- `php -l` new PHP files/controllers.
- `php artisan route:list | grep <feature>`.
- `php artisan view:clear && php artisan route:clear` after Blade/route changes.
- Login with curl + cookie jar to verify protected routes.
- `npm run build` after frontend/CSS/Blade asset changes.
- Mobile browser screenshot review before advancing to next phase.
