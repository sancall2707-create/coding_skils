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
- **Problem 1 (Narrow Print Column)**: Mobile-first PWA shells constrain their root container (e.g. `.sa-container`) to `max-width: 480px`. During browser print / "Save as PDF", if this container is not overridden, the output prints as an awkward ~12cm strip down the center of an A4 sheet with huge blank margins on both sides.
- **Problem 2 (Missing Badge Background Colors)**: Browsers disable background graphics by default during printing, stripping red/green status badges and table headers to white/invisible backgrounds.
- **Pattern & Fix**:
  1. **Container Breakout in `@media print`**:
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
         .raport-sheet {
             border: none !important;
             box-shadow: none !important;
             padding: 0 !important;
             margin: 0 !important;
             width: 100% !important;
             max-width: 100% !important;
         }
     }
     ```
  2. **Custom A4 Document Margins (`@page`)**:
     ```css
     @page {
         size: A4 portrait;
         margin: 1.5cm 1.5cm 1.5cm 2cm; /* Top 1.5cm, Right 1.5cm, Bottom 1.5cm, Left 2.0cm (binding clearance) */
     }
     ```
  3. **Print-Safe Badges & Status Indicators**:
     - Apply `-webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;` directly to badge elements and table headers.
     - Pair background colors with matching borders and high-contrast text:
       - Done: `background-color: #DCFCE7 !important; color: #166534 !important; border: 1px solid #86EFAC !important;` (`✔ TELAH TERLAKSANA`).
       - Not Done: `background-color: #FEE2E2 !important; color: #991B1B !important; border: 1px solid #FCA5A5 !important;` (`✘ BELUM / TIDAK TERLAKSANA`).
       - Recorded: `background-color: #E0F2FE !important; color: #0369A1 !important; border: 1px solid #BAE6FD !important;` (`TERCATAT`).
  4. **Continuous Flow vs Artificial Page Breaks (Paper Efficiency)**:
     - **Anti-Pattern**: Forcing hard page breaks (`.page-break { page-break-after: always !important; }`) between every section. When filtering sparse data (e.g. only 1–2 months), this causes large, unsightly blank white spaces at the bottom of printed sheets and wastes paper.
     - **Best Practice (Continuous Document Flow)**: Merge sections into one unified document container. Allow tables, logs, and sections to flow naturally from page to page.
     - **Prevent Splitting without Artificial Breaks**:
       - `tr { page-break-inside: avoid; break-inside: avoid; }` (never split a table row horizontally across page boundaries).
       - `.raport-log-card, .raport-card-box { page-break-inside: avoid; break-inside: avoid; }` (keep individual cards intact).
       - `.raport-section-title { page-break-after: avoid; break-after: avoid; }` (never orphan a section header at the bottom edge).
       - `.raport-signatures { page-break-inside: avoid; break-inside: avoid; }` (keep legal signature blocks together).
     - **Header & Footer**: Keep the official organization kop at the top of the document. Keep the document footer (`Raport Pendampingan - [Name] | Tim Pemantap Panggilan`) at the bottom with clear borders and branding.

### 5. Collision-Proof Per-Page Footers, Real Page Numbers & Continuous Documents ("Posisi Footer Jangan Sampai Menabrak, Halaman Bukan 0, & Footer Terakhir Tetap di Dasar Kertas")
- **The Pitfall of `position: fixed; bottom: 0` in Print**:
  When you set `position: fixed; bottom: 0` during browser or Android mobile printing (Brave, Chrome, Android Print Spooler), the footer is removed from normal flow. The browser fills the printable area with table rows and text all the way to `bottom: 0`. As a result, the fixed footer renders **directly on top of the document content (smashing/colliding into table rows, borders, and text)**.
- **The Pitfall of `display: table-footer-group` (`tfoot`)**:
  While `tfoot` avoids collision, it introduces two severe real-world bugs in browser PDF printing:
  1. *Footer floats up on the last page*: On the final page, `tfoot` is placed immediately below the last row of `tbody`. If the page only has signatures, the footer floats in the middle of the paper, leaving the lower half completely empty.
  2. *`counter(page)` evaluates to 0*: Chromium Skia/PDF does not support CSS `counter(page)` inside table cells or regular DOM elements. It renders as `Halaman 0` on every single printed page!
- **The Pitfall of Hardcoded Static Page Divs**:
  Hardcoding 4 separate `.raport-page` divs fails when data volume is dynamic (e.g. 10–12 months of logs vs 1–3 months). Dense data spills across multiple physical pages while intermediate pages lose their footer, and sparse data leaves massive empty white spaces.
