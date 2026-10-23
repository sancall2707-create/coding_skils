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

### 6. Dual-Logo Formal Header Pattern (Kop Surat Resmi)
- For formal religious / institutional documents representing a joint committee or division:
  - Left: Main congregation / parent organization seal (`logo-fic.png`, 58px).
  - Center: Document title (navy uppercase bold) + institutional subtitle + division name.
  - Right: Program / committee seal (`logo-tppbm.png`, 58px).
  - Divider: Double horizontal rule (`border-top: 2.5px solid #0E3366; border-bottom: 0.8px solid #0E3366; height: 2px; margin-bottom: 12px;`).

### 7. Dynamic Signatures Bound to RBAC Roles in Official Documents ("Tanda Tangan Raport Dinamis Berdasarkan Role Pengguna")
- **Problem**: Hardcoding signatory names (e.g., Chairman, Administrator Data) in official Blade views or PDF templates means that when personnel, provincial appointments, or administrators change, code edits are required across multiple files.
- **Pattern**:
  1. **Role Definition**: Add dedicated executive roles in RBAC (e.g., `admin_ketua_tppbm` alongside `admin` and `user`) in account creation (`users.create`) and account management (`users.account.edit`).
  2. **Role Inheritance**: In `RoleMiddleware`, ensure executive roles automatically inherit base administrative permissions:
     ```php
     if ($user->role === 'admin_ketua_tppbm' && in_array('admin', $roles, true)) {
         return $next($request);
     }
     ```
  3. **Dynamic Resolution**: In document builder/controller, dynamically query signatories by role with fallback:
     ```php
     $ketuaTppbm = User::where('role', 'admin_ketua_tppbm')->first() ?? User::where('username', 'galihsih')->first();
     $adminData = (Auth::check() && Auth::user()->role === 'super_admin') ? Auth::user() : User::where('role', 'super_admin')->first();

     $penandatangan = [
         'ketua_tppbm' => $ketuaTppbm?->name ?? 'Br. F.A. Galih Sih Hartanta, FIC',
         'admin_data' => $adminData?->name ?? 'Br. Andrias Purwanto, FIC',
     ];
     ```

### 8. Full Retract (Tarik) & Edit Lifecycle for Administrative Guidance Notes
- **Problem**: When mentors/administrators submit evaluations or guidance notes (`BruderNote` or `DirectMessage`), mistakes, typos, or wrong category classifications cannot be fixed if only a "store" action exists.
- **Pattern**:
  - Provide an inline history list directly below the creation form showing previously saved notes for that user.
  - Add **Edit** button leading to a dedicated edit view (`users.notes.edit`) with `PUT` update route.
  - Add **Tarik** button executing `DELETE` route with confirmation dialog (`onsubmit="return confirm('Tarik / hapus catatan ini?');"`).
  - Deleted notes immediately vanish from both the history list and Section I of the official printed Raport.

### 9. Differentiated User Directory Controls: Member Mentoring vs Administrator Management
- **Problem**: When user management directories (e.g. `/super-admin/users`) are expanded to display administrative accounts (`admin`, `admin_ketua_tppbm`, `super_admin`) alongside regular members (`user`), treating all rows identically produces confusion.
- **Pattern**:
  1. **Query Expansion with Separation**: Exclude administrative accounts from member progress cards while listing all in user directories.
  2. **Card Metadata Differentiation**: Regular members show completion pill (e.g., `2/2 bulan ini`), whereas administrators show distinct role badges.
  3. **Action Button Differentiation**: Regular members receive mentoring buttons plus account management; administrators receive only account management without track record.
  4. **Self-Action Guard**: Enforce `abort_if($user->is($request->user()), 403);` to prevent accidental self-deactivation or deletion.

### 10. Client-Side Image Pre-Compression & Server Upload Limits for Profile Photos
- **Problem**: Phone camera photos exceed default PHP and controller limits (3–8 MB), causing silent upload failures.
- **Solution & Proven Pattern**:
  1. Raise PHP runtime limits (`upload_max_filesize = 20M`, `post_max_size = 25M`).
  2. Increase controller validation to 10 MB (`max:10240`).
  3. Client-side canvas compression: Intercept `<input type="file">`, downscale to max 1200px at 0.85 JPEG quality using an `HTMLCanvasElement`, and update `input.files` with a `DataTransfer` object before submit.

