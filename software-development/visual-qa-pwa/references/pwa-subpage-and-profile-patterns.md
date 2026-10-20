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
