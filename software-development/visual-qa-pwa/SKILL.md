---
name: visual-qa-pwa
description: Visual Quality Assurance checklist & patterns for React/PWA/Laravel projects using browser vision. Catches icon overlap, nested cards, tab radius, CSS utility conflicts, and empty-state patterns.
---

# Skill: Visual QA for PWA / React Frontend

Trigger: any task that modifies UI components, layouts, or styling in a React + Tailwind + Laravel PWA project.

## Visual Regression Checklist (run after every UI change)

1. **Icon–Input Overlap**
   - Open the page in headless browser (`browser_navigate` + `browser_vision`).
   - Verify search/icon inputs: the icon must sit **left of** the text, never on top.
   - Root cause: a custom CSS class using `padding: 0.75rem 1rem` (shorthand) overrides Tailwind `pl-10` utility.
   - Fix: change custom class to explicit `padding-left`, `padding-right` or add `!pl-11` on the input and set icon `absolute left-3.5`.

2. **Nested Card Borders**
   - Scan for `app-card` (or equivalent) inside another `app-card`.
   - More than one level = visual noise (double borders, stacked shadows, extra padding).
   - Fix: flatten to a single card wrapper per semantic section.

3. **Segmented Tab Radius**
   - Tab bar wrapper: `bg-slate-200/60 p-1.5 rounded-2xl`.
   - Active tab button: `rounded-xl bg-primary text-white shadow-sm`.
   - Inactive tabs: `rounded-xl text-slate-600 hover:bg-white/60`.
   - **Never** let an active button be square while the outer wrapper is rounded.

4. **Filter / Search Alignment**
   - Use a single container card for all filter controls.
   - Grid: `grid grid-cols-1 sm:grid-cols-3 gap-3` for [search, status, unit].
   - Show “Reset Filter” button **only** when any filter/search is active.

5. **Empty State**
   - Centered icon + bold title + explanatory text.
   - If filters are active, include inline “Reset Filter” button.

6. **Hero / Section Header**
   - Solid background (navy) + accent pill (amber) + generous padding (`p-6 sm:p-7`).
   - Title `text-2xl sm:text-3xl font-extrabold`, subtitle `text-slate-300 text-sm`.

7. **Logo Asset Alignment**
   - When replacing initials/placeholders with an official logo, create square 1:1 assets before use (`public/images/logo-*.png`, PWA icons, favicon).
   - Header logo + text must share one vertical centerline: logo `w-10 h-10 rounded-full object-cover`, text wrapper `flex flex-col justify-center`, subtitle `leading-none mt-0.5`.
   - Visually verify no whitespace padding, off-center crop, or text block sitting too high/low.

8. **Dynamic Item Lists / Repeating Form Rows**
   - Never show a quantity field alone. Add explicit column headers and a name field, e.g. `Nama Barang / Peralatan` + `Jumlah`.
   - Place the item name input as the flexible column and quantity as a fixed-width numeric field (`w-24`).
   - Display saved items again in detail/admin views as `name — qty unit` so approvers know exactly what was requested.

## Verification Commands

```bash
# Build & test must pass
npm run build
php artisan test
```

```bash
# Quick headless visual check
browser_navigate <url>
browser_vision "check icon overlap, nested cards, tab radius, filter alignment, empty state"
```

## Common Pitfalls (from past sessions)

- `.input-base { padding: 0.75rem 1rem }` → use long-hand `padding-left/right` so `pl-*` utilities win.
- Forgetting `!pl-11` on icon inputs when a base class exists.
- Triple-nested `app-card` from `Admin.jsx` → tab content → list item.
- Tab button with `bg-primary` but no `rounded-xl` inside a `rounded-2xl` wrapper.

## New Patterns from Space Link Audit (Sep 2025)

### Admin sub-dashboard must expose "Back to Home"
- Add a prominent `Kembali ke Beranda` (or `Back to Dashboard`) button in the admin hero/header, not rely on logo click alone.
- Place it on the right side of the header banner, using `Link to="/"`.

### Logo asset pipeline
- Source logos often come as non-square JPEGs with whitespace.
- Create square 1:1 PNG assets at 1255×1255 (or similar) then generate:
  - `public/images/logo-pl-deltamas.png`
  - PWA icons `192x192` and `512x512`
  - Favicon `32x32` + `favicon.ico`
- Use a script (`scripts/gen-icons.py`) to automate this.

### TimePicker defaults
- For school/facility scheduling, default to **full 24-hour range (00–23)** and **full 60-minute range (00–59)** unless user explicitly restricts.
- Auto-scroll selected values into view when modal opens (`scrollIntoView({ block: 'center' })`).

### Dynamic item rows (repeating form fields)
- Always show column headers: `Nama Barang / Peralatan` | `Jumlah`
- Placeholders should include realistic examples: `Misal: Kursi Lipat, Mic, Sound System`
- On detail/admin views, render each saved item as `Name — Qty unit`.

### Filter / search section standardization
- Single container card with header row containing title + "Reset Filter" (only visible when filters active).
- Grid layout: `grid grid-cols-1 sm:grid-cols-3 gap-3` for [search, dropdown1, dropdown2].
- Search icon positioning: input `!pl-11`, icon `absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none`.

### Vertical centering for header logo + text
- Logo: `w-10 h-10 rounded-full object-cover bg-white p-0.5 shadow-sm ring-2 ring-amber/80`
- Text wrapper: `flex flex-col justify-center`
- Subtitle: `leading-none mt-0.5`