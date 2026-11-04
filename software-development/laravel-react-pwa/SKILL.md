---
name: laravel-react-pwa
description: Full-stack Progressive Web App development with Laravel (Sanctum API) + React (Vite, Tailwind) – authentication, role-based policies, service classes, conflict detection, PWA manifest & service worker, mobile-first UI components.
tags: [laravel, react, pwa, sanctum, vite, tailwind]
---

# Laravel + React PWA Development

## When to use
Building a progressive web app where the backend is Laravel (API, Sanctum tokens, policies) and the frontend is a React SPA (Vite, Tailwind CSS, React Router) with offline support, installability, and mobile-first components.

Also use when **auditing** an already-running PWA subsystem — notifications, sessions, browser permissions, service worker behaviour — where the user reports "it still has errors" or asks whether the flow is correct. See `references/runtime-system-audit-methodology.md` for the evidence-first method and report format.

## Core Stack
- **Backend**: Laravel 11, Sanctum (token auth), Policies, Service classes, Feature tests (PHPUnit)
- **Frontend**: React 18, Vite, Tailwind CSS v4, Lucide icons, React Router v6
- **PWA**: Web App Manifest, Service Worker (NetworkFirst for navigation, StaleWhileRevalidate for assets), icons 192/512
- **Testing**: Backend `php artisan test`, Frontend `npm run build`

## Project Structure (key paths)
```
app/
  Http/Controllers/Api/      # API controllers (Auth, Facility, Booking, AdminGrant, ContactInfo)
  Models/                    # Eloquent models with fills, casts, relationships
  Policies/                  # Role/unit based policies
  Services/                  # Business logic (ScheduleConflictChecker, CreateBookingService, BookingActionService, AdminGrantService)
  Providers/AppServiceProvider.php   # URL::forceScheme('https') behind proxy
database/
  migrations/                # users (app_role, unit), facilities, bookings, admin_grants, contact_infos
  seeders/DatabaseSeeder.php # Super admin, admin_unit per unit, regular user, facilities, contacts
routes/
  api.php                    # /api/v1/* routes, auth:sanctum middleware
  web.php                    # SPA fallback to resources/views/app.blade.php
resources/
  views/app.blade.php        # HTML shell, loads @vite react entry, manifest, fonts
  js/
    app.jsx                  # React entry, BrowserRouter, AuthProvider, ProtectedRoute
    context/AuthContext.jsx  # login/register/me/logout, token in localStorage
    components/
      ProtectedRoute.jsx
      AppLayout.jsx          # Header (navy), Bottom nav (mobile), OfflineBanner
      TimePicker.jsx         # Bottom-sheet hour/minute picker (06-20)
      StatusPill.jsx
    pages/
      Login.jsx, Register.jsx, Home.jsx, PilihFasilitas.jsx, FacilityDetail.jsx,
      BookingForm.jsx, MyBookings.jsx, BookingDetail.jsx, Admin.jsx, PanduanPWA.jsx
    lib/api.js               # Axios instance with token interceptor
  css/app.css                # Tailwind + design tokens (navy #0F2C59, amber #F2B807)
public/
  manifest.webmanifest
  sw.js
  icons/icon-192x192.png, icon-512x512.png
```

## Mandatory Steps (per feature)
1. **Migrations & Models** – add `app_role` (`super_admin|admin_unit|user`), `unit` enum, `phone_number` on users; facilities unified (type `tempat|kendaraan`, unit enum).
2. **Policies** – `BookingPolicy` (owner, admin_unit per unit, super_admin), `FacilityPolicy` (super_admin CRUD), `AdminGrantPolicy`, `ContactInfoPolicy`.
3. **Services** – isolate business logic:
   - `ScheduleConflictChecker::check()` – date overlap for `tempat`, time overlap for `kendaraan`.
   - `CreateBookingService::create()` – validates, sets initial status (`menunggu_unit` for aula units, `menunggu_super` otherwise).
   - `BookingActionService` – `approveByUnit`, `rejectByUnit`, `approveBySuper`, `rejectBySuper`, `cancelBySuper` (each re-checks conflicts – TOCTOU mitigation).
   - `AdminGrantService` – promote/demote/invite/accept + audit log.