### 11. Headless Chrome PDF Generation on Ubuntu VPS (`google-chrome-stable` vs Snap Confinement)
- **Problem**: Generating server-side PDFs via headless browser fails on Ubuntu VPS when using Snap wrappers.
- **Solution**: Install native official `google-chrome-stable` deb directly via `dpkg`, and store HTML/PDF files in project storage paths (`storage_path('app/...')`) to bypass container namespace boundaries.

### 12. Member Personal Logbook Edit & Delete Lifecycle (Jurnal & Agenda Pribadi)
- On each card in member feeds (Jurnal, Agenda), provide paired `Edit` and `Hapus` actions scoped to owner (`abort_unless($record->user_id === auth()->id(), 404)`).

### 13. Persona-Oriented Administrative Navigation ("Beranda Bruder Muda" over "Lihat PWA")
- In administrative menus, use explicit domain/persona targets (e.g. **"Beranda Bruder Muda"**) rather than generic developer jargon ("Lihat PWA").

### 14. Administrative Broadcast Lifecycle & Media Cleanup (Sapaan & Pengumuman)
- Provide Create, Edit, Toggle Status, and Delete for broadcasts (`ProvincialMessage`), cleaning up associated images on disk during deletion.

### 15. Blade HTML Attribute Interpolation Pitfall (No Escaped Quotes `\'` in `{{ }}`)
- Never use backslash-escaped quotes `\'` inside Blade `{{ ... }}` within HTML attributes; use double quotes or keep confirm text neutral.

### 16. Administrative Mobile Bottom Navigation & Floating Action Button (FAB) Clearance
- Elevate `.fab` from `bottom: 24px` to `bottom: 80px` when mobile bottom navigation (`.sa-bottom-nav`) is present, and set container `padding-bottom: 76px`.

### 17. Retrospective Date Boundary Enforcement Across Formative Instruments
- For all retrospective logs (Bimbingan Rohani, Wawanhati, Jurnal Pengembangan Diri), enforce:
  - Frontend: `max="{{ date('Y-m-d') }}"` on `<input type="date">`.
  - Backend: `'before_or_equal:today'` validation rule.

### 18. Zero Fabricated Content in Official Export Documents
- Never render hardcoded placeholder advice in `@else` blocks of official reports. Render `-` or clean empty spaces when formators have not yet submitted notes.

### 19. Handling Explicit Design Review Asks vs Immediate Execution
- When the user asks for a review/opinion and explicitly instructs not to execute ("jangan kamu kerjakan langsung ya"), deliver a structured analytical assessment and wait for steerage before patching code.

### 20. Exclusive Tab Panes vs Tall Scrollable Anchor Tabs
- For long 5+ section forms, use real exclusive tab panes (`display: none` / `display: block`) with paired progressive step buttons (`Lanjut ke ... →`, `← ...`) and an `invalid` listener to auto-switch tabs on HTML5 validation failures.

### 21. Symmetrical & Uniform Action Button Alignment in Checklist Feeds
- Lock action pill buttons to fixed dimensions (`width: 76px; height: 32px`) across all checklist rows, enforce row `min-height: 54px`, and set `white-space: nowrap` on counter badges.

### 22. Clean Metric Summaries vs Cluttered Arithmetic Formulas
- Display clean KPI targets (`Akumulasi Tahun {{ now()->year }}: {{ $val }} / 24`) without exposing raw arithmetic breakdowns like `(2 × 12)`.

### 23. Auto-Submit Loading Spinner State on Mobile Forms
- Add a lightweight global submit listener in base layouts to disable buttons and display a spinner with *"Menyimpan..."*.

### 24. Future Date Filtering in Historical Reports & Resumes
- In formation and community assignment histories, filter out future years (`$year <= now()->year`) and render ongoing assignments as `[Year] - Sekarang`.

### 25. Custom Mobile Pagination Component vs Raw Laravel Links
- Override default unstyled pagination via `Paginator::defaultView('vendor.pagination.custom')` using compact 34x34px buttons to avoid raw SVG overflows.

### 26. Role-Aware Dynamic Category Labels in Content Feeds
- Dynamically bind broadcast labels (`Sapaan TPPBM` vs `Sapaan Provinsial`) based on author role, and auto-fill author names on dropdown change.

### 27. Compliance Metrics: Strictly Separate Core Mandatory Instruments from Optional Personal Journals
- Limit expected compliance to mandatory pillars (e.g. 1 Bimbingan + 1 Wawanhati = 2x/month, 24x/year). Exclude supplemental journals from the denominator.

