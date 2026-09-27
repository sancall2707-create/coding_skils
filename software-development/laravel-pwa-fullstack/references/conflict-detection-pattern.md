# Temporal & Spatial Conflict Detection Patterns

## Core Concept

Conflict detection is the enforcement of **resource availability constraints** before confirming a booking. Two distinct patterns are needed depending on the resource type:

| Resource Type | Conflict Logic | Real-World Analogy |
|---------------|----------------|-------------------|
| **Facilities / Rooms** | Full-Date Exclusion (any overlap on same date = conflict) | Aula booked for 2025-10-05 → entire day blocked |
| **Vehicles / Equipment** | Date-Range + Time-Range Overlap (must overlap in BOTH dimensions) | Motor 08:00-12:00 and 10:00-14:00 on same day = conflict |

---

## Pattern 1: Full-Date Exclusion (Facilities)

### Logic
```php
function checkFacilityConflict(int $facilityId, string $dateFrom, string $dateTo, ?int $excludeId = null): bool {
    return Booking::where('bookable_type', 'Facility')
        ->where('bookable_id', $facilityId)
        ->where('status', 'approved')
        ->when($excludeId, fn($q) => $q->where('id', '!=', $excludeId))
        ->where(function ($q) use ($dateFrom, $dateTo) {
            // Three overlap patterns:
            // 1. Existing starts during new range
            $q->whereBetween('date_from', [$dateFrom, $dateTo])
            // 2. Existing ends during new range
              ->orWhereBetween('date_to', [$dateFrom, $dateTo])
            // 3. Existing fully encloses new range
              ->orWhere(function ($sub) use ($dateFrom, $dateTo) {
                  $sub->where('date_from', '<=', $dateFrom)
                      ->where('date_to', '>=', $dateTo);
              });
        })
        ->exists();
}
```

### Why Three Patterns?
Visual representation of date ranges (new booking: `[D1-----D2]`):
```
Pattern 1:     [old---]       (old starts inside new)
Pattern 2:         [---old]   (old ends inside new)
Pattern 3: [-----------old-----------] (old completely covers new)
```

### Test Cases (Verified)
| Existing Approved | New Request | Conflict? |
|-------------------|-------------|-----------|
| 2025-10-05 to 2025-10-05 | 2025-10-05 to 2025-10-05 | ✅ YES |
| 2025-10-05 to 2025-10-07 | 2025-10-06 to 2025-10-06 | ✅ YES |
| 2025-10-03 to 2025-10-10 | 2025-10-05 to 2025-10-05 | ✅ YES |
| 2025-10-05 to 2025-10-05 | 2025-10-06 to 2025-10-06 | ❌ NO |

---

## Pattern 2: Date + Time Overlap (Vehicles)

### Logic
```php
function checkVehicleConflict(int $vehicleId, string $dateFrom, string $dateTo,
    string $timeFrom, string $timeTo, ?int $excludeId = null): bool {
    
    // First: Find date-overlapping bookings
    $candidates = Booking::where('bookable_type', 'Vehicle')
        ->where('bookable_id', $vehicleId)
        ->where('status', 'approved')
        ->when($excludeId, fn($q) => $q->where('id', '!=', $excludeId))
        ->where(function ($q) use ($dateFrom, $dateTo) {
            // Same three date patterns as facilities
            $q->whereBetween('date_from', [$dateFrom, $dateTo])
              ->orWhereBetween('date_to', [$dateFrom, $dateTo])
              ->orWhere(function ($sub) use ($dateFrom, $dateTo) {
                  $sub->where('date_from', '<=', $dateFrom)
                      ->where('date_to', '>=', $dateTo);
              });
        })
        ->get();

    // Second: Filter by TIME overlap (minute-based precision)
    return $candidates->contains(function ($booking) use ($timeFrom, $timeTo) {
        return $this->isTimeOverlapping($timeFrom, $timeTo, $booking->time_from, $booking->time_to);
    });
}

function isTimeOverlapping(string $s1, string $e1, string $s2, string $e2): bool {
    $s1m = $this->timeToMinutes($s1);  // "08:00" → 480
    $e1m = $this->timeToMinutes($e1);  // "12:00" → 720
    $s2m = $this->timeToMinutes($s2);  // "10:00" → 600
    $e2m = $this->timeToMinutes($e2);  // "14:00" → 840
    
    // Overlap if: start1 < end2 AND start2 < end1
    return $s1m < $e2m && $s2m < $e1m;
}
```

### Test Cases (Verified)
| Existing (Date, Time) | New Request (Date, Time) | Conflict? |
|-----------------------|--------------------------|-----------|
| 2025-10-10, 08:00-12:00 | 2025-10-10, 10:00-14:00 | ✅ YES (10-12 overlap) |
| 2025-10-10, 08:00-12:00 | 2025-10-10, 12:00-14:00 | ❌ NO (end=start, no overlap) |
| 2025-10-10, 08:00-12:00 | 2025-10-10, 06:00-09:00 | ✅ YES (08-09 overlap) |
| 2025-10-10, 08:00-12:00 | 2025-10-11, 08:00-12:00 | ❌ NO (different date) |

---

## Integration Pattern

### Dual-Point Enforcement (Critical)
Call conflict service at **BOTH** points:

```php
// 1. During USER SUBMISSION (store) — Return WARNING, allow pending creation
public function store(Request $request) {
    $conflict = $this->conflictService->check($validated);
    $booking = Booking::create($validated);
    
    return response()->json([
        'booking' => $booking,
        'has_conflict' => $conflict['hasConflict'],  // Frontend shows warning
        'conflict_warning' => $conflict['message'],
    ], 201);
}

// 2. During ADMIN APPROVAL (updateStatus) — BLOCK if conflict
public function updateStatus(Request $request, Booking $booking) {
    if ($request->status === 'approved') {
        $conflict = $this->conflictService->check($booking->attributes, $booking->id);
        if ($conflict['hasConflict']) {
            return response()->json([
                'message' => 'Conflict: cannot approve',
                'conflict_detail' => $conflict['message'],
            ], 422);  // HTTP 422 Unprocessable Entity
        }
    }
    $booking->update($validated);
    // ...
}
```

### Frontend Warning Pattern
```vue
<!-- Show warning banner but don't block submission -->
<div v-if="booking.has_conflict" class="bg-yellow-100 border-yellow-500 p-3 rounded">
  ⚠️ {{ booking.conflict_warning }}
</div>
```

---

## Database Indexing for Performance

```sql
-- Composite index for conflict query performance
CREATE INDEX idx_bookings_conflict_check 
ON bookings (bookable_type, bookable_id, status, date_from, date_to);

-- For time-based queries on vehicles
CREATE INDEX idx_bookings_time_check 
ON bookings (bookable_type, bookable_id, status, time_from, time_to);
```

---

## Edge Cases Handled

1. **Same-start, same-end** → Conflict (exact match)
2. **End equals start** → NO conflict (08:00-12:00 vs 12:00-14:00)
3. **New encloses existing** → Conflict
4. **Existing encloses new** → Conflict
5. **Multi-day ranges** → All days checked
6. **Self-exclusion on update** → Pass booking ID to exclude itself