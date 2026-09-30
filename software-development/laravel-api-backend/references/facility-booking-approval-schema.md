# Facility Booking + Multi-Step Approval Schema Pattern

Use for school/facility-loan PWAs that manage rooms/halls/fields/vehicles with role-based approval and schedule-conflict checks.

## When to use
- Facilities include both `tempat` (aula/lapangan/ruangan) and `kendaraan`.
- Users submit booking requests.
- Admin Unit approves only their own unit's hall/room; Super Admin gives final approval or cancellation.
- Schedule conflicts must be checked server-side at submit and approval time.

## Recommended tables

### `users`
Add app-level role fields separate from Laravel's default auth fields:
- `app_role`: enum/string `super_admin | admin_unit | user`
- `unit`: nullable enum/string `PG-TK | SD | SMP | SMA | lapangan | kendaraan`
- `phone_number`: nullable string

Model helpers:
```php
public function isSuperAdmin(): bool { return $this->app_role === 'super_admin'; }
public function isAdminUnit(): bool { return $this->app_role === 'admin_unit'; }
public function isRegularUser(): bool { return $this->app_role === 'user'; }
```

### `facilities`
Prefer one unified facilities table over separate `vehicles` + `facilities` if the UI treats all items as bookable resources.
- `name`
- `type`: `kendaraan | tempat`
- `unit`: `PG-TK | SD | SMP | SMA | lapangan | kendaraan`
- `description`, `image_url`, `location`, `capacity`
- `active` boolean default true

Index: `['type', 'unit', 'active']`.

### `bookings`
Use snapshot fields for facility name/type/unit so old bookings remain readable after facility edits:
- `facility_id` FK to facilities
- `facility_name` snapshot
- `facility_type` snapshot `kendaraan | tempat`
- `unit` snapshot
- `category`: `PG-TK | SD | SMP | SMA | Bruderan | Gereja | Umum | Instansi | Pribadi`
- `penanggung_jawab`, `no_hp`
- vehicle fields: `driver`, `keperluan`
- place/event fields: `penyelenggara`, `nama_kegiatan`, `deskripsi`, `items` JSON, `fasilitas_tambahan`
- schedule: `tanggal_mulai`, `tanggal_selesai`, `jam_mulai`, `jam_selesai`
- status: `menunggu_unit | menunggu_super | disetujui | ditolak | dibatalkan`
- owner: `owner_id` FK to users
- unit approval audit: `unit_decided_by`, `unit_decided_by_name`, `unit_decided_at`, `unit_note`
- final approval audit: `final_decided_by`, `final_decided_by_name`, `final_decided_at`, `final_note`
- cancellation audit: `cancel_by`, `cancel_by_name`, `cancel_at`, `cancel_reason`
- `konfirmasi_sekolah`: `belum | sudah`

Indexes:
```php
$table->index(['facility_id', 'status', 'tanggal_mulai', 'tanggal_selesai'], 'idx_booking_schedule_conflict');
$table->index(['owner_id', 'status']);
$table->index(['unit', 'status']);
```

### `admin_grants`
Audit log for admin role changes / invitations:
- `target_user_id` nullable FK
- `target_name`, `target_email`, `invite_email`
- `action`: `promote | demote | invite`
- `new_role`: `super_admin | admin_unit | user`
- `new_unit`: nullable `PG-TK | SD | SMP | SMA`
- `prev_role`, `prev_unit`
- `status`: `pending | active`
- `granted_by_id` FK, `granted_by_name`

### `contact_infos`
WhatsApp/contact directory:
- `name`, `phone`, `label`
- `sapaan`: `Bapak | Ibu`
- `active` boolean

## Service Pattern: ScheduleConflictChecker

Place in `app/Services/ScheduleConflictChecker.php`. Injected into `CreateBookingService` and `BookingActionService`.

