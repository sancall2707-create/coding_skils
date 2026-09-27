# Sanctum API Auth Checklist & Troubleshooting

## Prerequisites Checklist
- [x] Package installed: `composer require laravel/sanctum`
- [x] Vendor published: `php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider"`
- [x] Migration ran: `php artisan migrate` (creates `personal_access_tokens` table)
- [x] User model updated: Added `use Laravel\Sanctum\HasApiTokens;` trait to `App\Models\User`
- [x] API routes registered: `php artisan install:api --no-interaction`
- [x] Route group wrapped: `Route::middleware('auth:sanctum')->group(...)`

## Common Sanctum Issues & Fixes

### Issue 1: "Unauthenticated." (401) on Protected Endpoint
- **Cause**: Missing `Authorization` header or token is invalid/revoked.
- **Fix**: Format header as `Authorization: Bearer <plainTextToken>`.
- **Note**: `plainTextToken` is returned upon `$user->createToken('token-name')->plainTextToken`.

### Issue 2: Call to undefined method `createToken()`
- **Cause**: `HasApiTokens` trait not added to `User` model.
- **Fix**: Add `use HasApiTokens;` in `app/Models/User.php`.

### Issue 3: Table `personal_access_tokens` does not exist
- **Cause**: Migration was skipped.
- **Fix**: `php artisan migrate`.

## Minimal Auth Controller Pattern

```php
namespace App\Http\Controllers\Api;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController
{
    public function login(Request $request)
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['Invalid credentials.'],
            ]);
        }

        $token = $user->createToken('api-token')->plainTextToken;

        return response()->json([
            'message' => 'Login successful',
            'token' => $token,
            'user' => $user,
        ]);
    }

    public function me(Request $request)
    {
        return response()->json([
            'user' => $request->user(),
        ]);
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json([
            'message' => 'Token revoked successfully',
        ]);
    }
}
```
