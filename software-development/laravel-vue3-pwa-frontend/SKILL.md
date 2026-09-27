---
name: laravel-vue3-pwa-frontend
description: Build Vue 3 SPA frontend on Laravel with Tailwind CSS v4, Vite, Pinia state, Sanctum API auth, and PWA support (manifest + Service Worker). Covers full setup, common build issues, and integration patterns.
---

# Skill: Laravel + Vue 3 + PWA Frontend

Full-stack single-page application (SPA) development using Laravel backend + Vue 3 frontend + Tailwind CSS + PWA capabilities. Suitable for mobile-responsive web apps requiring offline support.

## Scope

This skill covers:
- Vite + Vue 3 setup on existing Laravel project
- Tailwind CSS v4 configuration (uses `@tailwindcss/postcss` plugin model)
- Vue Router for client-side routing
- Pinia for state management (auth store, data stores)
- Axios HTTP client with Sanctum token interceptors
- Service Worker & PWA manifest setup
- Build optimization and asset pipeline
- Common integration gotchas (CORS, token refresh, offline caching)

## Prerequisites

- Existing Laravel project with API endpoints (see `laravel-api-backend`, `laravel-sanctum-rbac`)
- Node.js + npm installed on VPS
- Basic Vue 3 Composition API knowledge

## Procedure

### 1. Install Frontend Dependencies

```bash
cd ~/project-folder/app
npm install -D tailwindcss postcss autoprefixer vue@latest @vitejs/plugin-vue \
  axios vue-router pinia
```

**Expected output**: 180+ packages added, 0 vulnerabilities.

### 2. Create Tailwind Config Files

**tailwind.config.js:**
```javascript
export default {
  content: [
    "./index.html",
    "./resources/js/**/*.{js,ts,jsx,tsx,vue}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**postcss.config.js:**
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

**resources/css/app.css:**
```css
@import "tailwindcss";

body {
    background-color: #f3f4f6;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}
```

### 3. Configure Vite

**vite.config.js:**
```javascript
import { defineConfig } from 'vite';
import laravel from 'laravel-vite-plugin';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
    plugins: [
        laravel({
            input: ['resources/css/app.css', 'resources/js/app.js'],
            refresh: true,
        }),
        vue({
            template: {
                transformAssetUrls: {
                    base: null,
                    includeAbsolute: false,
                },
            },
        }),
    ],
});
```

### 4. Create Vue 3 Entry Point

**resources/js/app.js:**
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/index.js'
import App from './App.vue'
import '../css/app.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
```

### 5. Create Blade Host View & Configure Laravel SPA Routes

**routes/web.php:**
```php
<?php

use Illuminate\Support\Facades\Route;

// Host SPA Blade view for root route
Route::get('/', function () {
    return view('welcome');
});

// MANDATORY SPA FALLBACK: All other web routes render welcome view
// Allows Vue Router to handle client-side sub-path reloads (/login, /vehicles, /admin)
Route::fallback(function () {
    return view('welcome');
});
```

**app/Providers/AppServiceProvider.php (Force HTTPS behind proxy/tunnel):**
```php
<?php

namespace App\Providers;

use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        // Force HTTPS URL scheme when behind proxy/tunnel to avoid Mixed Content errors
        if (config('app.env') !== 'local' || request()->header('X-Forwarded-Proto') === 'https' || str_contains(config('app.url'), 'https://')) {
            URL::forceScheme('https');
        }
    }
}
```

**bootstrap/app.php (Trust Cloudflare / Reverse Proxy headers):**
```php
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->trustProxies(at: '*');
    })
```

**resources/views/welcome.blade.php:**
```blade
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your App</title>
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1e40af">
    <link rel="icon" href="/favicon.ico">
    
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen">
    <div id="app"></div>

    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('PWA Service Worker registered:', reg.scope))
                    .catch(err => console.log('PWA Service Worker registration failed:', err));
            });
        }
    </script>
</body>
</html>
```

### 6. Create API Service

