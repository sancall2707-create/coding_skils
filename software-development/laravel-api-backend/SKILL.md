---
name: laravel-api-backend
aliases: [laravel-backend-api, laravel-api-development]
trigger: |
  User is building a Laravel REST API (JSON endpoints, CRUD operations, authentication, token-based access control, database relationships, polymorphic models, Sanctum auth integration, API endpoint testing).
  Typically follows laravel-vps-bootstrap (after environment & project setup).
description: |
  Full-stack Laravel API development: database schema design (migrations), Eloquent models with relationships (including polymorphic), API controllers with CRUD + authorization, route registration, Sanctum token auth, and endpoint testing via curl.
  Covers models → migrations → seeders → controllers → routes → auth integration → testing workflow.
---

# Laravel API Backend Development

Workflow for building a production-grade REST API in Laravel (11+). Assumes Laravel project already created & dependencies installed (see `laravel-vps-bootstrap` for setup).

## Trigger Conditions
- Building JSON API endpoints (CRUD for resources)
- Implementing model relationships (hasMany, belongsTo, polymorphic morphTo/morphMany)
- Token-based authentication (Sanctum / JWT)
- Database schema design (migrations)
- Authorization logic (admin/user roles, ownership checks)
- Testing API responses

## Workflow: Models → Migrations → Seeders → Controllers → Routes → Auth → Test

### Phase 1: Database Schema (Migrations)

**Steps:**
1. Create migrations for each resource table:
   ```bash
   php artisan make:migration create_<resource>_table
   php artisan make:migration add_<column>_to_<table>_table
   ```

2. Design schema in migration `up()` method:
   - Use `$table->id()` for primary key
   - `$table->foreignId('parent_id')->constrained()->onDelete('cascade')` for FK relationships
   - For polymorphic: `$table->string('bookable_type')` + `$table->unsignedBigInteger('bookable_id')`
   - Use `$table->enum('field', ['value1', 'value2'])` for constrained choices
   - Add `timestamps()` for created_at / updated_at

3. Run migrations:
   ```bash
   php artisan migrate
   ```

**Common columns:**
- `$table->boolean('is_active')->default(true)`
- `$table->string('status')->default('pending')`
- `$table->text('description')->nullable()`
- `$table->integer('quantity')->nullable()`

### Phase 2: Eloquent Models

**Steps:**
1. Create models:
   ```bash
   php artisan make:model <Resource>
   php artisan make:model <Resource> -m  # with migration
   ```

2. Define relationships in model:
   - `hasMany()` for 1:N
   - `belongsTo()` for N:1
   - `morphMany()` for polymorphic 1:N
   - `morphTo()` for polymorphic inverse (on the child model)

3. Add `$fillable` array & `$casts`:
   ```php
   protected $fillable = ['name', 'email', 'role', 'phone_number'];
   protected $casts = ['is_active' => 'boolean', 'quantity' => 'integer'];
   ```

4. Add helper methods:
   ```php
   public function isAdmin(): bool { return $this->role === 'admin'; }
   ```

**Example: Polymorphic Bookings Model**
```php
public function bookable()
{
    return $this->morphTo();
}
public function user()
{
    return $this->belongsTo(User::class);
}
public function category()
{
    return $this->belongsTo(Category::class);
}
```

### Phase 3: Database Seeders

**Steps:**
1. Create seeder:
   ```bash
   php artisan make:seeder <ResourceSeeder>
   ```

2. Use `firstOrCreate()` for idempotency:
   ```php
   Category::firstOrCreate(
       ['name' => 'Admin'],
       ['created_at' => now()]
   );
   ```

3. Run seeder:
   ```bash
   php artisan db:seed --class=<ResourceSeeder>
   ```

**Gotcha:** Use `firstOrCreate(['unique_field' => $value])` to avoid duplicate seed runs.

### Phase 4: API Controllers

**Steps:**
1. Create controllers:
   ```bash
   php artisan make:controller Api/<Resource>Controller --api
   ```

2. Implement resource methods:
   - `index()` — list all
   - `store()` — create new
   - `show()` — fetch one
   - `update()` — modify
   - `destroy()` — delete

3. Validate input:
   ```php
   $validated = $request->validate([
       'name' => 'required|string|max:255',
       'email' => 'required|email|unique:users',
       'is_active' => 'boolean',
   ]);
   ```

4. Load relationships in responses:
   ```php
   return response()->json([
       'resource' => $model->load(['relation1', 'relation2']),
   ]);
   ```

5. Add authorization checks:
   ```php
   if ($request->user()->id !== $resource->user_id && !$request->user()->isAdmin()) {
       return response()->json(['message' => 'Unauthorized'], 403);
   }
   ```

### Phase 5: API Routes & Sanctum Auth

**Critical step for Laravel 11+:**

1. Enable API routes:
   ```bash
   php artisan install:api --no-interaction
   ```
   This publishes `config/sanctum.php` and creates `routes/api.php`.

