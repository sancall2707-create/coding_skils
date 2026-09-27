# Vue 3 + Sanctum Troubleshooting Guide

## Common Issues & Fixes

### 1. Token Not Persisting on Page Refresh

**Symptom**: User logs in, but on page refresh, auth state is lost and user redirected to login.

**Root Cause**: Token stored in `sessionStorage` instead of `localStorage`.

**Fix**: Update Pinia auth store to use `localStorage`:

```javascript
// resources/js/stores/auth.js
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
    token: localStorage.getItem('auth_token') || null,
  }),
  actions: {
    setAuth(user, token) {
      this.user = user
      this.token = token
      localStorage.setItem('auth_user', JSON.stringify(user))
      localStorage.setItem('auth_token', token)
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('auth_user')
      localStorage.removeItem('auth_token')
    },
  },
})
```

---

### 2. 419 CSRF Token Mismatch on API Calls

**Symptom**: API requests return 419 Page Expired.

**Root Cause**: Sanctum expects `X-CSRF-TOKEN` header for stateful routes, but SPA uses token auth.

**Fix**: Ensure API routes use `sanctum` middleware, not `web` middleware:

```php
// routes/api.php
Route::middleware('auth:sanctum')->group(function () {
    // Protected routes here
});
```

And in `bootstrap/app.php` (Laravel 11):
```php
->withRouting(
    api: __DIR__.'/../routes/api.php',
    // ...
)
```

---

### 3. 401 Unauthorized After Token Expiry

**Symptom**: API calls silently fail with 401 after token expires.

**Fix**: Add Axios interceptor to auto-redirect on 401:

```javascript
// resources/js/services/api.js
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

---

### 4. Vite Build Error: "v-else has no adjacent v-if"

**Symptom**: Build fails with Vue compiler error about v-else without v-if.

**Root Cause**: Template structure issue - `v-else` must immediately follow `v-if` in same parent element.

**Fix**: Use `<template v-if>` wrapper instead of trying to else on sibling elements:

```vue
<!-- ❌ WRONG - breaks build -->
<div v-if="authStore.isAuthenticated">
  <header>...</header>
  <main>...</main>
</div>
<router-view v-else />

<!-- ✅ CORRECT - template wrapper -->
<template v-if="authStore.isAuthenticated">
  <header>...</header>
  <main>...</main>
</template>
<template v-else>
  <router-view />
</template>
```

---

### 5. CORS Issues on Local Development

**Symptom**: Browser blocks API calls due to CORS policy.

**Fix**: Configure CORS in `config/cors.php`:

```php
'paths' => ['api/*', 'sanctum/csrf-cookie'],
'allowed_methods' => ['*'],
'allowed_origins' => ['http://localhost:5173', 'http://127.0.0.1:5173'],
'allowed_headers' => ['*'],
'supports_credentials' => true,
```

Then run: `php artisan config:clear`

---

### 6. Service Worker Caching Login Page

**Symptom**: After logout, user still sees cached login page or sees stale data.

**Root Cause**: Service Worker caching sensitive routes.

**Fix**: Implement Network-only for auth routes (see `references/service-worker-security.md`):

```javascript
// In sw.js fetch handler - Network Only for auth
if (
  url.pathname.includes('login') ||
  url.pathname.includes('register') ||
  url.pathname.startsWith('/api/') ||
  event.request.method !== 'GET'
) {
  event.respondWith(fetch(event.request))
  return
}
```

---

### 7. PWA Install Prompt Not Showing

**Symptom**: `beforeinstallprompt` never fires on mobile.

**Checklist**:
- [ ] HTTPS enabled (or localhost)
- [ ] Valid manifest.json with icons
- [ ] Service Worker registered
- [ ] Site meets engagement criteria (user interaction required)
- [ ] Not already installed

**Fix**: Add explicit check in mount:

```javascript
onMounted(() => {
  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches) {
    showInstallPrompt.value = false
  }
  // iOS standalone check
  if (window.navigator.standalone === true) {
    showInstallPrompt.value = false
  }
})
```

---

### 8. Laravel Sanctum Token Revocation Not Working

**Symptom**: Logout deletes token locally but token still valid on server.

**Fix**: Ensure `Logout` controller actually revokes the token:

```php
// app/Http/Controllers/Api/AuthController.php
public function logout(Request $request) {
  $request->user()->currentAccessToken()->delete()
  // Or for all tokens:
  // $request->user()->tokens()->delete()
  
  return response()->json(['message' => 'Logged out'])
}
```

---

### 9. Build Works Locally But Fails on Server

**Symptom**: `npm run build` passes locally but `vite: not found` on production.

**Fix**: Ensure build runs in deployment pipeline, not runtime. Add to deployment script:

```bash
# In deploy.sh
cd /path/to/laravel
npm ci
npm run build
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

---

### 10. Axios Token Not Sent on Subsequent Requests

**Symptom**: First API call works (login), subsequent calls return 401.

**Root Cause**: Axios interceptor not attached or token not injected.

**Fix**: Verify interceptor in `api.js`:

```javascript
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

---

## Debugging Commands

```bash
# Test API directly
curl -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Check token in localStorage (browser console)
localStorage.getItem('auth_token')

# Verify manifest
curl -s http://localhost/manifest.json | jq .

# Check SW registration (browser console)
navigator.serviceWorker.getRegistrations().then(console.log)

# Laravel route cache
php artisan route:list | grep api

# Clear all caches
php artisan optimize:clear
```