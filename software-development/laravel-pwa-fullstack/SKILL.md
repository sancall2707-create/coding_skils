---
name: laravel-pwa-fullstack
description: Full-stack Laravel 11 + Vue 3 SPA + PWA development pattern with Sanctum auth, conflict detection, role-based dashboards, and production deployment.
tags: [laravel, vue3, pwa, sanctum, fullstack]
---

# Skill: Laravel PWA Full-Stack Development

Complete pattern for building production-ready PWA applications with Laravel 11 backend, Vue 3 SPA frontend, Sanctum authentication, and role-based access control.

## Scope
- Laravel 11 REST API with Sanctum token auth
- Vue 3 SPA frontend with Vue Router & Pinia state management
- PWA setup (manifest, service worker, install prompts)
- Business logic patterns (conflict detection, temporal/spatial constraints)
- Role-based multi-dashboard UI (Super Admin, Unit Admin, User)
- Production HTTPS deployment via Caddy or other reverse proxy

## Architecture Overview

### Backend (Laravel 11)
- **Database**: MariaDB with polymorphic relationships for flexible data modeling
- **Authentication**: Laravel Sanctum for API token-based auth
- **Authorization**: Policy-based gate system for resource-level permission checks
- **Business Logic**: Service classes (e.g., `BookingConflictService`) for complex validation
- **API Structure**: RESTful routes under `/api/*` with JSON responses

### Frontend (Vue 3)
- **Build Tool**: Vite (Laravel Vite plugin)
- **Routing**: Vue Router with protected routes via meta guards
- **State**: Pinia for auth store, booking store, and global state
- **UI**: Tailwind CSS responsive components
- **HTTP**: Axios with Bearer token injection for API calls

### PWA Essentials
- **Manifest**: `public/manifest.json` (standalone display, theme color, icons)
- **Service Worker**: `public/sw.js` (selective caching — **security critical**)
- **Install Button**: Floating UI component that triggers `beforeinstallprompt` event
- **HTTPS Requirement**: PWA features only work over HTTPS (mandatory for production)

## Critical Steps (Mandatory)

### 1. Setup & Project Structure
1. Create Laravel project: `composer create-project laravel/laravel app`
2. Install dependencies: Sanctum, Vite Vue plugin, Tailwind CSS
3. Create Vue app entry: `resources/js/app.js` with router, Pinia, and Vite CSS import
4. Create Blade host: `resources/views/welcome.blade.php` with `<div id="app"></div>` and Vite asset tags
5. Setup Caddy/nginx to reverse proxy PHP-FPM socket and serve public folder

### 2. Database & Models
1. Create migrations for business entities (avoid over-normalization; use polymorphic relationships where appropriate)
2. Seed initial data for testing (users with roles, demo fixtures)
3. Use soft deletes or status columns for audit trails (never hard-delete production data)

### 3. Authentication & Authorization
1. Add `HasApiTokens` trait to User model
2. Use `Sanctum` middleware for protected API routes
3. Create Policy classes for each resource (e.g., `BookingPolicy`, `VehiclePolicy`)
4. Use `Gate::authorize()` in controllers to enforce policies
5. Test token expiry, refresh logic, and logout token revocation

### 4. Business Logic (Service Classes)
1. Extract complex validation into dedicated service classes (e.g., `BookingConflictService`)
2. Service should be stateless and injectable via constructor
3. Write comprehensive test cases for boundary conditions (date overlaps, time ranges, constraints)
4. Call service consistently from both `store()` and `updateStatus()` endpoints

### 5. Frontend State & Routing
1. Create Pinia stores for auth (login/logout, user state, token storage) and domain logic (bookings, filters)
2. Setup Vue Router guards: `beforeEach` for auth checks, meta-based role restrictions
3. **IMPORTANT**: Store auth token in localStorage, not sessionStorage (survives page refresh for PWA)
4. Inject token into every API request via Axios interceptor

### 6. PWA Assembly
1. Create `public/manifest.json` with app name, icons (512x512 SVG/PNG), theme color, display mode `standalone`
2. Create `public/sw.js` with **strict caching rules** (see `references/service-worker-security.md`)
3. Add PWA meta tags to Blade host (apple-mobile-web-app, theme-color, icons)
4. Add Service Worker registration script + `beforeinstallprompt` handler to capture install event
5. Create floating Install Button component (`resources/js/components/InstallPwaButton.vue`)

