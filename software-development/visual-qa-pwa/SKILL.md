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

### PWA Form Layout, Avatar Centering & Navigation Alignment (Oct 2026)
- **Profile Avatar Centering in Forms**: Never position user avatar thumbnails on the far left edge of a profile form. Center the avatar horizontally (`margin: 0 auto 10px; display: block; border-radius: 50%`) along with the user's name, username, and upload action.
- **Consistent Back Navigation in Subpages**: Never place ad-hoc return buttons like `← Ke Beranda` floating on the right side of content cards. Always integrate standard PWA subheader navigation with a back arrow `<` aligned on the top bar.
- **Indonesian Terminology ("Beranda" vs "Dashboard")**: In Indonesian-language applications, always use the standard term **"Beranda"** instead of the loanword "Dashboard" for all page titles, headers, navigation tabs, and back links.
- **Bottom Navigation Conflict on Long Forms**: On complex data entry or edit forms, either hide the fixed bottom nav (`$hideBottomNav = true`) or provide at least `100px` bottom margin so that the fixed bottom navigation bar does not overlap submit buttons or form inputs when virtual keyboards open.
- **Administrative Self-Profile Access**: When building administrative portals (Super Admin / TPPBM), ensure administrators have a dedicated, direct access point to their own profile, avatar upload, and password change (via top-bar avatar shortcut and a dedicated sidebar/hamburger item), rather than only managing subordinate accounts.
- **Lifecycle Status Automation (Schedule & Report Pairing)**: When users submit an event reflection or report (e.g. spiritual guidance, wawanhati, journal), the report status must immediately reflect **"Selesai"** (completed/green badge, not remaining stuck on "Menunggu"), and any corresponding agenda schedule on that date must be automatically linked and updated to `completed`.
- **Flexible Month-Range Recap Filtering**: In administrative monitoring and reporting views, replace single-month dropdowns with customizable month ranges (e.g., `Dari Bulan` to `Sampai Bulan` across 1–12 months) to allow semester, annual, and custom period filtering for both on-screen list views and Excel/PDF exports.
- **Official Document & Raport Printing in Mobile-First PWAs**: Mobile-first shells (`max-width: 480px`) must break out to `width: 100% !important; max-width: 100% !important;` in `@media print` so A4 prints don't render as narrow 12cm columns. Use `@page { size: A4 portrait; margin: 1.5cm 1.5cm 1.5cm 2cm; }`, enforce `print-color-adjust: exact !important` for status badges/headers.
- **Collision-Proof Print Footers, Real Page Numbers & Continuous Documents ("Jangan Menabrak Dokumen, Halaman Bukan 0, & Footer Terakhir Tetap di Dasar Kertas")**:
  - *Pitfall 1 (`position: fixed; bottom: 0`)*: Content flows to bottom:0 and collides/overlaps with the fixed footer line.
  - *Pitfall 2 (`tfoot` with `counter(page)`)*: `counter(page)` in DOM elements evaluates to `0` in Chromium Skia/PDF (`Halaman 0`), and on the last page `tfoot` is rendered immediately below the last row (floating in the middle of the paper instead of at the bottom).
  - *Proven Solution (Dynamic A4 Client Pagination)*: Measure block heights (`testContainer.offsetHeight`) against safe A4 printable threshold (~820px at 96 DPI), group blocks into `.raport-page` with `min-height: 25.8cm; display: flex; flex-direction: column; justify-content: space-between; page-break-after: always;`. This guarantees:
    1. Content flows continuously without huge empty spaces.
    2. Footer is pinned to the very bottom on EVERY page, including the last page (via `justify-content: space-between; flex-shrink: 0;`).
    3. Real page numbers (`Halaman 1`, `Halaman 2`, etc.) rendered as DOM text, never evaluating to `0`.
    4. Exact margins (Atas 1.5cm, Kanan 1.5cm, Bawah 1.5cm, Kiri 2.0cm).
