---
name: laravel-sanctum-rbac
title: Laravel Sanctum Token Auth + Policy-Based RBAC
trigger: |
  Building a Laravel API with role-based access control (admin/user/custom roles).
  Implementing Sanctum for SPA token authentication.
  Protecting API endpoints based on user roles and resource ownership.
  Designing authorization logic that forces role assignment on self-registration.
description: |
  Complete pattern for setting up Laravel Sanctum token-based authentication paired with Policy classes for role-based access control (RBAC). Covers forced role assignment during registration, Gate-based authorization in controllers, and testing RBAC with curl. Suitable for PWA backends and REST APIs.
---

# Laravel Sanctum + Policy-Based RBAC Pattern

## Overview

Build a Laravel API with **Sanctum token authentication** and **Laravel Policy classes** for authorization. Key features:
- Sanctum for stateless API token auth (SPA-friendly)
- Policy classes for resource-level authorization (not just role checks)
- Forced role assignment on self-registration (security best practice)
- Gate authorization in controllers to check policies
- Testing RBAC via curl with Bearer tokens

---

## Quick Setup (5 Steps)

### 1. Install Sanctum
```bash
composer require laravel/sanctum
php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider"
php artisan migrate
```

### 2. Add HasApiTokens Trait to User Model
```php
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable {
    use HasApiTokens, HasFactory, Notifiable;
}
```

### 3. Create Policy Classes
```bash
php artisan make:policy BookingPolicy --model=Booking
php artisan make:policy ItemPolicy --model=Item  # e.g., Vehicle/Facility
```

### 4. Create Auth Controller with Sanctum Token Generation
```php
// In AuthController@register (force role='user' on self-registration)
$user = User::create([
    'email' => $validated['email'],
    'password' => Hash::make($validated['password']),
    'role' => 'user',  // FORCED — cannot be overridden by user input
]);
$token = $user->createToken('api-token')->plainTextToken;
return response()->json(['token' => $token, 'user' => $user], 201);
```

### 5. Use Gate in Controllers to Authorize
```php
// In BookingController@update
Gate::authorize('update', $booking);  // Checks BookingPolicy@update
```

---

## Policies: Authorization Logic

### Pattern: Role Check + Ownership Check

```php
// app/Policies/BookingPolicy.php
class BookingPolicy {
    public function view(User $user, Booking $booking): bool {
        return $user->isAdmin() || $user->id === $booking->user_id;
    }

    public function update(User $user, Booking $booking): bool {
        // User can edit own booking if pending; admin can edit all
        return $user->isAdmin() || 
               ($user->id === $booking->user_id && $booking->status === 'pending');
    }

    public function updateStatus(User $user, Booking $booking): bool {
        // Only admin can approve/reject
        return $user->isAdmin();
    }
}
```

### Pattern: Admin-Only Resources

```php
// app/Policies/VehiclePolicy.php
class VehiclePolicy {
    public function create(User $user): bool {
        return $user->isAdmin();  // Only admin can create
    }

    public function update(User $user, Vehicle $vehicle): bool {
        return $user->isAdmin();
    }

    public function delete(User $user, Vehicle $vehicle): bool {
        return $user->isAdmin();
    }
}
```

---

## API Routes with auth:sanctum Middleware

```php
// routes/api.php
Route::post('/register', [AuthController::class, 'register']);  // Public
Route::post('/login', [AuthController::class, 'login']);        // Public

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', [AuthController::class, 'me']);

    // Protected resources
    Route::post('/bookings', [BookingController::class, 'store']);
    Route::get('/bookings/{booking}', [BookingController::class, 'show']);
    Route::put('/bookings/{booking}', [BookingController::class, 'update']);
    Route::delete('/bookings/{booking}', [BookingController::class, 'destroy']);
    Route::patch('/bookings/{booking}/status', [BookingController::class, 'updateStatus']);

    // Admin-only
    Route::post('/items', [ItemController::class, 'store']);  // Admin only
    Route::put('/items/{item}', [ItemController::class, 'update']);  // Admin only
});
```

