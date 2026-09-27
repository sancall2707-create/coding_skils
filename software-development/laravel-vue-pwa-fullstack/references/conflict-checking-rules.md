# Conflict Checking Rules Reference

This document captures the exact conflict checking logic implemented in `BookingConflictService` for the PL Deltamas PWA project.

## Rule 1: Facility (Ruangan & Lapangan) - Full Date Basis

**Rule**: If a facility is already `approved` on ANY date within the requested range, the new request cannot be approved.

### Logic
```php
// Check if facility has ANY approved booking that overlaps the requested date range
$conflicts = Booking::where('bookable_type', 'App\Models\Facility')
    ->where('bookable_id', $facilityId)
    ->where('status', 'approved')
    ->where(function ($q) use ($dateFrom, $dateTo) {
        $q->whereBetween('date_from', [$dateFrom, $dateTo])
          ->orWhereBetween('date_to', [$dateFrom, $dateTo])
          ->orWhere(function ($subQ) use ($dateFrom, $dateTo) {
              $subQ->where('date_from', '<=', $dateFrom)
                   ->where('date_to', '>=', $dateTo);
          });
    })
    ->get();
```

### Example Scenarios
| Existing Approved | New Request | Result |
|-------------------|-------------|--------|
| Aula SD: 2026-10-05 08:00-17:00 | Aula SD: 2026-10-05 18:00-21:00 | **CONFLICT** (same date) |
| Aula SD: 2026-10-05 | Aula SD: 2026-10-06 | **OK** (different date) |
| Aula SD: 2026-10-01 to 2026-10-10 | Aula SD: 2026-10-05 | **CONFLICT** (date inside range) |
| Aula SD: 2026-10-05 to 2026-10-10 | Aula SD: 2026-10-01 to 2026-10-15 | **CONFLICT** (enveloping) |

---

## Rule 2: Vehicle (Kendaraan) - Date + Time Overlap

**Rule**: Conflict only if BOTH date range overlaps AND time range overlaps.

### Logic
```php
// 1. First filter by date overlap
$candidates = Booking::where('bookable_type', 'App\Models\Vehicle')
    ->where('bookable_id', $vehicleId)
    ->where('status', 'approved')
    ->where(function ($q) use ($dateFrom, $dateTo) {
        $q->whereBetween('date_from', [$dateFrom, $dateTo])
          ->orWhereBetween('date_to', [$dateFrom, $dateTo])
          ->orWhere(function ($subQ) use ($dateFrom, $dateTo) {
              $subQ->where('date_from', '<=', $dateFrom)
                   ->where('date_to', '>=', $dateTo);
          });
    })
    ->get();

// 2. Then filter by time overlap (in-memory)
$conflicts = $candidates->filter(function ($booking) use ($timeFrom, $timeTo) {
    return $this->isTimeOverlapping($timeFrom, $timeTo, $booking->time_from, $booking->time_to);
});

private function isTimeOverlapping($start1, $end1, $start2, $end2): bool {
    $start1Min = $this->timeToMinutes($start1);
    $end1Min = $this->timeToMinutes($end1);
    $start2Min = $this->timeToMinutes($start2);
    $end2Min = $this->timeToMinutes($end2);
    return $start1Min < $end2Min && $start2Min < $end1Min;
}

private function timeToMinutes(string $time): int {
    [$hours, $minutes] = explode(':', $time);
    return intval($hours) * 60 + intval($minutes);
}
```

### Example Scenarios
| Existing Approved | New Request | Result |
|-------------------|-------------|--------|
| Motor Tosa: 2026-10-10 08:00-12:00 | Motor Tosa: 2026-10-10 10:00-14:00 | **CONFLICT** (date + time overlap) |
| Motor Tosa: 2026-10-10 08:00-12:00 | Motor Tosa: 2026-10-10 14:00-18:00 | **OK** (no time overlap) |
| Motor Tosa: 2026-10-10 08:00-12:00 | Motor Tosa: 2026-10-11 08:00-12:00 | **OK** (different date) |
| Motor Tosa: 2026-10-10 08:00-12:00 | Motor Tosa: 2026-10-09 20:00-23:00 | **OK** (different date) |
| Motor Tosa: 2026-10-10 08:00-12:00 | Motor Tosa: 2026-10-10 06:00-09:00 | **CONFLICT** (09:00 overlaps) |

---

## Integration Points (Dual Enforcement)

The service is called in **two distinct places** with different behaviors:

### 1. At Submission Time (`BookingController::store`)
```php
$conflictCheck = $this->conflictService->checkConflict(...);

// Booking is STILL CREATED as 'pending'
return response()->json([
    'message' => 'Peminjaman berhasil dibuat',
    'booking' => $booking,
    'has_conflict' => $conflictCheck['hasConflict'],
    'conflict_warning' => $conflictCheck['hasConflict'] ? $conflictCheck['message'] : null,
], 201);
```
- **Behavior**: Warning only. User can still submit, frontend shows warning badge.

### 2. At Approval Time (`BookingController::updateStatus`)
```php
if ($validated['status'] === 'approved') {
    $conflictCheck = $this->conflictService->checkConflict(
        $booking->bookable_id,
        $booking->bookable_type,
        $booking->date_from->format('Y-m-d'),
        $booking->date_to->format('Y-m-d'),
        $booking->time_from ? $booking->time_from->format('H:i') : '00:00',
        $booking->time_to ? $booking->time_to->format('H:i') : '23:59',
        $booking->id  // Exclude this booking from check
    );

    if ($conflictCheck['hasConflict']) {
        return response()->json([
            'message' => 'Gagal menyetujui peminjaman: Terjadi bentrok jadwal.',
            'conflict_detail' => $conflictCheck['message'],
            'conflicts' => $conflictCheck['conflicts'],
        ], 422); // UNPROCESSABLE ENTITY
    }
}
```
- **Behavior**: BLOCKS approval. Returns 422 with detailed conflict info for admin UI.

---

## Frontend Integration

### User Dashboard (BookingForm.vue)
```javascript
const submitBooking = async () => {
  const res = await apiClient.post('/bookings', formData)
  if (res.data.has_conflict) {
    // Show warning alert but don't block
    showAlert(res.data.conflict_warning, 'warning')
  }
  // Proceed to booking history
}
```

### Admin Dashboards (AdminDashboard.vue / UnitAdminDashboard.vue)
```javascript
const updateStatus = async (id, status) => {
  try {
    await apiClient.patch(`/bookings/${id}/status`, { status })
    showAlert('Berhasil', 'success')
    await fetchData()
  } catch (e) {
    // 422 conflict response handling
    const msg = e.response?.data?.conflict_detail || e.response?.data?.message
    showAlert(msg, 'error')
  }
}
```

---

## Test Results (Verified)

Run these test cases to verify implementation:

```bash
# Facility test: same date, different time → 422 on approve
# Vehicle test: same date, overlapping time → 422 on approve
```

Both test scenarios passed with the exact response structure above.

---

## Migration Note

If extending to new booking types (e.g., recurring bookings), add new `checkXxxConflict` method and update `checkConflict` dispatcher. Keep the service stateless and injectable.