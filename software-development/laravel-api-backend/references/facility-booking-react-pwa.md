# Facility Booking React PWA Pattern

Use for school/facility reservation apps with Laravel API + React PWA frontend.

## Domain Shape
- Unified `facilities` table covers rooms/aulas/lapangan and vehicles:
  - `type`: `tempat` | `kendaraan`
  - `unit`: `PG-TK`, `SD`, `SMP`, `SMA`, `lapangan`, `kendaraan`
- `bookings` stores facility snapshots (`facility_name`, `facility_type`, `unit`) plus audit fields for unit/final approvals and cancellation.
- Roles:
  - `super_admin`: full access, final approval, cancellation.
  - `admin_unit`: read all, approve/reject only own unit at unit stage.
  - `user`: create/list own bookings.

## Conflict Rules
- Only `status = disetujui` blocks a new booking.
- Tempat: any overlapping date range conflicts.
- Kendaraan: overlapping date range AND overlapping time window conflicts.
- Use `whereDate()` for date column comparisons to avoid false negatives in tests/DB drivers:
```php
Booking::where('facility_id', $facility->id)
  ->where('status', 'disetujui')
  ->whereDate('tanggal_mulai', '<=', $endDate)
  ->whereDate('tanggal_selesai', '>=', $startDate);
```
- Re-check conflicts both on create and before approval (TOCTOU mitigation).

## React PWA Frontend Structure
- `AuthContext.jsx`: stores Sanctum token in `localStorage`, exposes `login`, `register`, `logout`, `isAdmin`, `isSuperAdmin`.
- `ProtectedRoute.jsx`: gate authenticated/admin/super_admin routes.
- `AppLayout.jsx`: navy header, mobile bottom nav, offline banner.
- User flow pages:
  - `PilihFasilitas.jsx`: search + filter + card list.
  - `FacilityDetail.jsx`: facility info + schedule + `Ajukan Peminjaman`.
  - `BookingForm.jsx`: identity, activity, date range, custom `TimePicker`, dynamic extra items, conflict check.
  - `MyBookings.jsx`: status filter + search + paginated cards.
  - `BookingDetail.jsx`: timeline + status pill + notes.

## Service Worker Pitfall
Do not cache SPA navigations with stale route HTML. It can make `/fasilitas/26` render old `/pilih-fasilitas` content.
Use fresh network fetch for navigation:
```js
if (request.mode === 'navigate') {
  event.respondWith(fetch(request).catch(() => caches.match('/')));
  return;
}
```
Also clear old SW/caches during debugging:
```js
const regs = await navigator.serviceWorker.getRegistrations();
for (const r of regs) await r.unregister();
const keys = await caches.keys();
for (const k of keys) await caches.delete(k);
```

## Verification Gate Per Phase
Before moving to next phase:
```bash
npm run build
php artisan test
php artisan route:clear
```
Then run a browser visual check on critical pages and verify no truncation/layout breakage.
