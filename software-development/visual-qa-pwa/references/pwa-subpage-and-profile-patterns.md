# PWA Subpage, Profile Form & Admin Self-Management Patterns

## 1. Subpage Navigation vs Ad-Hoc Back Buttons
- **Anti-Pattern**: Placing floating or inline text links such as `← Ke Beranda` or `Kembali` on the right side of content cards. This breaks visual symmetry and creates uneven whitespace.
- **Best Practice**: Use the standardized PWA subheader (`.page-subheader`) rendered at the top of the container:
  - Back arrow `<` on the left.
  - Page title clearly displayed beside the arrow.
  - In Laravel Blade layouts: set `$backUrl = route('...')` and `$pageTitle = '...'` in the view to trigger the layout's subheader automatically.

## 2. Avatar & Profile Heading Centering
- **Anti-Pattern**: Floating avatar thumbnails to the far-left edge of profile or account forms while section labels or titles sit above or beside them.
- **Best Practice**:
  - Center the user's avatar circle horizontally (`display: flex; justify-content: center; margin: 0 auto 10px`).
  - Center the user's full name, username, and account badge directly below the avatar.
  - Center or neatly standardize the file upload box below the avatar.
  - Keep form section titles centered or consistently aligned across all cards.

## 3. Fixed Bottom Navigation Conflicts on Form Pages
- **Problem**: Fixed bottom navigation bars (`position: fixed; bottom: 0`) often overlap bottom form elements (submit buttons, cancel links) and get pushed awkwardly when mobile virtual keyboards pop up.
- **Solution**:
  1. Set `$hideBottomNav = true` on dedicated full-page edit forms so the entire viewport is dedicated to data entry.
  2. If bottom navigation remains visible, always enforce a minimum container bottom margin/padding of at least `100px` (`margin: 12px 0 100px;` on the form actions block) so that scrolling reaches all buttons with clear clearance.

## 4. Multi-Role Admin Self-Profile Management
- **Problem**: Administrative consoles often implement user CRUD (managing subordinate users, brothers, employees) but forget that administrators also need to update their own credentials, contact info, photo, and password.
- **Pattern**:
  - Header shortcut: Circular avatar/initials badge in the admin header top bar directly opening `/super-admin/profil`.
  - Menu shortcut: Dedicated `Profil & Edit Akun Saya` item in the slideout/hamburger menu.
  - Dedicated view extending admin layout with personal profile editing and separate current-password-verified password reset.

## 5. Lifecycle Status Automation (Schedule & Report Pairing)
- **Problem**: Users submit reports/reflections (e.g. bimbingan rohani, wawanhati), but the monitoring dashboard still displays "Menunggu", and the calendar schedule remains open/scheduled.
- **Root Cause**:
  1. The monitoring query only treated explicit statuses like `['completed', 'approved', 'published']` as done, leaving `submitted` as `Menunggu`.
  2. The report submission controller did not look up or update the corresponding event schedule in the database.
- **Pattern**:
  - In report controller `store()`:
    ```php
    $schedule = EventSchedule::where('user_id', auth()->id())
        ->whereDate('scheduled_at', $validated['meeting_date'])
        ->where('status', '!=', 'cancelled')
        ->first();
    if ($schedule) {
        $schedule->update(['status' => 'completed']);
    }
    ```
  - In monitoring query `row()` mapping:
    ```php
    $done = in_array(strtolower($status), ['completed', 'approved', 'published', 'submitted', 'selesai', 'done'], true);
    ```
  - In schedule queries: check if schedule is marked `completed` OR if a matching report exists for that user and date.

## 6. Multi-Month Range Recap Filtering & Export Pattern
- **Problem**: Admin monitoring filters fixed to a single month make it impossible to audit full semester (6 months) or annual (12 months) progress in one view or export.
- **Pattern**:
  - Provide two month selectors: `Dari Bulan` (`bulan`) and `Sampai Bulan` (`bulan_akhir`), plus `Tahun`.
  - Compute period label: single month (e.g., `Oktober 2026`) when equal, or range (e.g., `Januari – Agustus 2026`) when different.
  - In query builder:
    ```php
    $start = Carbon::create($tahun, $bulanAwal, 1)->startOfMonth();
    $end = Carbon::create($tahun, $bulanAkhir, 1)->endOfMonth();
    $query->whereBetween($column, [$startVal, $endVal]);
    ```
  - Export filename reflects the range (e.g., `rekap-laporan-2026-01_sd_08.xls`).

## 7. Official Document & Raport Printing from Mobile-First PWA (A4 Custom Margins, Container Breakout & Print Colors)
- **Container Breakout in `@media print`**:
  ```css
  @media print {
      html, body {
          background: #ffffff !important;
          margin: 0 !important;
          padding: 0 !important;
          width: 100% !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          color-adjust: exact !important;
      }
      .sa-container {
          max-width: 100% !important;
          width: 100% !important;
          min-height: auto !important;
          margin: 0 !important;
          padding: 0 !important;
          box-shadow: none !important;
          background: transparent !important;
      }
      .sa-header, .sa-bottom-nav, .sa-menu-toggle, .sa-menu, .no-print, header, nav {
          display: none !important;
      }
      .sa-body {
          padding: 0 !important;
          margin: 0 !important;
          width: 100% !important;
          max-width: 100% !important;
          gap: 0 !important;
      }
  }
  ```
- **Custom A4 Document Margins (`@page`)**:
  ```css
  @page {
      size: A4 portrait;
      margin: 1.5cm 1.5cm 1.5cm 2cm; /* Top 1.5cm, Right 1.5cm, Bottom 1.5cm, Left 2.0cm (binding clearance) */
  }
  ```