```php
public function check(Facility $facility, string $tanggalMulai, string $tanggalSelesai,
    ?string $jamMulai = null, ?string $jamSelesai = null, ?int $excludeBookingId = null): array
{
    // Only 'disetujui' bookings block schedule
    $query = Booking::where('facility_id', $facility->id)
        ->where('status', 'disetujui')
        ->where('tanggal_mulai', '<=', $tanggalSelesai)
        ->where('tanggal_selesai', '>=', $tanggalMulai);
    if ($excludeBookingId) $query->where('id', '!=', $excludeBookingId);
    $overlapping = $query->get();
    if ($overlapping->isEmpty()) return ['has_conflict' => false, 'conflicts' => [], 'message' => null];

    // tempat: any date overlap = conflict
    if ($facility->type === 'tempat') { /* return has_conflict=true */ }

    // kendaraan: additionally check time overlap per booking
    // Time overlap: (newStart < existEnd) AND (newEnd > existStart)
    // Convert HH:MM to minutes for comparison
}
```

Key rules:
- `tempat` (aula/lapangan) → conflict on date overlap alone.
- `kendaraan` → conflict only if date AND time windows overlap.
- Missing time defaults: `null jam_mulai` = 00:00 (0 min), `null jam_selesai` = 23:59 (1440 min).
- Return `{has_conflict: bool, conflicts: array, message: string|null}`.

## Service Pattern: BookingActionService

3 approval methods + reject methods + cancel:

```php
// Admin Unit approves (menunggu_unit → menunggu_super)
public function approveByUnit(Booking $booking, User $adminUnit, ?string $note): array

// Admin Unit rejects (menunggu_unit → ditolak)
public function rejectByUnit(Booking $booking, User $adminUnit, string $reason): array

// Super Admin final approve (menunggu_super → disetujui)
// Also accepts menunggu_unit for lapangan/kendaraan (skip unit stage)
public function approveBySuper(Booking $booking, User $superAdmin, ?string $note): array

// Super Admin final reject (menunggu_super → ditolak)
public function rejectBySuper(Booking $booking, User $superAdmin, string $reason): array

// Super Admin cancel (disetujui → dibatalkan), reason required
public function cancelBySuper(Booking $booking, User $superAdmin, string $reason): array
```

Every approve method must re-check conflicts via `ScheduleConflictChecker::check()` immediately before updating status (TOCTOU mitigation). If conflict found, return `['success' => false, 'message' => ..., 'conflicts' => [...]]` and let controller return 422.

## Initial Status Determination

```php
// Aula (tempat + unit in PG-TK/SD/SMP/SMA) → menunggu_unit (2-stage)
// Lapangan + Kendaraan → menunggu_super (1-stage, Super Admin only)
$initialStatus = 'menunggu_super';
if ($facility->type === 'tempat' && in_array($facility->unit, ['PG-TK', 'SD', 'SMP', 'SMA'])) {
    $initialStatus = 'menunggu_unit';
}
```

## Action Endpoint Pattern

Single `POST /bookings/{id}/action` endpoint replaces separate approve/reject routes:
```php
$validated = $request->validate([
    'action' => 'required|in:approve_unit,reject_unit,approve_final,reject_final,cancel',
    'note' => 'nullable|string',
    'reason' => 'nullable|string',
]);
```

Gate::authorize() each action using BookingPolicy method matching the action name.

## Modeling notes
- If converting from an older polymorphic design (`vehicles` + `facilities` + `bookable_type/bookable_id`), either add a new migration path or, early in greenfield work, replace with the unified `facilities` table before building APIs.
- Keep server-side schedule conflict logic centralized and call it twice: on create request and immediately before approval to mitigate TOCTOU.
- For place/aula/lapangan, conflicts are usually date-range based; for vehicles, conflicts are time-range based.
- Keep `admin_unit` read access broad if needed, but decision authority must be unit-scoped.

## Verification commands
```bash
php artisan migrate:fresh --seed --force
php artisan test
```