---

## Controller Pattern: Using Gate + Policy

```php
public function update(Request $request, Booking $booking) {
    // This calls BookingPolicy@update($request->user(), $booking)
    // Raises 403 Forbidden if policy returns false
    Gate::authorize('update', $booking);

    $booking->update($request->validated());
    return response()->json(['booking' => $booking->load('relations')]);
}

public function index(Request $request) {
    $user = $request->user();

    // Admin sees all; regular users see only their own
    $query = Booking::query();
    if (!$user->isAdmin()) {
        $query->where('user_id', $user->id);
    }

    return response()->json(['bookings' => $query->get()]);
}
```

---

## Forced Role on Self-Registration (Security Best Practice)

```php
public function register(Request $request) {
    $validated = $request->validate([
        'name' => 'required|string|max:255',
        'email' => 'required|email|unique:users',
        'password' => ['required', 'confirmed', Password::defaults()],
    ]);

    // STRICT: self-registered users ALWAYS get role='user'
    // Even if caller sends "role":"admin", it is ignored/overridden
    $user = User::create([
        'name' => $validated['name'],
        'email' => $validated['email'],
        'password' => Hash::make($validated['password']),
        'role' => 'user',  // FORCED — not from $validated
    ]);

    $token = $user->createToken('api-token')->plainTextToken;
    return response()->json(['token' => $token, 'user' => $user], 201);
}
```

**Rationale**: Prevents users from self-promoting to admin. Admin role is assigned only by database seeding or manual admin panel.

---

## Testing RBAC with Curl + Bearer Token

### Test 1: Register & Get Token
```bash
curl -X POST http://localhost/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"User","email":"user@test.com","password":"Pass123!","password_confirmation":"Pass123!"}'
# Response: {"token":"1|abc...", "user":{"role":"user"}}
```

### Test 2: Verify Token Works (Protected Route)
```bash
TOKEN="1|abc..."
curl -X GET http://localhost/api/me \
  -H "Authorization: Bearer $TOKEN"
# Response: {"user": {...}}
```

### Test 3: User Unauthorized for Admin Action (403 Forbidden)
```bash
curl -X POST http://localhost/api/vehicles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Vehicle","plate":"B 1234 PL"}'
# Response: 403 Forbidden
```

### Test 4: Admin Can Do Admin Action (201 Created)
```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}' | jq -r '.token')

curl -X POST http://localhost/api/vehicles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Vehicle","plate":"B 1234 PL"}'
# Response: 201 Created
```

---

## Pitfalls & Common Mistakes

1. **Forgetting to call Gate::authorize() in controller**
   - Policy is written but never checked in the controller
   - **Fix**: Explicitly call `Gate::authorize('action', $resource)` before performing action

2. **Checking `$user->role === 'admin'` instead of Policy**
   - Works for simple cases but doesn't scale; policies are more maintainable
   - **Fix**: Use Policy classes for resource-level checks, not raw role comparisons

3. **Self-registration with user-controlled role**
   - Allows privilege escalation: `{"role":"admin"}` in payload
   - **Fix**: Always force role on self-registration, never read from $validated

4. **Forgetting Sanctum middleware on routes**
   - Routes not protected by `auth:sanctum` allow unauthenticated access
   - **Fix**: Wrap protected routes in `Route::middleware('auth:sanctum')->group(...)`

5. **Testing auth without Bearer token**
   - curl without `-H "Authorization: Bearer $TOKEN"` returns 401 Unauthorized
   - **Fix**: Always include Authorization header for protected routes

6. **Policy class not registered**
   - Policy file exists but Laravel doesn't auto-discover it
   - **Fix**: Define policy in `app/Providers/AuthServiceProvider.php` if not using convention