## 8. Collision-Proof Per-Page Footers, Real Page Numbers & Continuous Documents
- **The Pitfall of `position: fixed; bottom: 0` in Print**: Collides with table rows.
- **The Pitfall of `counter(page)` in Chromium Skia/PDF**: Evaluates to `Halaman 0`.
- **Solution (Client-Side Dynamic A4 Paginator)**: Group content blocks into `.raport-page` with `min-height: 25.8cm; display: flex; flex-direction: column; justify-content: space-between; page-break-after: always;`. Renders real DOM page numbers and keeps footer at the bottom of every page.

## 9. Form Input Creation Cleanliness: Placeholders vs Default Values
- **Anti-Pattern**: Populating text inputs in creation forms with dummy strings:
  ```blade
  <!-- WRONG: Pre-populates the field, forcing user to backspace/delete -->
  <input type="text" name="mentor_name" value="{{ old('mentor_name', 'Br. Yohanes Subagio, FIC') }}">
  ```
- **Best Practice**: Keep `value` strictly bound to `old('field')`, and place sample text in `placeholder`:
  ```blade
  <!-- RIGHT: Field starts clean and empty, placeholder guides input -->
  <input type="text" name="mentor_name" value="{{ old('mentor_name') }}" placeholder="Contoh: Br. Yohanes Subagio, FIC">
  ```

## 10. No Emojis in Professional Input Placeholders
- Avoid decorative emojis inside search or form input placeholders (e.g. `placeholder="Cari nama bruder..."`, never `placeholder="🔍 Cari nama bruder..."`).

## 11. Blade `@{{ ... }}` Raw Output Bug
- In Laravel Blade, `@{{ ... }}` is the verbatim escape sequence for JavaScript frameworks (Vue/Alpine). If you write `@{{ $journal->user->username }}`, Blade outputs the raw code string `{{ $journal->user->username }}` to the browser!
- **Fix**: To display a literal `@` symbol before a variable in Blade:
  ```blade
  <!-- RIGHT -->
  {{ '@' . ($journal->user->username ?? '') }}
  <!-- OR -->
  &#64;{{ $journal->user->username ?? '' }}
  ```

## 12. Instant Debounced Real-Time Search & Dropdown Filtering
- **Member Directory Live Search (AJAX Debounce)**:
  ```javascript
  let timer = null;
  let controller = null;
  searchInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(() => {
          if (controller) controller.abort();
          controller = new AbortController();
          const url = new URL(form.action, window.location.origin);
          if (this.value.trim()) url.searchParams.set('search', this.value.trim());
          fetch(url.toString(), {
              headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'text/html' },
              signal: controller.signal
          })
          .then(res => res.text())
          .then(html => { listWrapper.innerHTML = html; window.history.replaceState({}, '', url.toString()); });
      }, 250);
  });
  ```
- **Instant Client-Side Dropdown Filtering**: Pre-cache original select options and dynamically re-populate the `<select>` on each character typed into an accompanying search box.

## 13. Symmetrical Document Action Pairs
- Align paired document actions (e.g., Download PDF and Print Report) side-by-side in a single flex row:
  ```blade
  <div style="display: flex; gap: 8px; margin-top: 12px;">
      <a href="{{ route('...export', ['format' => 'pdf']) }}" style="flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">Unduh PDF</a>
      <button onclick="window.print()" style="flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">Cetak Raport</button>
  </div>
  ```

## 14. Web Server Service Worker Cache-Busting (Caddy / Nginx)
- **Problem**: When a web server caches `/sw.js` with `max-age=31536000`, client browsers never request an updated Service Worker file, keeping stale JavaScript and styles locked for a year even after browser hard-refreshes.
- **Resolution (Caddyfile)**:
  ```caddy
  @sw {
      path /sw.js
  }
  header @sw {
      Cache-Control "no-cache, no-store, must-revalidate"
      Expires "0"
  }

  @static {
      file
      path *.ico *.css *.js *.gif *.webp *.avif *.jpg *.jpeg *.png *.svg *.woff *.woff2 *.webmanifest
      not path /sw.js
  }
  header @static {
      Cache-Control "public, max-age=31536000, immutable"
  }
  ```
- In `sw.js`, explicitly bypass all administrative routes:
  ```javascript
  function isPrivateAsset(pathname) {
      return pathname.startsWith('/super-admin')
          || pathname.startsWith('/admin')
          || pathname === '/profil/foto'
          || pathname.endsWith('/foto')
          || pathname.includes('/bukti');
  }
  ```

## 15. Broadcast Agendas from Admin to All Members
- When administrators add organization-wide joint events (e.g. annual retreat, province days), iterate over all active member records to insert the schedule into each member's personal agenda calendar:
  ```php
  $users = User::where('role', 'user')->where('is_active', true)->get();
  foreach ($users as $user) {
      PersonalAgenda::create([
          'user_id' => $user->id,
          'title' => $validated['title'],
          'start_at' => $startAt,
          'location' => $validated['location'],
          'description' => $validated['description'] ?? null,
          'status' => 'scheduled',
      ]);
  }
  ```

## 16. Soft-Deleted User Safeguard in Administrative Bulk Deletes
- **Pitfall**: Filtering queries with `whereHas('user', fn($q) => $q->where('role', 'user'))` causes bulk delete actions to silently skip records whose owner was soft-deleted (`trashed`), resulting in confusing messages like *"0 laporan berhasil dihapus"*.
- **Fix**: Remove restrictive active-user scoping during administrative cleanup routines so orphaned or demo/trashed records can be purged cleanly.
