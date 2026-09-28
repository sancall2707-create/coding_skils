# Educational Game Frontend Pattern (React + Vite + Tailwind + PWA)

## Overview
Frontend implementation for "Misi Pintar Digital" — an Indonesian elementary CS education game (Kelas 1-6) with:
- **Student Area (no login)**: localStorage session, 32-byte token + SHA-256 hash, 4 missions × (materi + kuis)
- **Teacher Dashboard (Sanctum auth)**: CRUD materi/kuis, 6 question types, grade evaluation, student results

## Stack
- React 18 + Vite + React Router 6
- Tailwind CSS v4 (custom theme tokens from DESIGN.md)
- `html2canvas` + `jspdf` for certificate PDF export
- `canvas-confetti` for correct-answer celebration
- Laravel backend API + Sanctum

## Key Patterns

### 1. Design System Integration (DESIGN.md → Tailwind)
`resources/css/app.css` defines all design tokens as CSS custom properties:
```css
@theme {
  --font-display: 'Plus Jakarta Sans';
  --font-body: 'Inter';
  --color-primary-600: #2563EB;
  --color-amber-500: #F59E0B;
  --color-emerald-500: #10B981;
  --color-rose-500: #F43F5E;
  --color-grade-1: #06B6D4;  /* Digi */
  --color-grade-2: #8B5CF6;  /* Nexa */
  /* ... */
}
```
Utility classes expose tactile 3D buttons (`.btn-hero-primary`), checkpoint nodes (`.checkpoint-node`), answer pills (`.answer-pill`), mastery bars, score chips.

### 2. Grade-Themed UI (`resources/js/data/gradeThemes.js`)
```js
export const gradeThemes = {
  1: { character: 'Digi', emoji: '🤖', accent: '#06B6D4', borderClass: 'border-cyan-500', ... },
  // 2..6
};
```
Used in `MissionIntro`, `MissionCheckpoint`, `AppreciationCertificate`, `LandingPage`.

### 3. Student Session (no login)
```js
// StudentForm.jsx
const { rawToken, hashHex } = await generateRandomTokenAndHash();
await createSession(name, classId, hashHex);
localStorage.setItem('mpd_active_session', JSON.stringify({ id, token: rawToken, ... }));
```
Backend stores only SHA-256 hash; client keeps raw token in localStorage.

### 3a. Resume + "Bukan Saya"
`Home.jsx` on mount calls `resumeSession(id, token)` → if `in_progress`, shows modal with "Lanjutkan" / "BUKAN SAYA" (only clears localStorage).

### 4. Mission Flow
`MissionIntro` → `QuestionEngine` (one question at a time) → `MissionCheckpoint` (serpentine roadmap) → `SessionDone` → `ReviewAnswers` / `AppreciationCertificate`.

`QuestionEngine`:
- Confetti on correct: `canvas-confetti`
- Gentle shake on incorrect: CSS `animate-shake`
- Answer pills: 56px min-height, rounded-full, selected/correct/incorrect states

### 5. Teacher Dashboard
Sidebar tabs: Nilai Siswa, Kelola Materi, Kelola Kuis, Evaluasi Kompetensi.
- `GradesView`: sticky student-name column, score chips (`chip-remedial`..`chip-mastery`)
- `QuizzesView`: CRUD + 6 question type editor
- `EvaluationView`: 12px gradient mastery bars
- `MaterialsView`: CRUD with publish toggle

### 6. Certificate PDF
`AppreciationCertificate` uses `html2canvas` → `jspdf` for landscape PDF export. Gold-leaf border, mascot celebration, watermark.

### 7. HTTPS Behind Tunnel (Mixed Content Fix)
`AppServiceProvider.php`:
```php
if ($this->app->environment('production') || request()->header('x-forwarded-proto') === 'https') {
    URL::forceScheme('https');
}
```

## Build & Deploy
```bash
npm run build          # Vite production build
php artisan serve --host=0.0.0.0 --port=8000
cloudflared tunnel --url http://127.0.0.1:8000   # public HTTPS URL
```

## Test Suite
- `ApiFlowTest`: full student + teacher workflow
- `BackendFunctionSecurityTest`: 403 wrong token, 400 review before complete, no answer keys, idempotent duplicate, 400 finalize before all answered

All 8 tests pass (56 assertions).