### 7. Testing & Verification
1. **API**: Use curl or Python to test all endpoints (auth, CRUD, conflict scenarios)
2. **Build**: Run `npm run build` and verify no Vite/Vue compiler errors
3. **Permissions**: Check `public/manifest.json`, `public/sw.js`, icon files are world-readable
4. **Manifest**: Fetch and validate JSON structure (`curl http://localhost/manifest.json | jq .`)
5. **Conflict Logic**: Test boundary cases (same-day full-date conflict, overlapping time ranges)

### 8. Deployment to HTTPS
1. Use domain-based SSL (Caddy auto-renews Let's Encrypt via DNS challenge)
2. Or use internal SSL for testing (Caddy `tls internal` for self-signed certs)
3. Update Laravel `.env`: `APP_URL=https://your-domain.com`
4. Verify PWA installable via Chrome DevTools Application → Manifest tab
5. Test on mobile (iOS Safari or Android Chrome) to ensure install prompt appears

## Pitfalls & Common Issues

### Vue 3 Compilation
- **Error**: `v-else has no adjacent v-if` → Check template structure; `v-else` must directly follow `v-if` in same element/parent
- **Error**: Multiple root elements in `<template>` → Wrap multiple sections in `<template v-if>` or single root `<div>`
- **Fix**: Use `<template v-if="condition">` block elements to group logically without adding DOM wrapper

### Service Worker & Caching
- **Pitfall**: Caching HTML pages with old Vite asset hashes → After deployment, browser renders HTML with `<script src="...app-OldHash.js">` but SW cache cleared old hash. Blank page.
- **Pitfall**: Service Worker registration waiting for `load` event → Event may already fire before script registers. Browser does not activate SW until next reload.
- **Fix**: Register SW immediately (no `addEventListener('load')`). Append version query: `/sw.js?v=1` to bypass HTTP browser cache on SW.js itself.
- **Fix**: HTML navigation MUST be Network-First (`event.request.mode === 'navigate'`). Only Vite build hashed assets (`/build/assets/*`) are Cache-First.
- **Rule**: Evict ALL old cache versions immediately in `activate` event (`if (cache !== CACHE_NAME)`). No gradual migration.
- **Test**: Deploy new SW version, check browser DevTools Application tab → Service Worker shows `activated` state. Check Cache Storage → old cache names gone.

### Reverse Proxy & HTTPS Detection
- **Pitfall**: Laravel Error 419 (CSRF / Page Expired) or Mixed Content behind Cloudflare Tunnel / Reverse Proxy → Laravel running on HTTP behind tunnel sends HTTP session cookies / mismatched CSRF origin.
- **Fix 1**: In `bootstrap/app.php` (Laravel 11/12): Add `$middleware->trustProxies(at: '*');` so Laravel inspects `X-Forwarded-Proto` and `X-Forwarded-Host`.
- **Fix 2**: In `app/Providers/AppServiceProvider.php`: Call `URL::forceScheme('https')` when `HTTP_X_FORWARDED_PROTO === 'https'` or `APP_URL` contains `https://`.
- **Fix 3**: In `.env`: Set `APP_URL=https://<your-tunnel-domain>` and use `SESSION_DRIVER=file` (if DB session table is not migrated or schema mismatch).
- **Pitfall**: HTTP redirect loop (`ERR_TOO_MANY_REDIRECTS`) behind Cloudflare Tunnel → Caddy configured with `:443` or `tls internal` but receives HTTP from tunnel. Sends 308 redirect back, infinite loop.
- **Fix**: Use `:80` in Caddyfile (no TLS directives) when behind reverse proxy. Let tunnel handle SSL termination.
- **Pitfall**: Mixed Content error (HTTPS page + HTTP Vite assets) → Laravel running on HTTP port 80 generates `http://` URLs for assets. Browser blocks mixed content.

### Mobile PWA UI & Typography Hygiene
- **Pitfall**: Missing back button (`←`) in sub-page headers → User gets stuck on inner views (`/super-admin/users`, `/monitoring`) without intuitive navigation back to main dashboard.
- **Fix**: Every sub-page header MUST include a clear back button (`←` or `← Kembali`) in the top navigation bar, linking back to the parent dashboard or list view.
- **Pitfall**: Inconsistent system font fallbacks (e.g. mobile browser falling back to cursive/handwritten/monospace system fonts) or misaligned floating buttons on small screens.
- **Fix**: Explicitly preload Google Fonts (`Plus Jakarta Sans` & `Inter`) in `<head>`, use standard mobile shell container (`max-width: 480px; margin: 0 auto;`), and ensure action buttons use full width (`width: 100%`) with proper padding and icon alignment rather than small absolute/floating blocks.
- **User review pattern**: When a user marks/circles a UI element in a screenshot, treat it as targeted feedback on that component. Fix the specific visual problem first (size, positioning, alignment, tap target, whitespace) before broad redesign.
- **Role Session Mismatch in Testing**: When switching between User and Admin test links in the same browser, active session cookies can trigger `403 Access Denied`. Remind user to logout or use clear account switching.

### Phase-Gated Feature Delivery for User-Reviewed PWAs
- **Preference**: For large Laravel/PWA builds, implement one phase at a time and stop for user review. Do not continue to the next phase until the user explicitly approves the current phase.
- **Required deliverable after each phase**: Provide a live HTTPS check link (Cloudflare Tunnel link if available), test credentials if needed, and a concise list of changed files + executed verification commands.
- **Implementation pattern**: For backend-only phases, create a small read-only verification route/page such as `/super-admin/fase-1-check` or `/super-admin/fase-2-check` that demonstrates the new backend/model/service output without prematurely building later-phase UI.
- **Scope control**: If a plan says “Fase 1: database/model” or “Fase 2: backend services,” avoid sneaking in full UI/UX work from later phases. Minimal diagnostic pages are allowed only to let the user check the phase.

### SPA Routing & Direct Page Reloads
- **Pitfall**: `404 Not Found` when reloading directly on SPA routes (`/login`, `/vehicles`, `/bookings`) → Laravel has no route definition for `/login`, returns 404. Vue Router never loads.
- **Fix**: Add `Route::fallback(function() { return view('welcome'); })` in `routes/web.php` after all other routes. This serves the SPA Blade host for any unmatched web route. Vue Router renders the correct component client-side.
- **Test**: `curl -s -w "%{http_code}" https://your-domain/login` should return `200`, not `404`.

### Sanctum Token Management
- **Pitfall**: Token stored in `sessionStorage` → Lost on page refresh, breaks PWA offline experience
- **Fix**: Use `localStorage` for token persistence; clear on logout
- **Test**: Logout, refresh page, verify redirected to login (token must be gone)

### Permissions & File Serving
- **Error**: `manifest.json` returns HTML (Caddy 403) → Check `public/` file permissions
- **Fix**: `chmod 644 public/manifest.json public/sw.js public/icons/*`

### Conflict Detection Complexity
- **Pitfall**: Only checking date overlap for time-based items → Misses edge cases (same-start, end-at-start)
- **Pattern**: Use minute-based overlap logic; test with: (start1 < end2) AND (start2 < end1)
- **Real**: Tested with 08:00-12:00 vs 10:00-14:00 (overlap at 10:00-12:00) ✓

## Support References
- `references/bruder-fic-phase-delivery.md` — Phase-gated delivery, Cloudflare proxy session fixes, mobile UX header back buttons, profile fields, character counters
- `references/service-worker-security.md` — SW caching rules, Network-first vs Cache-first patterns, security verification, versioned SW registration
- `references/tunnel-proxy-troubleshooting.md` — Cloudflare Tunnel / Reverse Proxy HTTPS config, Caddyfile patterns, Laravel trusted proxies, SPA route fallback
- `references/conflict-detection-pattern.md` — Temporal & spatial conflict logic, test cases, integration pattern
- `templates/manifest.json.template` — PWA manifest boilerplate (copy to public/manifest.json)
- `scripts/verify-pwa-readiness.sh` — Automated check for manifest, icons, SW presence, permissions, security rules

## Quick Start Checklist (New Project)
1. Copy `templates/manifest.json.template` → `public/manifest.json` and customize
2. Copy `references/service-worker-security.md` example → `public/sw.js`
3. Run `scripts/verify-pwa-readiness.sh` after build
4. Follow Critical Steps 1-8 in SKILL.md

## Verification Checklist (Pre-Deployment)
- [ ] All API endpoints tested with tokens (admin & user roles)
- [ ] Conflict service tested on boundaries (same-day, overlapping ranges)
- [ ] Vue build passes without errors (`npm run build` exit code 0)
- [ ] PWA manifest valid JSON, icons present, theme color set
- [ ] Service Worker console logs show "Registered successfully"
- [ ] HTTPS enabled and Let's Encrypt cert valid
- [ ] Install prompt appears on mobile browser
- [ ] Login/register pages excluded from SW cache
- [ ] Role-based dashboards render correct data for each role
- [ ] Git commits clean, no lingering debug code or secrets

## Related Skills
- `coding-agent` (generic development procedures)
- Delegatable subtasks: database migrations, API testing, PWA icon generation, CI/CD setup