- **Dual-Logo Header Pattern**: Left: parent logo (`logo-fic.png`), Center: title + subtitle, Right: committee logo (`logo-tppbm.png`), separated by dual navy rule (`border-top: 2.5px solid #0E3366; border-bottom: 0.8px solid #0E3366;`).
- **Dynamic Signatures Bound to RBAC Roles in Official Documents**: Never hardcode signatory names. Bind Ketua/Chairman signature to `admin_ketua_tppbm` and Administrator Data to `super_admin` with graceful defaults. Allow role assignment in account creation and edit views.
- **Full Retract (Tarik) & Edit Lifecycle for Admin Notes**: Provide inline history with Edit and Tarik (confirm dialog) for all administrative guidance notes (`BruderNote`) and private messages (`DirectMessage`).
- **Differentiated Directory Controls for Members vs Administrators**: In multi-role directories (e.g. Manajemen Data), list all accounts but differentiate actions: regular members have mentoring links (Track Record, Add Notes, Send Message), while administrators and chairs (admin, admin_ketua_tppbm, super_admin) only have account management (Kelola Akun, Nonaktifkan, Hapus), with self-deactivation/deletion guards.
- **Member Personal Logbook Edit & Delete Lifecycle (Jurnal & Agenda Pribadi)**: Every member logbook/record card (e.g. Jurnal Pengembangan Diri, Agenda Pribadi) must include explicit paired actions: `Edit` (pre-filled form with live validation/character counter) and `Hapus` (`btn-danger` form with confirm dialog, scoped to owner via `user_id`).
- **Domain-Specific Administrative Navigation ("Beranda Bruder Muda" over "Lihat PWA")**: In administrative slideout and desktop menus, never use technical/developer jargon such as "Lihat PWA", "Open PWA", or "View App". Use standard role/persona-based navigation labels, such as **"Beranda Bruder Muda"**.
- **Administrative Broadcast Lifecycle & Attachment Cleanup (Sapaan & Pengumuman)**: Administrative broadcast management must provide the complete lifecycle: Create, Edit, Toggle Status (Tarik/Tayangkan), and Delete (Hapus with confirmation). When deleting broadcast records (`ProvincialMessage`), verify and remove associated media files (`storage/app/public/sapaan/*`) to prevent disk bloat.
- **Blade Attribute Interpolation Pitfall (No `\'` in `{{ }}`)**: Never escape quotes with backslashes `\'` inside Blade interpolation `{{ ... }}` within HTML attributes. Blade compiles `{{ }}` into `<?php echo e(...) ?>`, making `\'` a fatal PHP `ParseError`. Use double quotes `"` or keep JS strings outside the interpolation.
- **Client-Side Image Pre-Compression & Upload Limits**: Intercept profile photo file inputs with `<canvas>` to downscale modern phone photos (e.g. 1200px max, 0.85 JPEG quality) client-side before submission, paired with 20M/25M PHP ini and 10MB controller validation.
- **Native Google Chrome Deb vs Snap Headless PDF**: Headless PDF printing on Ubuntu requires native `google-chrome-stable` deb (not Canonical's Snap wrapper, which breaks `--headless` flag delegation and sandbox `/tmp` access).
- **Administrative Mobile Bottom Navigation & FAB Clearance**: When providing bottom navigation menus for administrative roles (`sa-bottom-nav` with Beranda, Bruder, Raport, Monitoring, Sapaan), adjust root container `padding-bottom: 76px` and elevate any fixed Floating Action Button (`.fab`) from `bottom: 24px` to `bottom: 80px` to maintain touch clearance and prevent icon overlap. Ensure `@media print` explicitly hides `.sa-bottom-nav`.
- **Retrospective Date Boundary Enforcement**: For past events and reflection reports (Bimbingan Rohani, Wawanhati), set `max="{{ date('Y-m-d') }}"` in HTML to block future date pickers and pair with `'before_or_equal:today'` backend validation rule.
- **Zero Fabricated/Dummy Content in Official Documents**: Never insert placeholder or hardcoded sample evaluations in `@else` blocks of official reports (e.g. Raport Section I). Render `-` or blank space if mentors/admins have not yet entered notes.
- **Exclusive Tab Panes vs Tall Scrollable Anchor Tabs in Multi-Section Forms**: When a form has 5+ detailed sections, do not merely render sticky anchor links on one tall scrollable page. Use real exclusive tab panes (`display: none` / `display: block`) with paired progressive step buttons (`Lanjut ke ... →`, `← ...`) and an `invalid` event listener that auto-switches to the tab pane containing any invalid input.
- **Symmetrical & Uniform Action Button Alignment in Checklist Feeds**: Enforce fixed dimensions for action pill buttons (`width: 76px; height: 32px`) across all checklist rows, uniform row heights (`min-height: 54px`), and non-wrapping counter badges (`white-space: nowrap; font-size: 10px`).
- **Clean Metric Summaries vs Cluttered Arithmetic Formulas**: Keep dashboard KPI cards clean (`Akumulasi Tahun {{ now()->year }}: {{ $val }} / 24`). Do not expose internal multiplication or arithmetic formulas (e.g. `(2 × 12)`).
- **Auto-Submit Loading Spinner State on Mobile Forms**: Add a global submit listener to base PWA layouts to automatically disable submit buttons, prevent duplicate clicks, and show a spinner with text like *"Menyimpan..."*.
- **Future Date Filtering in Historical Reports & Resumes**: In official documents (Raport) and assignment timelines, filter out future years (`$year <= now()->year`) and render ongoing assignments as `[Year] - Sekarang`.
- **Custom Touch-Friendly Mobile Pagination**: Override Laravel's default unstyled pagination (`Paginator::defaultView('vendor.pagination.custom')`) with compact 34x34px square buttons and a clean results summary to avoid raw SVG overflows.
- **Role-Aware Dynamic Category Labels in Content Feeds**: When broadcast items can be authored by different roles (e.g. Provinsial vs TPPBM), bind card badges and page headers dynamically via a helper (`$model->sapaanLabel()`). Provide client-side author auto-fill when switching author role dropdowns.
- **Compliance Metrics Denominator Scoping**: Strictly limit mandatory compliance calculations to core required instruments (e.g. 1 Bimbingan + 1 Wawanhati = 2x/month, 24x/year). Never inflate expected reports by including optional/supplemental personal development journals in the denominator.
- **Dual Time-Horizon Progress Gauge (Full-Year Cumulative vs Monthly Reset)**:
  - *Left Gauge (Akumulasi Tahunan)*: Menghitung seluruh pembinaan sejak 1 Januari s.d. tanggal saat ini pada tahun berjalan dengan target tetap 24 kali ($2 \times 12$). Nilai akumulasi terus bertambah dan tidak di-reset saat pergantian bulan.
  - *Right Stats (Akumulasi Bulanan)*: Menghitung pembinaan aktual pada bulan berjalan (target: 2), otomatis kembali ke `0 / 2` (`0%`) saat bulan berganti.
- **Universal Retrospective Date Boundary**: Terapkan `max="{{ date('Y-m-d') }}"` di HTML dan validasi backend `'before_or_equal:today'` di seluruh instrumen formasi (Bimbingan, Wawanhati, Jurnal).
- **Eloquent Collection Merge vs Concat Pitfall with Generic Objects (`stdClass::getKey()`)**: When combining mapped arrays or generic `stdClass` items created from Eloquent models (e.g. merging three schedule types), never use `$collection->merge($other)`. Eloquent's Collection `merge()` checks `$item->getKey()`, throwing fatal `Error: Call to undefined method stdClass::getKey()`. Always use `collect()->concat($a)->concat($b)->values()`.
- **Omnipresent Member Agendas in Administrative Monitoring**: All personal member schedules/agendas (`PersonalAgenda`) must be seamlessly aggregated into administrative oversight (Super Admin & TPPBM monitoring calendar `/super-admin/monitoring/agenda` and dashboard "Jadwal Pembinaan & Agenda Terdekat" widget) so mentors can remind members of upcoming commitments.
- **Dual Circular Progress Indicators Side-by-Side (Horizontal Pair)**:
  - Do not leave empty space by rendering only one circular gauge on the left of KPI cards.
  - Render two distinct circular SVG gauges side-by-side (`display: flex; gap: 12px; flex-shrink: 0;`):
    1. *Left Ring (Akumulasi Tahunan)*: Measures total records since January 1st to today with annual target (e.g. 24x), label "Akumulasi Tahunan", badge `[N]/24`, does not reset when months change.
    2. *Right Ring (Bulan Berjalan)*: Measures current month records with monthly target (e.g. 2x), label "Bulan Berjalan", badge `[N]/2`, resets to 0/2 (0%) on the 1st of every month.
  - Position detail breakdown (target description, count per month, and full-year cumulative line) on the right of both rings (`flex: 1; min-width: 160px;`).
  - Size rings proportionally (`width: 68px; height: 68px;`) so mobile viewports fit both rings and text side-by-side without line wrapping or truncation.
- **Full-Width Accumulation Summary Bar (`.stat-year-summary`)**: Instead of nesting the full-year accumulation metric inside small side info text, position it as a full-width bottom pill bar spanning the entire card with flex justify-between (`Akumulasi Januari – [Bulan] [Tahun]` on left, bold pill badge `[N] / 24` on right).
- **Service Worker Cache Invalidation on UI Assets Change**: Always increment `CACHE_VERSION` in `public/sw.js` (e.g. `'20261023a'`) when modifying CSS or Blade views so clients immediately drop stale caches and load refreshed styles.
- **Continuous A4 Document Font Sizing Standards**: For Chrome Headless printed documents (Raport), calibrate base body to `12px` (not 11px), section headers to `13px`, and table cells to `11.5px` with `10.5px` footers to maximize legibility without page blow-out.
- **Custom Domain Deployment Architecture (cPanel vs VPS)**: Never deploy Laravel PWA with headless Chrome requirements to cPanel shared hosting; point domain `A` records (`@` and `www`) via cPanel Zone Editor directly to the VPS IP and let Caddy handle automatic HTTPS.
- See `references/pwa-subpage-and-profile-patterns.md` for detailed subpage navigation, avatar centering, dynamic signatures, note retract/edit lifecycle, differentiated directory controls, client-side photo compression, headless PDF printing, retrospective date bounds, exclusive tab panes, checklist button symmetry, future date filtering, mobile pagination styling, role-aware category labels, compliance denominator scoping, dual time-horizon gauges, Eloquent concat patterns, administrative agenda aggregation, dual circular indicators, SW cache invalidation, and custom domain deployment.