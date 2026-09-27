---
name: laravel-vue-pwa-fullstack
title: Laravel 11 + Vue 3 PWA Full-Stack Development
trigger: |
  User is building a full-stack web application combining Laravel backend (API), Vue 3 frontend (SPA), and PWA features (Manifest + Service Worker). Typically involves:
  - Database schema design & migrations
  - API endpoints (Sanctum auth, CRUD, business logic)
  - Complex service patterns (e.g., conflict checking, state management)
  - Role-based frontend & backend authorization
  - Vue 3 SPA with routing, stores (Pinia), and HTTP client (axios)
  - Tailwind CSS responsive UI
  - Vite build process
description: |
  Full workflow for building a production-ready Laravel + Vue 3 PWA application with role-based access control, complex business logic services, and modern frontend tooling. Optimized for incremental, sequential implementation (no upfront mega-planning). Includes debugging patterns for common build & API testing issues.
---

## 1. DEVELOPMENT PHASES (Sequential Workflow)

Execute in strict order. Minimize planning; validate each phase before moving forward.
- See `references/pwa-deployment-patterns.md` for PWA manifest, service worker security rules, and Cloudflare Tunnel HTTPS setup.
- See `references/https-proxy-pwa-diagnosis.md` for HTTPS proxy pitfalls, mixed-content fixes, and real-diagnosis methodology.
- See `references/conflict-checking-rules.md` for full-date facility and time-overlapping vehicle conflict service rules.
- See `references/vue-template-errors.md` for Vue template compilation traps.

### Phase 1: Backend Foundation
- **Laravel setup**: `composer create-project laravel/laravel app`, `php artisan key:generate`
- **Database**: Migrations for all core tables (users, items, bookings, etc.)
- **Models**: Define relationships (hasMany, morphMany, belongsTo, etc.) — test via tinker
- **Sanctum**: `composer require laravel/sanctum`, `php artisan vendor:publish`, `php artisan migrate`
- **Add `HasApiTokens` to User model**
- **Seeding**: DatabaseSeeder with realistic initial data

### Phase 2: API Layer
- **Controllers**: Create API controllers for each resource
- **Routes**: Register routes in `routes/api.php`, wrap with Sanctum middleware where needed
- **Form Requests / Validation**: Define request classes; validate in controller actions
- **Policies / Gate**: Define authorization rules (who can view, create, update, delete)
- **Test API endpoints**: Use `curl` or Python `execute_code` with real tokens (see below for pattern)

### Phase 3: Complex Business Logic Services
- Create `app/Services/` directory
- Implement domain-specific services (conflict checking, approval workflows, etc.)
- **Inject services** into controllers via constructor DI
- **Test services independently** before wiring to controllers
- Keep services **stateless and reusable**

### Phase 4: Frontend Setup
- **Vite + Vue 3**: Already scaffolded by Laravel; install deps (`npm install`)
- **Tailwind CSS**: `npm install -D tailwindcss postcss autoprefixer`, init configs
- **Pinia stores**: `npm install pinia`, define state + actions for (auth, data, UI)
- **Vue Router**: `npm install vue-router`, define routes with meta guards (requiresAuth, requiresAdmin)
- **Axios HTTP client**: Service module (`resources/js/services/api.js`) with interceptors for auth tokens

### Phase 5: Frontend Pages & Components
- **Build auth pages** first (Login, Register) — tie to Pinia auth store
- **User dashboard**: Query API, display data, navigation to other sections
- **CRUD pages**: Lists, forms, detail views — bind to stores + API
- **Admin dashboards**: Filter/display based on role — use computed properties for authorization
- **Error handling**: Show alerts for validation, conflict errors, network failures

### Phase 6: Router & Navigation
- **Route guards**: Check `meta.requiresAuth`, `meta.requiresAdmin` in `beforeEach`
- **Redirect logic**: Unauthenticated → Login; non-admin → Dashboard; admin → Admin Dashboard
- **Navbar**: Conditional links based on `authStore.isAdmin` / `authStore.isAuthenticated`
- **404 fallback**: Catch-all route redirects to "/"

