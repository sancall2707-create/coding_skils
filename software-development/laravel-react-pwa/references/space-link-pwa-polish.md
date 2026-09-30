# Space Link PWA Polish Notes

Session-derived patterns for Laravel + React PWA polish.

## Durable UI/PWA patterns
- Add a global `ToastProvider` high in `app.jsx` so any page/action can give success/error/info feedback without per-page modal hacks.
- Keep `OfflineBanner` inside `AppLayout` so every authenticated page gets online/offline state automatically.
- Use `beforeinstallprompt` in both `Home.jsx` and a dedicated `PanduanPWA.jsx`; headless browsers may not trigger it, so absence during automated browser checks is not a failure if manifest + SW load.
- For admin bottom navigation, use dynamic grid classes (`grid-cols-4` vs `grid-cols-5`) based on nav item count; otherwise admin nav can wrap/squish on mobile.
- PWA install guide should include Android Chrome/Edge and iOS Safari paths; iOS uses Share → Add to Home Screen, not `beforeinstallprompt`.

## Service worker pitfall
- Stale navigation cache can make deep links appear to redirect to a previous route. During debugging, clear/unregister SW + cache in browser:

```js
(async () => {
  const regs = await navigator.serviceWorker.getRegistrations();
  for (const r of regs) await r.unregister();
  const keys = await caches.keys();
  for (const k of keys) await caches.delete(k);
})();
```

- Production-safe `sw.js` rule: skip `/api/*`, skip non-GET, skip `/storage/*`, and fetch navigations fresh (`request.mode === 'navigate'`) before falling back.

## Visual QA notes
- Verify PWA polish with real browser screenshots: Home, Admin Dashboard, Calendar, Panduan PWA.
- Check for truncated labels in bottom nav and admin tabs.
- If a visual model says no screenshot attached despite a screenshot path being returned, load the screenshot path with `vision_analyze` and continue.

## Verification
- `npm run build` must pass.
- `php artisan test` must pass.
- Manual browser smoke: login → home → `/panduan-pwa` → `/admin` → tab switching.