- **The Definitive Solution: Client-Side Dynamic A4 Paginator (`paginateRaport`)**:
  Store clean content blocks in a hidden `#raportSource`. On page load, window resize, and `beforeprint`, measure each block's actual height in a hidden test container, grouping blocks into `.raport-page` containers with a safe threshold of ~820px (well within A4's 1009px printable height).
  ```javascript
  function paginateRaport() {
      const source = document.getElementById('raportSource');
      const target = document.getElementById('raportContainer');
      if (!source || !target) return;

      const blocks = Array.from(source.children).map(el => el.cloneNode(true));
      const MAX_CONTENT_HEIGHT = 820; // Safe height per A4 page in px at 96 DPI
      const pageGroups = [];
      let currentGroup = [];
      let currentHeight = 0;

      const testContainer = document.createElement('div');
      testContainer.style.width = (target.offsetWidth || 760) + 'px';
      testContainer.style.visibility = 'hidden';
      testContainer.style.position = 'absolute';
      testContainer.style.top = '-9999px';
      document.body.appendChild(testContainer);

      for (let i = 0; i < blocks.length; i++) {
          const b = blocks[i];
          testContainer.appendChild(b);
          const h = b.offsetHeight || 50;

          // Prevent orphaned section headers
          let extra = 0;
          if (b.classList && b.classList.contains('raport-section-title') && (i + 1) < blocks.length) {
              const nextB = blocks[i + 1].cloneNode(true);
              testContainer.appendChild(nextB);
              extra = nextB.offsetHeight || 50;
              testContainer.removeChild(nextB);
          }

          if ((currentHeight + h + extra) > MAX_CONTENT_HEIGHT && currentGroup.length > 0) {
              pageGroups.push(currentGroup);
              currentGroup = [b];
              currentHeight = h;
          } else {
              currentGroup.push(b);
              currentHeight += h;
          }
      }
      if (currentGroup.length > 0) pageGroups.push(currentGroup);
      document.body.removeChild(testContainer);

      // Rebuild target pages
      target.innerHTML = '';
      pageGroups.forEach((group, index) => {
          const pageEl = document.createElement('div');
          pageEl.className = 'raport-page';

          const bodyEl = document.createElement('div');
          bodyEl.className = 'raport-page-body';
          group.forEach(el => bodyEl.appendChild(el));
          pageEl.appendChild(bodyEl);

          // Pinned footer at the bottom of EVERY page
          const footerEl = document.createElement('div');
          footerEl.className = 'raport-page-footer';
          footerEl.innerHTML = `
              <div style="font-weight:700;">Raport Bruder Muda - ${RAPORT_NAMA}</div>
              <div style="font-weight:700;">Halaman ${index + 1}</div>
          `;
          pageEl.appendChild(footerEl);
          target.appendChild(pageEl);
      });
  }
  ```
  - In CSS:
    ```css
    @page {
        size: A4 portrait;
        margin: 1.5cm 1.5cm 1.5cm 2.0cm; /* Top 1.5cm, Right 1.5cm, Bottom 1.5cm, Left 2.0cm */
    }

    .raport-page {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 25.8cm;
        box-sizing: border-box;
        margin-bottom: 24px;
        background: #ffffff;
    }

    .raport-page-body {
        flex: 1;
    }

    .raport-page-footer {
        flex-shrink: 0;
        border-top: 1px solid #D1D5DB;
        padding-top: 6px;
        margin-top: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 9.5px;
        color: #6B7280;
        background: #ffffff;
    }

    @media print {
        .raport-page {
            min-height: 25.8cm !important;
            height: 25.8cm !important;
            margin-bottom: 0 !important;
            page-break-after: always !important;
            break-after: page !important;
        }

        .raport-page:last-child {
            page-break-after: auto !important;
            break-after: auto !important;
        }

        .raport-page-footer {
            border-top: 1px solid #D1D5DB !important;
            background: #ffffff !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
    ```
- **Why This Guarantees Success**:
  1. **Continuous Flow without Empty Pages**: Blocks fill each page up to the safe threshold, dynamically expanding to 3, 4, 5, or 6 pages as data requires without giant empty spaces.
  2. **Footer Always at the Very Bottom**: Thanks to `display: flex; flex-direction: column; justify-content: space-between; min-height: 25.8cm;`, the footer on the last page is **anchored at the very bottom of the A4 paper (at 25.8cm)**, never floating up beneath the signatures!
  3. **Zero Collision**: Content sits inside `raport-page-body` and footer is a separate flex-child with dedicated padding and margin. Content can never overlap the footer.
  4. **Real Page Numbers (Never 0)**: Page numbers are rendered as literal HTML text (`Halaman 1`, `Halaman 2`, etc.), completely immune to the Chromium `counter(page)` bug.

### 6. Dual-Logo Formal Header Pattern (Kop Surat Resmi)
- For formal religious / institutional documents representing a joint committee or division:
  - Left: Main congregation / parent organization seal (`logo-fic.png`, 58px).
  - Center: Document title (navy uppercase bold) + institutional subtitle + division name.
  - Right: Program / committee seal (`logo-tppbm.png`, 58px).
  - Divider: Double horizontal rule (`border-top: 2.5px solid #0E3366; border-bottom: 0.8px solid #0E3366; height: 2px; margin-bottom: 12px;`).


