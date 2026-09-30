# Space Link Phase 3–4 implementation patterns

## User area patterns
- `PilihFasilitas.jsx`: fetch `/api/v1/facilities`, client-side search + unit/type filters, cards link to `/fasilitas/:id`.
- `FacilityDetail.jsx`: fetch `/facilities/:id` and `/facilities/:id/schedule`; redirect back to list only after confirmed API failure. Remember seeded IDs change after `migrate:fresh --seed`.
- `BookingForm.jsx`: prefill `penanggung_jawab` and `no_hp` from authenticated user; use custom bottom-sheet `TimePicker`; call `/bookings/check-conflict` before submit; support dynamic `items[]`.
- `MyBookings.jsx`: search/status filters, paginate client-side for small datasets, make booking cards clickable to `/bookings/:id`.
- `BookingDetail.jsx`: show status timeline and approval audit fields, not just raw status.

## Admin dashboard patterns
- `Admin.jsx`: implement tabs as explicit conditional JSX (`activeTab === 'x' && <TabX />`). Avoid JSX dynamic tag syntax like `<TAB_COMPONENTS[activeTab] />`; Vite/Rolldown treats it as an unexpected token.
- `TabPengajuan.jsx`: super admin can final approve/reject/cancel; admin_unit can approve/reject only matching unit at unit stage; always send backend action names exactly (`approve_unit`, `reject_unit`, `approve_final`, `reject_final`, `cancel`).
- `TabKalender.jsx`: use month filter (`?month=YYYY-MM`) and expand multi-day bookings into each rendered calendar date.
- `TabFasilitas.jsx`, `TabKontak.jsx`, `TabKelolaAdmin.jsx`: gate UI affordances with `isSuperAdmin()`, but keep backend policies authoritative.

## Durable bugs/fixes
- Laravel date columns should use `whereDate()` when comparing against `YYYY-MM-DD` strings from request/test payloads. Using plain `where()` can miss overlaps depending on DB casting/time fragments.
- SPA fallback should be a catch-all GET route, e.g. `Route::get('/{any?}', fn () => view('app'))->where('any', '^(?!api).*$');` so hard refreshes on React routes work.
- Service workers can keep serving stale navigation shells and make browser route debugging misleading. For Laravel React dev/prod, do not cache navigation responses aggressively. Prefer network-first for `request.mode === 'navigate'`, skip `/api/*`, bump `CACHE_NAME`, and clear old caches in `activate`.
- If route `/fasilitas/:id` redirects back to list, verify the API ID exists first. After repeated `migrate:fresh --seed`, IDs drift unless DB reset is deterministic.
- JSX comments must be `{/* ... */}`; HTML `<!-- ... -->` causes Vite/Rolldown “Unexpected token”.