### 28. Dual Time-Horizon Dashboard Gauges: Full-Year Cumulative vs Monthly Reset
- Left progress ring: Calculates cumulative formation from January 1st to the current date on the active year (Target: 24, percent = $(\text{actual} / 24) \times 100\%$, capped at 100%). Month changes do not reset this gauge.
- Right stats: Calculates actual monthly reports (Target: 2). Resets automatically to `0 / 2` (`0%`) when a new month begins.
- Use `Carbon::now('Asia/Jakarta')` and `config(['app.timezone' => 'Asia/Jakarta'])` to guarantee timezone alignment.

### 29. Omnipresent Member Agendas in Administrative Monitoring
- **Requirement**: All personal member schedules/agendas (`PersonalAgenda`) must be seamlessly aggregated into administrative oversight (Super Admin & TPPBM monitoring calendar `/super-admin/monitoring/agenda` and dashboard "Jadwal Pembinaan & Agenda Terdekat" widget) so mentors can remind members of upcoming commitments.
- **Pattern**:
  - In `MonitoringQuery::agendas()`: Query `PersonalAgenda` alongside `SpiritualGuidanceSchedule` and `WawanhatiSchedule`.
### 30. Dual Circular Progress Indicators Side-by-Side Pattern (Dashboard KPI)
When KPI cards track both long-term accumulation (e.g. annual target 24) and short-term compliance (e.g. monthly target 2), do not render a single lonely gauge leaving large empty gaps on the right.

**Markup & Styling Structure:**
```blade
<div class="progress-stat-card">
    <div class="stat-header">
        <span class="stat-title">Statistik Pembinaan Formatif</span>
        <span class="badge badge-scheduled">{{ $stats['label_bulan'] }} {{ now('Asia/Jakarta')->year }}</span>
    </div>
    <div class="stat-body" style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
        <!-- DUA CIRCULAR INDICATOR BERDAMPINGAN SECARA HORIZONTAL -->
        <div style="display:flex; align-items:center; gap:12px; flex-shrink:0;">
            <!-- Ring 1: Akumulasi Tahunan (Target 24) -->
            <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
                <div class="stat-ring" style="width:68px; height:68px; position:relative;">
                    <svg class="stat-ring-svg" viewBox="0 0 80 80" style="transform:rotate(-90deg); width:100%; height:100%;">
                        <circle class="stat-ring-circle-bg" cx="40" cy="40" r="32" style="fill:none; stroke:#E0E7FE; stroke-width:7;" />
                        <circle class="stat-ring-circle" cx="40" cy="40" r="32" style="fill:none; stroke:#1455C0; stroke-width:7; stroke-linecap:round; stroke-dasharray:201; stroke-dashoffset:{{ $ringOffsetTahun }}; transition:stroke-dashoffset 0.8s ease;" />
                    </svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:13px; font-weight:800; color:#1455C0;">
                        {{ $stats['persentase_tahun'] }}%
                    </div>
                </div>
                <span style="font-size:10px; font-weight:800; color:#475467; text-align:center; white-space:nowrap;">Akumulasi Tahunan</span>
                <span style="font-size:9.5px; font-weight:700; color:#1455C0; background:#EFF4FF; padding:1px 6px; border-radius:999px;">{{ $stats['pembinaan_tahun'] }}/24</span>
            </div>

            <!-- Ring 2: Bulan Berjalan (Target 2) -->
            <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
                <div class="stat-ring" style="width:68px; height:68px; position:relative;">
                    <svg class="stat-ring-svg" viewBox="0 0 80 80" style="transform:rotate(-90deg); width:100%; height:100%;">
                        <circle class="stat-ring-circle-bg" cx="40" cy="40" r="32" style="fill:none; stroke:#E0F2FE; stroke-width:7;" />
                        <circle class="stat-ring-circle" cx="40" cy="40" r="32" style="fill:none; stroke:#00838F; stroke-width:7; stroke-linecap:round; stroke-dasharray:201; stroke-dashoffset:{{ $ringOffsetBulan }}; transition:stroke-dashoffset 0.8s ease;" />
                    </svg>
                    <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:13px; font-weight:800; color:#00838F;">
                        {{ $stats['persentase_bulan'] }}%
                    </div>
                </div>
                <span style="font-size:10px; font-weight:800; color:#475467; text-align:center; white-space:nowrap;">Bulan Berjalan</span>
                <span style="font-size:9.5px; font-weight:700; color:#00838F; background:#E0F7FA; padding:1px 6px; border-radius:999px;">{{ $stats['pembinaan_bulan'] }}/2</span>
            </div>
        </div>

        <!-- DETAIL KANAN -->
        <div class="stat-info" style="flex:1; min-width:160px;">
            <div style="font-size:11px; font-weight:800; color:#667085; text-transform:uppercase;">Target Formasi Bulanan</div>
            <div style="font-size:22px; font-weight:800; color:#101828;">{{ $stats['pembinaan_bulan'] }} <span style="font-size:15px; font-weight:600; color:#667085;">/ 2 Laporan</span></div>
            <div style="font-size:11px; color:#475467; margin-top:3px;">Target 2 kali per bulan (Bimbingan Rohani &amp; Wawanhati Pilok).</div>
        </div>
    </div>

    <!-- DEDICATED FULL-WIDTH ACCUMULATION SUMMARY BAR -->
    <div class="stat-year-summary">
        <span>Akumulasi {{ $stats['label_tahunan'] }}</span>
        <strong>{{ $stats['pembinaan_tahun'] }} / 24</strong>
    </div>
</div>
```

