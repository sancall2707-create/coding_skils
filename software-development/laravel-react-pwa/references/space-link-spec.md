# Space Link — PL Deltamas PWA Spec

## App Purpose
Progressive Web App for borrowing school facilities at Sekolah Pangudi Luhur Deltamas: aula (PG-TK/SD/SMP/SMA), lapangan, and operational vehicles.

## Stack
- Frontend: React + Vite + Tailwind CSS (+ shadcn/ui style patterns)
- Backend: Laravel API + Sanctum tokens in the local implementation; Base44 was the original reference app.
- PWA: custom Service Worker + Manifest
- Timezone: Asia/Jakarta (WIB)

## Roles
- `super_admin`: full access; manage facilities, contacts, admins; final approval; cancel approved booking.
- `admin_unit`: read all history/schedules; approve/reject only aula for own `unit`.
- `user`: submit bookings, view own history.

User fields:
- `app_role`: `super_admin|admin_unit|user`
- `unit`: `PG-TK|SD|SMP|SMA|null`

## Entities
### Facility
Fields: `name`, `type` (`kendaraan|tempat`), `unit` (`PG-TK|SD|SMP|SMA|lapangan|kendaraan`), `description`, `image_url`, `location`, `capacity`, `active`.

### Booking
Fields: `facility_id`, `facility_name`, `facility_type`, `unit`, `category`, `penanggung_jawab`, `driver`, `keperluan`, `penyelenggara`, `nama_kegiatan`, `deskripsi`, `no_hp`, `items`, `fasilitas_tambahan`, `tanggal_mulai`, `tanggal_selesai`, `jam_mulai`, `jam_selesai`, `status`, `owner_id`, approval/cancel audit fields, `konfirmasi_sekolah`.

Statuses: `menunggu_unit`, `menunggu_super`, `disetujui`, `ditolak`, `dibatalkan`.

### AdminGrant
Audit log for `promote`, `demote`, `invite`; supports pending invite status.

### ContactInfo
WhatsApp contact list: `name`, `phone`, `label`, `sapaan`, `active`.

## Availability Rules
- `tempat` (aula/lapangan): availability by date overlap. Any approved booking overlapping date range blocks new approval/submission.
- `kendaraan`: availability by date + time overlap. Same day different time is allowed.
- Check conflicts at submission and again before approval to prevent TOCTOU.

## Approval Flow
### Aula units (`PG-TK|SD|SMP|SMA`)
1. User submits → `menunggu_unit`.
2. Admin Unit approves/rejects own unit → `menunggu_super` or `ditolak`.
3. Super Admin final approves/rejects → `disetujui` or `ditolak`.

### Lapangan/Kendaraan
User submits → `menunggu_super`; Super Admin decides final.

## Cancellation
Super Admin can cancel approved bookings only. `cancel_reason` is mandatory; save `cancel_by`, `cancel_by_name`, `cancel_at`.

## UI/UX Reference
- Navy `#0F2C59`, Amber `#F2B807`, white surfaces.
- Fonts: Plus Jakarta Sans (heading), Inter (body).
- Auth page: centered card, SL badge, email/password icons, full-width navy submit button, register link.
- Home page: sticky navy header, amber SL badge, hero card, quick action buttons, stats cards, mobile bottom nav.
- Time input: custom bottom-sheet TimePicker, not browser `type=time`.
- Offline: banner shown; booking form blocked while offline.

## Verification Flow
- `php artisan migrate:fresh --seed --force`
- `php artisan test`
- `npm run build`
- Browser visual smoke: `/login` → login seeded super admin → `/` dashboard.
