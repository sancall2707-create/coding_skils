# Branding assets for Laravel + React PWAs

Use when the user provides an official logo or asks to replace placeholder branding.

## Asset placement pattern
- Save the uploaded official logo to `public/images/<brand-logo>.png`.
- Generate PWA icons from the same source:
  - `public/icons/icon-192x192.png`
  - `public/icons/icon-512x512.png`
- Generate browser favicon:
  - `public/favicon.png`
  - `public/favicon.ico`
- Keep `manifest.webmanifest` pointing at `/icons/icon-192x192.png` and `/icons/icon-512x512.png` unless names change.
- Add `<link rel="icon" type="image/png" href="/favicon.png">` to the Blade shell.

## UI replacement checklist
- Replace placeholder text logos (e.g. `SL`) in:
  - shared layout/header component
  - login page
  - register page
  - PWA icon files
  - favicon
- Use accessible alt text: `alt="Logo <organization>"`.
- For circular crest logos, use a white circular wrapper with `rounded-full`, subtle border/ring, `overflow-hidden`, and `object-contain`.

## Verification
- Run `npm run build`.
- Run backend tests if the project uses Laravel: `php artisan test`.
- Browser visual check:
  - login page logo appears centered and not cropped
  - app header logo is readable at small size
  - favicon and PWA icons load

## Durable pitfall
Do not leave old placeholder branding in the header after replacing login/register logos. Check every reused layout component, not only auth pages.
