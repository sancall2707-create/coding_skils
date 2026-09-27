# Vue 3 Template Build Errors & Debugging

Common Vite + Vue 3 compilation errors and fixes discovered during full-stack development.

---

## Error: v-else/v-else-if Without Adjacent v-if

**Symptom**:
```
SyntaxError: v-else/v-else-if has no adjacent v-if or v-else-if.
/path/to/file.vue:N:N
```

**Cause**: Vue 3 compiler requires `v-else` or `v-else-if` to immediately follow (or be part of same v-if branch as) the preceding `v-if`.

**Common Bad Pattern**:
```vue
<!-- WRONG: separated by non-conditional elements -->
<header v-if="authStore.isAuthenticated">
  <!-- navbar -->
</header>

<main>
  <router-view />
</main>

<footer v-else>
  <!-- This v-else is NOT adjacent to the header v-if -->
</footer>
```

**Fix 1: Wrap Both in Template**
```vue
<template v-if="authStore.isAuthenticated">
  <header><!-- navbar --></header>
  <main><router-view /></main>
</template>
<template v-else>
  <footer><!-- no navbar, just router-view --></footer>
</template>
```

**Fix 2: Use Separate Root Wrapper** (if you need multi-level layout)
```vue
<div class="min-h-screen flex flex-col">
  <template v-if="authStore.isAuthenticated">
    <header><!-- navbar --></header>
    <main><router-view /></main>
  </template>
  <template v-else>
    <router-view />
  </template>
</div>
```

---

## Debug Strategy: npm run build via execute_code

**Problem**: Running `npm run build` from terminal sometimes hangs or fails silently. Shell output truncation masks real error messages.

**Solution**: Use Python subprocess with explicit stderr capture and timeout.

```python
import subprocess
import os

os.chdir('/path/to/app')

result = subprocess.run(
    ['npm', 'run', 'build'],
    capture_output=True,
    text=True,
    timeout=60  # 60-second timeout
)

print("Exit code:", result.returncode)
print("\nSTDOUT (last 1000 chars):")
print(result.stdout[-1000:])

if result.returncode != 0:
    print("\nSTDERR (full):")
    print(result.stderr)
```

**Expected output on success**:
```
Exit code: 0

STDOUT (last 1000 chars):
✓ 88 modules transformed.
public/build/assets/app-CJP1fpfe.css   26.63 kB │ gzip:  5.54 kB
public/build/assets/app-Dhftysbd.js   201.48 kB │ gzip: 66.39 kB
✓ built in 788ms
```

**Typical errors caught**:
- Missing deps (add to package.json + `npm install`)
- Vue template syntax errors (see above)
- Missing Tailwind config
- PostCSS configuration issues

---

## Tailwind CSS + Vite Integration

**Minimal Config** (tailwind.config.js):
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

**Minimal Config** (postcss.config.js):
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

**CSS Entry** (resources/css/app.css):
```css
@import "tailwindcss";

body {
  background-color: #f3f4f6;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

---

## Vite Config Essentials

**vite.config.js** (for Laravel + Vue 3):
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

---

## Common Package Installation Issues

### Missing Tailwind Formatter (Older Versions)
```bash
# If @tailwindcss/postcss not found:
npm install -D @tailwindcss/postcss postcss autoprefixer
```

### Vue 3 Component Format
Ensure Vue components use `<script setup>` syntax (recommended) or traditional `<script>` block. Vite/Rolldown expects strict template structure.

**Correct**:
```vue
<template>
  <div>{{ message }}</div>
</template>

<script setup>
import { ref } from 'vue'
const message = ref('Hello')
</script>
```

**Avoid** (loose templates):
```vue
<!-- Missing <script> block causes parser errors -->
<template>
  <div>{{ message }}</div>
</template>
```

---

## Build Output Verification

After successful build, check `public/build/`:
```bash
ls -la public/build/
# Should contain:
# - manifest.json
# - assets/app-*.css
# - assets/app-*.js
```

Manifest structure (used by Laravel Vite plugin):
```json
{
  "resources/js/app.js": {
    "file": "assets/app-Dhftysbd.js",
    "src": "resources/js/app.js",
    "isEntry": true,
    "imports": ["_vendor-xyz.js"],
    "css": ["assets/app-CJP1fpfe.css"]
  }
}
```

---

## Performance Optimization

### Code Splitting
Vite automatically splits async imports into separate chunks. Use lazy routes:
```javascript
const AdminDashboard = defineAsyncComponent(() =>
  import('./pages/AdminDashboard.vue')
)

const routes = [
  { path: '/admin', component: AdminDashboard, meta: { requiresAdmin: true } }
]
```

### Watch Mode (Development)
```bash
npm run dev  # Vite dev server with HMR (hot reload)
```

Rebuilds only changed files; significantly faster feedback loop than full builds.