2. Verify `bootstrap/app.php` contains:
   ```php
   ->withRouting(
       web: __DIR__.'/../routes/web.php',
       api: __DIR__.'/../routes/api.php',
       ...
   )
   ```

3. Register routes in `routes/api.php`:
   ```php
   Route::post('/login', [AuthController::class, 'login']);  // Public
   
   Route::middleware('auth:sanctum')->group(function () {
       Route::get('/me', [AuthController::class, 'me']);
       Route::apiResource('bookings', BookingController::class);
   });
   ```

4. Add `HasApiTokens` trait to User model:
   ```php
   use Laravel\Sanctum\HasApiTokens;
   class User extends Authenticatable { use HasApiTokens; }
   ```

5. Cache routes after changes:
   ```bash
   php artisan route:cache
   ```

### Phase 6: Authentication (Sanctum)

**Login endpoint:**
```php
public function login(Request $request)
{
    $request->validate(['email' => 'required|email', 'password' => 'required']);
    $user = User::where('email', $request->email)->first();
    
    if (!$user || !Hash::check($request->password, $user->password)) {
        throw ValidationException::withMessages(['email' => 'Invalid credentials']);
    }
    
    $token = $user->createToken('api-token')->plainTextToken;
    return response()->json(['token' => $token, 'user' => $user]);
}
```

**Protected endpoints:**
```
Authorization: Bearer <token>
```

### Phase 7: Backend Functions / RPC Layer for Server-Side Game Logic

Use this pattern when the API needs serverless/RPC-style functions: anonymous student sessions, hidden answer keys, server-only scoring, or Base44-style functions.

1. Keep controllers thin. Controllers validate HTTP shape, call one function class, then return `data` or `error` with the function's status code:
   ```php
   $result = SubmitAnswer::handle($sessionId, $token, $questionId, $answer);
   return response()->json($result['data'] ?? ['message' => $result['error']], $result['status']);
   ```

2. Put reusable helpers in `app/Services/`:
   - `SessionAuth`: `hashSessionToken()`, `verifySessionToken()`, `authenticate()` returning `session/status/error`.
   - `ClassTarget`: choose class-specific quiz before general quiz.
   - `SessionScoring`: dedupe answers, compute score, persist results, build review list.

3. Put RPC functions in `app/Functions/`:
   - `LoadMissionContent`
   - `SubmitAnswer`
   - `FinalizeSession`
   - `GetSessionReview`

4. Enforce security in every student function:
   - Missing required params -> `400`
   - Missing session/model -> `404`
   - Token hash mismatch -> `403`
   - Never expose answer keys in student load payloads (`is_correct`, `pair_key`, `order_value`, `explanation`) before completion.

5. Make writes idempotent:
   - Before saving an answer, check existing `(game_session_id, question_id)`.
   - Return existing result with `already_answered: true`.
   - Points count once per question per session.

6. Finalization pattern:
   - Ensure all required mission questions are answered.
   - Score formula: `round(20 + (earned_points / max_points) * 80)`, clamp `20..100`.
   - Save `StudentResult` and `CompetencyResult`, then mark session `completed`.
   - Make finalization idempotent; if already completed, return existing result.

7. Add security feature tests:
   - Wrong token returns `403`.
   - Review before completion returns `400`.
   - Student mission payload does not contain answer keys/explanations.
   - Duplicate answer saves only one `StudentAnswer`.
   - Finalize before all questions answered returns `400`.
   - Happy path covers full student flow plus teacher dashboard endpoints.

### Phase 8: Test Endpoints & Public Preview

**Public Tunneling for User Testing:**
When the user asks for a public test link after app development on a VPS:
```bash
# Start background server
php artisan serve --host=127.0.0.1 --port=8000 &

# Create temporary public URL via Cloudflare Tunnel
cloudflared tunnel --url http://127.0.0.1:8000
```
Extract `https://xxx.trycloudflare.com` from the logs and provide it to the user.

**Public route:**
```bash
curl -s http://localhost/api/categories | jq .
```

**Login:**
```bash
curl -s -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' | jq -r '.token'
```

