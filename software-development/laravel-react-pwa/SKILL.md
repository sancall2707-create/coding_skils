---
name: laravel-react-pwa
description: Full-stack Progressive Web App development with Laravel (Sanctum API) + React (Vite, Tailwind) – authentication, role-based policies, service classes, conflict detection, PWA manifest & service worker, mobile-first UI components.
tags: [laravel, react, pwa, sanctum, vite, tailwind]
---

# Laravel + React PWA Development

## When to use
Building a progressive web app where the backend is Laravel (API, Sanctum tokens, policies) and the frontend is a React SPA (Vite, Tailwind CSS, React Router) with offline support, installability, and mobile-first components.

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

## References
- `references/branding-assets-pwa.md` – logo replacement pattern, PWA icon generation, favicon, auth card & header updates.
- `references/space-link-spec.md` – original Space Link documentation (roles, entities, flows).
- `references/space-link-phase3-4-patterns.md` – user area & admin dashboard implementation patterns and durable bug fixes.
- `references/space-link-pwa-polish.md` – PWA polish patterns: install prompt, offline banner, toast provider, SW cache clearing, mobile nav.
- `references/phase1-backend.md` – backend implementation notes (migrations, services, policies, tests).
- `references/phase2-frontend.md` – frontend implementation notes (React setup, components, PWA config).
- [ ] Login with seeded `superadmin@...` / `password123` redirects to `/`.
- [ ] Dashboard shows navy header, amber badge, stats cards, bottom nav on mobile viewport.
- [ ] Offline banner appears when network disconnected (devtools).
- [ ] Manifest loads, icons present, `sw.js` registered.

## References
- `references/space-link-spec.md` – original Space Link documentation (roles, entities, flows).
- `references/phase1-backend.md` – backend implementation notes (migrations, services, policies, tests).
- `references/phase2-frontend.md` – frontend implementation notes (React setup, components, PWA config).

## Templates
- `templates/app.blade.php` – SPA blade shell with fonts, manifest, @vite.
- `templates/AuthContext.jsx` – token handling, login/register/me/logout.
- `templates/TimePicker.jsx` – reusable bottom-sheet picker.
- `templates/sw.js` – service worker with NetworkFirst + StaleWhileRevalidate.
- `templates/manifest.webmanifest` – PWA manifest with navy/amber theme.

## Scripts
- `scripts/gen-icons.py` – Pillow script to generate 192/512 PNG icons (navy bg, amber rounded square, white “SL”).