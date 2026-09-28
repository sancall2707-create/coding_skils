# Anonymous Session Token Authentication (SHA-256)

## Pattern
Used for no-login guest/student sessions (e.g., educational games).

### Client-side (JavaScript)
```js
// Generate 32-byte random token
const bytes = new Uint8Array(32);
crypto.getRandomValues(bytes);
const rawToken = Array.from(bytes).map(b => b.toString(16).padStart(2,'0')).join('');

// Compute SHA-256 hash to send to server
const encoder = new TextEncoder();
const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(rawToken));
const hashHex = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2,'0')).join('');
```

Send `hashHex` as `session_token_hash` when creating the session. Store `rawToken` only in `localStorage` (e.g., `mpd_active_session`).

### Server-side (Laravel)
```php
// In SessionAuth service
public static function hashSessionToken(string $rawToken): string
{
    return hash('sha256', $rawToken);
}

public static function verifySessionToken(string $rawToken, string $storedHash): bool
{
    return hash_equals($storedHash, self::hashSessionToken($rawToken));
}

public static function authenticate(?int $sessionId, ?string $rawToken): array
{
    if (empty($sessionId) || empty($rawToken)) {
        return ['session' => null, 'status' => 400, 'error' => 'Missing session_id or session_token'];
    }
    $session = GameSession::find($sessionId);
    if (!$session) {
        return ['session' => null, 'status' => 404, 'error' => 'Session not found'];
    }
    if (!self::verifySessionToken($rawToken, $session->session_token_hash)) {
        return ['session' => null, 'status' => 403, 'error' => 'Invalid token'];
    }
    return ['session' => $session, 'status' => null, 'error' => null];
}
```

All student functions must call `SessionAuth::authenticate()` first and return the provided status/error if not null.

### Security notes
- Raw token never leaves the device; only its hash is stored server-side.
- Token is 256-bit (32 bytes) – cryptographically strong.
- Use `hash_equals` for timing-safe comparison.
- "Bukan Saya" flow: delete only localStorage entry; keep server session intact for teacher review.