**Protected route (with token):**
```bash
TOKEN=$(curl -s -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' | jq -r '.token')

curl -s http://localhost/api/me \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Create resource:**
```bash
curl -s -X POST http://localhost/api/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"category_id":2,"date_from":"2026-10-01",...}' | jq .
```

## Pitfalls & Troubleshooting

### 1. API Routes Not Found (404)
**Cause:** `php artisan install:api` was skipped or `bootstrap/app.php` doesn't register `api:` route file.
**Fix:**
```bash
php artisan install:api --no-interaction
# Verify routes/api.php exists
cat bootstrap/app.php | grep "api:"
php artisan route:list | grep api
```

### 2. Routes Not Updated After Edits
**Cause:** Route cache is stale.
**Fix:**
```bash
php artisan route:cache  # Regenerate
# or during development: php artisan route:clear
```

### 3. "Route api/resource not found"
**Cause:** Middleware `auth:sanctum` blocking access without token, or route not registered.
**Fix:**
- Public routes must be OUTSIDE `Route::middleware('auth:sanctum')->group()`
- Verify route file is explicitly imported in bootstrap/app.php

### 4. Polymorphic Relationship Returns Null
**Cause:** `bookable_type` column has wrong fully-qualified namespace (e.g., missing backslashes).
**Fix:** Ensure migration uses exact strings:
```php
$table->string('bookable_type');  // Will store: "App\Models\Vehicle"
// Not: "App\\Models\\Vehicle"
```
And in controller, use proper escaping:
```php
'bookable_type' => 'App\\Models\\Vehicle'
```

### 5. Seeder Not Creating Records (firstOrCreate Silent)
**Cause:** Duplicate key exists; firstOrCreate found match and skipped.
**Fix:**
```bash
php artisan migrate:fresh --seed  # Wipe & reseed
# or manually delete conflicting records
mysql> TRUNCATE categories;
php artisan db:seed
```

### 6. Mixed Content / Blank Screen Behind Reverse Proxy or Cloudflare Tunnel
**Cause:** Laravel generates `http://` asset/API URLs because reverse proxy/tunnel (Cloudflare Tunnel, ngrok, Nginx) isn't forced to HTTPS, causing browser Mixed Content blocking.
**Fix:** Force HTTPS in `app/Providers/AppServiceProvider.php`:
```php
use Illuminate\Support\Facades\URL;

public function boot(): void
{
    if ($this->app->environment('production') || request()->header('x-forwarded-proto') === 'https' || str_contains(config('app.url'), 'https://')) {
        URL::forceScheme('https');
    }
}
```

### 7. Anonymous Session Auth (No Login / LocalStorage + Hashed Token)
**Pattern:** Client generates 32-byte raw token via Web Crypto (`crypto.getRandomValues`), calculates SHA-256 hash (`crypto.subtle.digest`), sends ONLY the hash to backend `GameSession`. Client retains raw token in `localStorage`. All student requests carry raw token; backend verifies via `hash_equals(stored_hash, hash('sha256', raw_token))`.

### 6. SQLite "table users has no column named X" During Seeding
**Cause:** Scaffolding or initial migrations were run before adding new columns (e.g. `role` in users table). SQLite tables were already created with old schema.
**Fix:**
```bash
php artisan migrate:fresh --seed
```

### 7. BadMethodCallException: `HasMany::last()`
**Cause:** Calling Collection methods directly on an Eloquent relation builder, e.g. `$quiz->questions()->last()`.
**Fix:** evaluate to a collection first or use query-builder ordering:
```php
$lastQuestion = $quiz->questions()
    ->orderBy('difficulty', 'asc')
    ->orderBy('id', 'asc')
    ->get()
    ->last();

// or query-builder style
$lastQuestion = $quiz->questions()->latest('id')->first();
```

### 8. Vite Manifest Missing After React Entry Rename
**Cause:** Laravel Blade or compiled view cache still references `resources/js/app.js` after converting entry to `resources/js/app.jsx`.
**Fix:** keep `vite.config.js` input and Blade `@vite()` aligned, then rebuild and clear caches:
```bash
npm run build
php artisan view:clear
php artisan route:clear
php artisan config:clear
```

## Support Files

See `references/` for:
- `polymorphic-booking-pattern.md` — Full example of Vehicle/Facility morphMany + Booking morphTo
- `sanctum-auth-checklist.md` — Step-by-step Sanctum setup verification
- `curl-api-test-examples.md` — Copy-paste curl commands for testing
- `misi-pintar-digital-schema.md` — Laravel schema/seeder pattern for anonymous-student educational game apps with teacher dashboard
- `educational-game-api-pattern.md` — Anonymous student token auth, server-side scoring, and teacher dashboard API architecture
- `anonymous-session-token-auth.md` — Client-generated 32-byte token + SHA-256 hash pattern for no-login sessions
- `educational-game-frontend-pattern.md` — React/Vite frontend architecture, DESIGN.md token integration, student game loop, teacher dashboard, certificate PDF, and Cloudflare Tunnel HTTPS fix

See `templates/` for:
- `crud-controller-scaffold.php` — Starter CRUD controller
- `migration-booking-template.php` — Polymorphic booking migration
- `seeders/database-seeder-template.php` — Idempotent seeder pattern

See `scripts/` for:
- `test-auth-endpoints.sh` — Automated API endpoint tester (login → GET protected → POST booking)

## Related Skills
- `laravel-vps-bootstrap` — Environment setup, PHP/MariaDB/Composer/Laravel installation
- `systematic-debugging` — Debug API responses, validation errors, auth failures
- `test-driven-development` — Test-first API development with Feature/Unit tests

## Notes
- This skill assumes Laravel 11+ (routes registration via bootstrap/app.php)
- For Laravel 10 and earlier, routes are in `config/api.php` or explicitly imported in `routes/web.php`
- Sanctum tokens are bearer-token based (not JWT, but similar UX)
- Polymorphic relationships are powerful for booking/reservation systems (single table, multiple resource types)