4. **Controllers** – thin, call services, return JSON, use `Gate::authorize`.
5. **Routes** – `/api/v1` group, `auth:sanctum` middleware, role-gated via policies.
6. **Frontend Auth** – `AuthContext` stores user + token; `ProtectedRoute` guards by `requireAdmin` / `requireSuperAdmin`.
7. **UI Components** – `AppLayout` (sticky navy header, bottom mobile nav, safe-area), `TimePicker` bottom sheet, `OfflineBanner` (listens online/offline).
8. **PWA** – `manifest.webmanifest` (standalone, theme_color navy), `sw.js` (NetworkFirst navigation, StaleWhileRevalidate assets, skip API), icons generated.
9. **Testing** – Feature tests for conflict detection, approval flow, admin management (`php artisan test`).
10. **Build & Verify** – `npm run build` (zero errors), `php artisan test` (all green), visual smoke test via headless browser (login → dashboard).

## Pitfalls & Fixes
- **HTTPS scheme & Cloudflare Tunnel (HTTP 419 / CSRF Mismatch)** – Behind Cloudflare Tunnel (`cloudflared`), Laravel gets requests over HTTP from local proxy. Fix 419 Page Expired:
  1. Add `$middleware->trustProxies(at: '*');` in `bootstrap/app.php`.
  2. Set `URL::forceScheme('https')` in `AppServiceProvider::boot()` when `APP_URL` starts with `https://` or `HTTP_X_FORWARDED_PROTO == 'https'`.
  3. Ensure `SESSION_DRIVER=file` (or migrate session table if using `database`).
  4. Set `APP_URL=https://<your-tunnel>.trycloudflare.com` in `.env`.