### Phase 7: Build & Deployment
- **CSS + JS bundling**: `npm run build` → outputs to `public/build/`
- **PWA setup**: Add `manifest.json` to `public/`, register Service Worker in Blade template
- **Web server**: Point to `public/index.php` (e.g., Caddy reverse proxy to PHP-FPM)
- **Verify**: Test login flow, role-based access, API calls, offline support

---

## 2. ROLE-BASED AUTHORIZATION PATTERNS

### Backend (Laravel Policies)
```php
// app/Policies/BookingPolicy.php
public function view(User $user, Booking $booking): bool {
  return $user->isAdmin() || $booking->user_id === $user->id;
}

public function updateStatus(User $user, Booking $booking): bool {
  return $user->isAdmin(); // Only admin can change status
}
```

**Apply in controller:**
```php
public function update(Request $req, Booking $booking) {
  Gate::authorize('update', $booking);
  // ... proceed
}
```

### Frontend (Vue 3 + Pinia)
```javascript
// stores/auth.js
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
  }),
  getters: {
    isAdmin: (state) => state.user?.role === 'admin',
  },
})

// In component:
<button v-if="authStore.isAdmin" @click="approve()">Approve</button>
```

**Router guard:**
```javascript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Dashboard' })
    return
  }
  next()
})
```

---

## 3. COMPLEX SERVICE PATTERN (Conflict Checking Example)

Create stateless, injectable services in `app/Services/`. Example: booking conflict checking with two rule sets.

```php
// app/Services/BookingConflictService.php
class BookingConflictService {
  public function checkConflict(
    int $bookableId,
    string $bookableType, // 'App\Models\Vehicle' or 'App\Models\Facility'
    string $dateFrom,
    string $dateTo,
    ?string $timeFrom = null,
    ?string $timeTo = null,
    ?int $excludeBookingId = null
  ): array {
    // Dispatch to type-specific logic
    if ($this->isFacility($bookableType)) {
      return $this->checkFacilityConflict(...);
    } else {
      return $this->checkVehicleConflict(...);
    }
  }

  private function checkFacilityConflict(...): array {
    // Full-date check: if facility already booked on ANY date in range, conflict
    // Return ['hasConflict' => bool, 'conflicts' => [...], 'message' => string]
  }

  private function checkVehicleConflict(...): array {
    // Time-overlap check: date AND time must overlap
  }

  private function isTimeOverlapping($start1, $end1, $start2, $end2): bool {
    // Helper: convert H:i to minutes, compare ranges
  }
}
```

**Inject & use in controller:**
```php
public function __construct(BookingConflictService $conflictService) {
  $this->conflictService = $conflictService;
}

public function store(Request $req) {
  // Check at submission time (warn user)
  $conflict = $this->conflictService->checkConflict(...);
  $booking = Booking::create($validated);
  return response()->json([
    'booking' => $booking,
    'has_conflict' => $conflict['hasConflict'],
    'conflict_warning' => $conflict['message'] ?? null,
  ]);
}

public function updateStatus(Request $req, Booking $booking) {
  if ($req->status === 'approved') {
    // Check at approval time (BLOCK if conflict)
    $conflict = $this->conflictService->checkConflict(...);
    if ($conflict['hasConflict']) {
      return response()->json([...], 422); // Unprocessable Entity
    }
  }
  $booking->update(['status' => $req->status]);
  return response()->json(['booking' => $booking]);
}
```

---

## 4. API TESTING PATTERN (Python + execute_code)

When testing complex API flows with state (login → create resource → modify → verify), use Python in `execute_code` block instead of shell curl. Easier token management, JSON parsing, and control flow.

```python
import subprocess
import json

BASE_URL = "http://localhost/api"

def api_call(method, endpoint, token=None, data=None):
  cmd = ["curl", "-s", "-X", method, f"{BASE_URL}{endpoint}"]
  cmd.extend(["-H", "Content-Type: application/json"])
  if token:
    cmd.extend(["-H", f"Authorization: Bearer {token}"])
  if data:
    cmd.extend(["-d", json.dumps(data)])
  result = subprocess.run(cmd, capture_output=True, text=True)
  return json.loads(result.stdout)

# Test flow
admin_resp = api_call("POST", "/login", data={"email": "admin@...", "password": "..."})
admin_token = admin_resp["token"]

# Create booking
booking_resp = api_call("POST", "/bookings", admin_token, {...})
booking_id = booking_resp["booking"]["id"]

# Attempt approval (may fail with 422 if conflict)
approve_resp = api_call("PATCH", f"/bookings/{booking_id}/status", admin_token, {"status": "approved"})
print(json.dumps(approve_resp, indent=2))
```

