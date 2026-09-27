# Tailwind CSS v4 Integration Rationale & Troubleshooting

## Tailwind CSS v4 Changes

In Tailwind CSS v4:
- The `@tailwindcss/postcss` package is required when using PostCSS.
- Direct use of `tailwindcss` in `postcss.config.js` causes build errors.
- The CSS directive changes from `@tailwind base; @tailwind components; @tailwind utilities;` to `@import "tailwindcss";`.

## Troubleshooting Vite Build Errors

### Error: `It looks like you're trying to use tailwindcss directly as a PostCSS plugin`

**Fix**:
1. Install `@tailwindcss/postcss`:
   ```bash
   npm install -D @tailwindcss/postcss
   ```
2. Update `postcss.config.js`:
   ```javascript
   export default {
     plugins: {
       '@tailwindcss/postcss': {},
       autoprefixer: {},
     },
   }
   ```
3. Update `resources/css/app.css`:
   ```css
   @import "tailwindcss";
   ```

## Chunked Write Protocol for Frontend Code

When creating large Vue single-page apps (SPA) or components:
- Keep Vue files modular and under 300 lines each.
- Separate stores (`stores/auth.js`, `stores/booking.js`), routing (`router/index.js`), and HTTP services (`services/api.js`).
- This fits within the 350-line write limit per tool call and prevents server timeouts.