- **HTTPS scheme on local dev** – `URL::forceScheme('https')` triggers when `APP_URL` contains `https://`. For local `php artisan serve` set `APP_URL=http://127.0.0.1:8020` (or the actual port) to avoid mixed-content asset URLs.
- **Route cache** – after editing `routes/api.php` run `php artisan route:clear` before testing.
- **Vue remnants** – if repo previously used Vue, delete `resources/js/*.vue`, `stores/`, `router/`, `components/`, `pages/` before adding React files.
- **HTML comments in JSX** – use `{/* comment */}` not `<!-- -->`; otherwise Vite/Rolldown throws “Unexpected token”.
- **Dynamic component tags in JSX** – avoid `<TAB_COMPONENTS[activeTab] />`; use explicit conditional rendering (`{activeTab === 'x' && <TabX />}`).
- **Service worker caching** – never cache `/api/*` or POST; `request.mode === 'navigate'` gets NetworkFirst so SPA shell stays fresh.
- **Laravel Date Overlap Queries** – use `whereDate('tanggal_mulai', '<=', $endDate)` instead of plain `where()` to avoid type/string mismatch in conflict checks.
- **SPA Fallback Route** – use `Route::get('/{any?}', fn() => view('app'))->where('any', '^(?!api).*$');` so deep links like `/fasilitas/26` render the Blade shell instead of 404ing.
- **TimePicker range** – default to full 24-hour selection (`00`–`23`) and all minutes (`00`–`59`) unless the user explicitly requests school-hour / interval restrictions. Auto-scroll the selected hour/minute into view when opening the picker.
- **Seed before manual test** – `php artisan db:seed` after fresh migrate, and note that auto-increment IDs shift after re-seeding.
- **Web Push (minishlink/web-push v11) Constructor** – do not pass integer timeout as argument #3 (`TypeError: Argument #3 ($client) must be of type ?Psr\Http\Client\ClientInterface, int given`). Pass `$auth` and `$defaultOptions` (e.g. `['TTL' => 86400]`).
- **Android PWA Badging vs Chrome Host** – Android Chrome routes push notifications through `com.android.chrome`. Android launchers badge the parent Chrome icon in the dock rather than the PWA shortcut on homescreen. For standalone app icon badges, wrap PWA into a TWA/Capacitor APK with its own Android package ID.
- **Web Push Logout Token Cleanup** – Always clear `PushSubscription` records for the logged-out user in `AuthenticatedSessionController@destroy` and unsubscribe in the client SW, otherwise notifications for previous user accounts on shared devices leak across sessions.
- **`Notification.permission === 'granted'` does NOT imply a PushSubscription exists** – single most common cause of "notifications never arrive". A device can hold `granted` permission with no subscription object, so no token ever reaches the server and nothing is sent — with zero error messages. A `syncSubscription()` that only re-sends an *existing* subscription is the bug; it must CREATE one when permission is already `granted` (no new dialog appears). Never gate token registration on a manual button click — the button is only for the first permission request. See `references/pwa-web-push-android-badging.md` §5.
- **Missing `pushsubscriptionchange` handler is a time bomb** – browsers/FCM rotate subscriptions periodically; without the handler, push silently stops days later with no code change. Audit with `grep -nE "addEventListener\('(push|notificationclick|pushsubscriptionchange)'" public/sw.js`. The rotation endpoint runs with no page open, so it has no CSRF token and possibly no session: give it its own route outside `auth`, exempt it via `$middleware->validateCsrfTokens(except: ['push/rotate'])`, add `throttle`, require a *previously registered* old endpoint, and derive ownership from the old DB row (never from `auth()->id()` or caller input). See §6.
- **`setAppBadge` called from a Service Worker is usually dead code** – MDN *does* list `WorkerNavigator.setAppBadge()`, so "unavailable in SW" is wrong; the real defect is calling it with no argument (yields a dot, never a number). Correct pattern: the SW `postMessage`s open clients and the *page* sets the badge with a real count. Also set expectations honestly — per MDN's compat table the Badging API is unsupported on Chrome Android, Samsung Browser, Opera Android, Firefox Android **and WebView Android**, so it will not show numbers on Android even inside a TWA. Visible Android icon badges come from *system notifications*, not this API. See §7.
- **Notification system installed in only some Blade layouts** – projects with separate user/admin layouts easily wire the script into one only; the missed layout never syncs tokens and never revokes them on logout, leaking notifications across accounts. Audit with `grep -rln "notifikasi.js" resources/views/`. For admin panels where the user forbids new UI, install a *minimal* version: `<meta name="csrf-token">` + the script, with no bell element, and assert `assertStringNotContainsString('id="notifBell"', $html)` to lock the no-visual-change contract. Note `meta csrf-token` is often absent from older layouts, which makes every JS `fetch` POST return 419. See §8.
- **Be honest about TWA limits** – a TWA APK does NOT remove the Chrome dependency (Chrome must still be installed; it is still the Chrome engine). What changes is the app identity/package so badges *should* attach to the app icon; launcher policy still decides. True Chrome independence needs native/Capacitor + native FCM. Promising "the APK will fix badging" and then failing costs user trust. See §3a.
- **A notification defect can live INSIDE the APK, not in your web code** – Web Push can be 100% correct server-side (real send confirmed, token in DB, no log errors) and still fail because the APK manifest lacks `android.support.customtabs.trusted.DELEGATE_NOTIFICATIONS`. Symptom: the app's notification toggle in Android Settings is **off and cannot be switched on**. Do NOT blame launcher policy (ColorOS vs MIUI) first — that wastes the user's time. An APK is a zip and `AndroidManifest.xml` keeps its string pool in UTF-16LE, so you can audit it with pure Python, no apktool/JDK (important on a RAM-tight VPS). Beware: the APK can carry `POST_NOTIFICATIONS` + `DelegationService` and look complete while `DELEGATE_NOTIFICATIONS` is missing. See `references/twa-apk-packaging-notifications.md` §2–§3.
- **PWABuilder has 3 identical-looking `Generate Package` panels** – Google Play is the *second*; the "Other Android" tab lacks `Signing key` entirely, so you cannot reuse the old keystore. Diagnose a user's screenshot by counting *missing* options: if they see `Display mode → Meta Quest compatible → Fallback behavior`, five options were skipped, so it is a different panel — never conclude "the option doesn't exist". PWABuilder's docs also lag its UI, so verify against the live DOM, and note it uses Web Components: plain `querySelector` and accessibility snapshots miss everything, you must walk `shadowRoot` recursively. See §4.
- **Rebuilding an APK must reuse the original keystore** – Android matches the APK's SHA-256 against `/.well-known/assetlinks.json`; a mismatch shows the Chrome address bar or fails launch. Prefer `Use mine`: a new key means `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (user must uninstall first) and two keys to track, which Play Store rejects later. `sha256_cert_fingerprints` is an array, so merging old+new is a valid fallback. Verify the user picked `Use mine` by confirming the *Key full name / organization* fields disappeared. See §5.