---

## 5. COMMON PITFALLS & FIXES

### Vue Build Errors: v-else/v-else-if Without Preceding v-if
**Symptom**: `SyntaxError: v-else/v-else-if has no adjacent v-if or v-else-if.`

**Fix**: Use `<template v-if>` wrapper for multi-element conditionals.
```vue
<!-- WRONG: v-else not adjacent to v-if -->
<header v-if="auth">...</header>
<main><!-- other content --></main>
<footer v-else>...</footer> <!-- ERROR -->

<!-- RIGHT: Both in same if/else branch -->
<template v-if="auth">
  <header>...</header>
  <main>...</main>
</template>
<template v-else>
  <footer>...</footer>
</template>
```

### Build Hangs on npm run build
**Symptom**: `npm run build` appears to start a long-lived process and times out.

**Fix**: Run with `execute_code` subprocess instead of terminal; set timeout (e.g., 60s). Capture stderr for real error messages.

### Token Expiry During Multi-Step API Tests
**Symptom**: First API call succeeds (login), but second call returns 401.

**Cause**: Tokens may be short-lived; tests run too slowly or in separate curl invocations.

**Fix**: Keep token in same Python script, re-fetch if needed. Don't rely on shell history across separate `curl` commands.

### Cascading Deletion / Foreign Key Conflicts
**Symptom**: Cannot delete user or resource; foreign key constraint error.

**Fix**: Add `onDelete('cascade')` or `onDelete('set null')` to migrations:
```php
$table->foreignId('user_id')->constrained()->onDelete('cascade');
```

---

## 6. FILE STRUCTURE

```
app/
├── app/
│   ├── Models/
│   │   ├── User.php (+ HasApiTokens trait)
│   │   ├── Booking.php (morphTo/morphMany relationships)
│   │   └── ...
│   ├── Http/Controllers/Api/
│   │   ├── AuthController.php
│   │   ├── BookingController.php
│   │   └── ...
│   ├── Services/
│   │   └── BookingConflictService.php (stateless, injectable)
│   ├── Policies/
│   │   ├── BookingPolicy.php
│   │   └── ...
│   └── ...
├── database/
│   ├── migrations/
│   │   ├── ...create_bookings_table.php
│   │   └── ...
│   └── seeders/
│       └── DatabaseSeeder.php
├── routes/
│   ├── api.php (Sanctum-protected endpoints)
│   └── web.php (Blade routes for SPA host)
├── resources/
│   ├── js/
│   │   ├── App.vue (root component, navbar, auth logic)
│   │   ├── app.js (entry point, Pinia + Router init)
│   │   ├── pages/
│   │   │   ├── Dashboard.vue
│   │   │   ├── AdminDashboard.vue
│   │   │   ├── Login.vue
│   │   │   └── ...
│   │   ├── stores/
│   │   │   ├── auth.js (Pinia: user, token, isAdmin)
│   │   │   ├── booking.js (Pinia: bookings, vehicles, facilities)
│   │   │   └── ...
│   │   ├── router/
│   │   │   └── index.js (routes + beforeEach guards)
│   │   ├── services/
│   │   │   └── api.js (axios instance + interceptors)
│   │   └── ...
│   ├── css/
│   │   └── app.css (@tailwind directives)
│   └── views/
│       └── welcome.blade.php (SPA host: <div id="app">)
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── ...
```

---

## 7. WORKFLOW PREFERENCES

- **Sequential over parallel**: Complete Phase 1 (DB + Models) before starting Phase 4 (Frontend). Validate each layer works before moving to next.
- **Minimal upfront planning**: Sketch the schema and API shape, then build incrementally. Refine based on actual testing.
- **Direct implementation**: Code first, document after. Validation gates each phase transition.
- **Test early & often**: Use Python API testing script after each controller is written. Catch conflicts and auth issues immediately.