**resources/js/services/api.js:**
```javascript
import axios from 'axios'

const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Add token from localStorage to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// Handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

### 7. Create Pinia Stores

**resources/js/stores/auth.js:**
```javascript
import { defineStore } from 'pinia'
import apiClient from '../services/api.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('auth_user')) || null,
    token: localStorage.getItem('auth_token') || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/login', { email, password })
        this.token = response.data.token
        this.user = response.data.user
        
        localStorage.setItem('auth_token', this.token)
        localStorage.setItem('auth_user', JSON.stringify(this.user))
        return response.data
      } catch (err) {
        this.error = err.response?.data?.message || 'Login failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    async logout() {
      try {
        if (this.token) {
          await apiClient.post('/logout')
        }
      } finally {
        this.token = null
        this.user = null
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    },
  },
})
```

### 8. Setup Vue Router

**resources/js/router/index.js:**
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

import Login from '../pages/Login.vue'
import Dashboard from '../pages/Dashboard.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { requiresGuest: true } },
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
```

### 9. Create PWA Assets

**public/manifest.json:**
```json
{
  "name": "Your App Name",
  "short_name": "App",
  "description": "Your app description",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1e40af",
  "theme_color": "#1e40af",
  "icons": [
    {
      "src": "/favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ]
}
```

**public/sw.js:**
```javascript
const CACHE_NAME = 'pwa-v1';
const urlsToCache = ['/', '/index.html', '/favicon.ico', '/manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Skip API calls - always fetch from network
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((response) => {
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return response;
      }).catch(() => {
        return caches.match('/index.html');
      });
    })
  );
});
```

### 10. Build Frontend Assets

```bash
npm run build
```

**Expected output:**
```
✓ built in 790ms
public/build/assets/app-xxxx.css  24 kB
public/build/assets/app-xxxx.js   180 kB
```

---

## Common Pitfalls & Fixes

See `references/tailwind-v4-migration.md` for:
- `@tailwindcss/postcss` vs legacy `tailwindcss` plugin error
- PostCSS configuration changes in v4
- Vite build failures with CSS

---

## Verification

```bash
# Check SPA loads
curl -s http://localhost | grep -E "(app|vite|manifest)"

# Expected: asset links visible in HTML
# <link rel="modulepreload" href="http://localhost/build/assets/app-xxxx.js">
```

---

## File Structure

After setup:
```
resources/
├── css/
│   └── app.css
├── js/
│   ├── app.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js
│   ├── stores/
│   │   ├── auth.js
│   │   └── booking.js
│   ├── services/
│   │   └── api.js
│   └── pages/
│       ├── Login.vue
│       ├── Dashboard.vue
│       └── ...
└── views/
    └── welcome.blade.php

public/
├── build/
│   └── assets/
│       ├── app-xxxx.css
│       └── app-xxxx.js
├── manifest.json
├── sw.js
└── favicon.ico
```

---

### Caddy SPA Fallback Configuration (Required for Production)

**/etc/caddy/Caddyfile** (Official Laravel Caddy v2 pattern):
```caddyfile
:80 {
    root * /home/ubuntu/your-project/app/public
    encode gzip

    # SPA Fallback: Check if static file exists; if not, rewrite to index.php
    @notStatic {
        not file {path}
    }
    rewrite @notStatic /index.php?{query}

    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
}
```

This handles:
- Static assets (`/build/*`, `/icons/*`, `*.css`, `*.js`, etc.) served directly
- API routes (`/api/*`) handled by Laravel
- All other routes (Vue SPA routes: `/login`, `/vehicles`, `/admin`, etc.) rewritten to `index.php` so Laravel returns the Blade host view, letting Vue Router take over

---

## Next Steps

1. Create reusable Vue components (Header, Cards, Forms)
2. Implement specific pages (Dashboard, Forms, Lists)
3. Add Tailwind responsive utilities for mobile
4. Test PWA offline functionality
5. Enable HTTPS for production (Caddy auto-HTTPS)