## References
- `references/runtime-system-audit-methodology.md` – when the user asks to *audit* a running subsystem: evidence-gathering order (DB → logs → live-vs-local diff → coverage grep → endpoint codes → browser), safe test harness on a DB copy, a table of harness pitfalls that produce false results, and the finding-report format (severity codes, evidence blocks, "already correct" table, minimal-vs-full variant, ask before executing).
- `references/pwa-web-push-android-badging.md` – Web Push (VAPID) patterns, minishlink v11 signature fix + reflection probe, the `granted`-without-subscription root cause, safe `pushsubscriptionchange` rotation endpoint, `setAppBadge` context rules, layout-coverage audit, a 10-step notification audit checklist, and the Chrome DevTools Protocol verification harness (with its own pitfalls).
- `references/twa-apk-packaging-notifications.md` – wrapping a PWA into a TWA APK: reading `AndroidManifest.xml` from the APK zip with pure Python (no apktool/JDK), the missing `DELEGATE_NOTIFICATIONS` meta-data that silently kills notifications, navigating PWABuilder's three look-alike panels (+ shadow-DOM walker), keystore/`assetlinks.json` fingerprint continuity with an A-vs-B trade-off table, and the diagnosis order to run before blaming launcher policy.
- `references/pwa-form-bulk-delete-cache-patterns.md` – form placeholder rules, bulk delete scoping & modal, SoftDeletes test assertions, avatar cache-busting.
- `references/branding-assets-pwa.md` – logo replacement pattern, PWA icon generation, favicon, auth card & header updates.
- `references/space-link-spec.md` – original Space Link documentation (roles, entities, flows).
- `references/space-link-phase3-4-patterns.md` – user area & admin dashboard implementation patterns and durable bug fixes.
- `references/space-link-pwa-polish.md` – PWA polish patterns: install prompt, offline banner, toast provider, SW cache clearing, mobile nav.
- `references/phase1-backend.md` – backend implementation notes (migrations, services, policies, tests).
- `references/phase2-frontend.md` – frontend implementation notes (React setup, components, PWA config).

## Smoke Test Checklist
- [ ] Login with seeded `superadmin@...` / `password123` redirects to `/`.
- [ ] Dashboard shows navy header, amber badge, stats cards, bottom nav on mobile viewport.
- [ ] Offline banner appears when network disconnected (devtools).
- [ ] Manifest loads, icons present, `sw.js` registered.

## Templates
- `templates/app.blade.php` – SPA blade shell with fonts, manifest, @vite.
- `templates/AuthContext.jsx` – token handling, login/register/me/logout.
- `templates/TimePicker.jsx` – reusable bottom-sheet picker.
- `templates/sw.js` – service worker with NetworkFirst + StaleWhileRevalidate.
- `templates/manifest.webmanifest` – PWA manifest with navy/amber theme.

## Scripts
- `scripts/gen-icons.py` – Pillow script to generate 192/512 PNG icons (navy bg, amber rounded square, white “SL”).