```css
.stat-year-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed rgba(20, 85, 192, 0.18);
    font-size: 12px;
    font-weight: 700;
    line-height: 1.35;
    color: #1455C0;
}
.stat-year-summary span { min-width: 0; }
.stat-year-summary strong {
    flex-shrink: 0;
    font-size: 13px;
    font-weight: 800;
    color: #1455C0;
    background: #EFF4FF;
    border-radius: 999px;
    padding: 4px 10px;
    white-space: nowrap;
}
```

### 31. Service Worker Cache Invalidation on UI Assets Change
When updating CSS, Blade templates, or static images in a PWA:
- Browsers aggressively cache assets via the Service Worker cache (`STATIC_CACHE`, `PAGE_CACHE`).
- Always increment the cache version constant in `public/sw.js` (e.g. `const CACHE_VERSION = '20261023a';`).
- On activation, the Service Worker compares cache keys and purges all obsolete caches automatically (`caches.delete(cacheName)`), ensuring users immediately see updated font sizing, layout fixes, and styles upon next refresh.

### 32. Legibility & Font Sizing Standards for Continuous A4 Official Raport Documents
For continuous multi-page A4 documents printed via Chrome Headless:
- Base body font: `12px` (not 11px) with `line-height: 1.45`.
- Section headers: `13px` bold uppercase navy (`#0E3366`).
- Table contents and log cards: `11.5px` (not 10.5px) with `11px` reflection narrative text.
- Running footer text: `10.5px` (not 9.5px).
- This 1-point increase significantly improves readability when printed or viewed on mobile screens without causing premature page overflow.

### 33. Custom Domain Deployment: cPanel Shared Hosting vs VPS Architecture
- **Problem**: When a domain is registered on a shared hosting registrar (e.g. Domainesia/cPanel), users instinctively try to deploy the Laravel PWA via cPanel "Git Version Control" into `/home/user/public_html`.
- **Pitfalls**:
  1. *Chrome Headless Failure*: PWA features relying on server-side PDF engines (`RaportPdfPrinter` using `google-chrome-stable`) fail completely on cPanel shared hosting because users do not have root/sudo privileges to install Debian/Ubuntu packages.
  2. *SSL Version / Cipher Mismatch (`ERR_SSL_VERSION_OR_CIPHER_MISMATCH`)*: Accessing the domain before AutoSSL runs or while misconfigured results in SSL cipher handshake failure.
  3. *Security & Directory Traversal*: Deploying directly to `public_html` exposes `.env` and SQLite databases if the web server document root cannot be shifted to `/public`.
- **Pattern & Resolution (Keep VPS Engine + Direct DNS via Zone Editor)**:
  - Do not deploy Git to cPanel. Keep the full application, database, and background processes on the VPS.
  - In cPanel **Zone Editor** / Registrar DNS Management:
    1. Locate or create `A` record for `@` (domain.com) and `www`.
    2. Set Address / Value directly to the VPS public IP (e.g. `43.173.9.113`).
    3. Remove or replace default shared hosting IP (e.g. `202.155.137.49`).
  - On the VPS, configure Caddy or Nginx with automatic Let's Encrypt SSL:
    ```caddy
    formatio-fic.com, www.formatio-fic.com {
        reverse_proxy 127.0.0.1:8022
    }
    ```
  - Caddy automatically provisions and renews TLS certificates, eliminating `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` without manual intervention.

```bash
# Verify rendering on mobile viewport
browser_navigate http://localhost:8022/dashboard
browser_vision "verify dual circular gauges side-by-side on mobile without horizontal scroll"
```

