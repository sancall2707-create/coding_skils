---
name: educational-game-pwa
description: Full-stack pattern for building educational game PWAs with Laravel API backend and React frontend. Covers game loop, student session management without login, teacher dashboard, design system implementation, and security patterns for answer-key protection.
---

# Skill: Educational Game PWA (Laravel + React)

## Overview
Pattern for building gamified educational platforms for Indonesian elementary schools (SD Kelas 1–6) with:
- **Student Area**: No-login game loop using localStorage session tokens
- **Teacher Dashboard**: Authenticated CRUD for materials, quizzes, grading
- **Security**: Server-side answer key protection, score calculation 20–100 scale
- **Design System**: Grade-based theming (6 mascots), tactile gamified UI + SaaS teacher UI

## When to Use
- Building educational game platforms for schools
- Need student progress tracking without accounts
- Require teacher analytics dashboard
- Must protect answer keys from client exposure

## Architecture

### Backend (Laravel)
```
app/
├── Services/           # SessionAuth, ClassTarget, SessionScoring
├── Functions/          # LoadMissionContent, SubmitAnswer, FinalizeSession, GetSessionReview
├── Http/Controllers/Api/
│   ├── StudentApiController.php
│   └── TeacherApiController.php
└── Models/             # 14 Eloquent models
```

### Frontend (React + Vite)
```
resources/js/
├── app.jsx             # Router + AuthProvider + ProtectedRoute
├── pages/
│   ├── Home.jsx        # Game loop orchestrator
│   └── teacher/        # Dashboard tabs
├── components/
│   ├── mission/        # MissionIntro, QuestionEngine, Checkpoint, etc.
│   └── LandingPage.jsx
├── services/           # studentApi.js, teacherApi.js
├── context/AuthContext.jsx
├── components/ProtectedRoute.jsx
└── data/gradeThemes.js # 6 grade themes with mascots
```

## Key Patterns

### 1. Student Session (No Login)
```javascript
// Generate 32-byte token, store raw in localStorage, send SHA-256 hash to backend
const bytes = new Uint8Array(32);
crypto.getRandomValues(bytes);
const token = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
// Store { id, token } in localStorage as 'mpd_active_session'
```

### 2. Answer Key Protection
```php
// LoadMissionContent.php - strip keys before sending to client
foreach ($questions as $q) {
    foreach ($q->options as $opt) {
        unset($opt->is_correct, $opt->explanation);
    }
}
```

### 3. Score Calculation (Server-only)
```php
// SessionScoring.php - 20-100 scale
$score = 20 + round(($earned / $max) * 80);
```

### 4. Grade Theming
```javascript
// gradeThemes.js - 6 mascots with colors
1: Digi (Cyan) - Petualangan Teknologi
2: Nexa (Violet) - Penjaga Dunia Digital
3: Byte (Amber) - Laboratorium Komputer
4: Guard (Rose) - Cyber Safety Mission
5: Nova (Emerald) - Digital Explorer
6: Orbit (Indigo) - Digital Master Mission
```

### 5. Cloudflare Tunnel Mixed Content Fix
```php
// AppServiceProvider.php - force HTTPS behind proxy
if ($this->app->environment('production')) {
    URL::forceScheme('https');
    $this->app['request']->server->set('HTTP_X_FORWARDED_PROTO', 'https');
}
```

## Component Checklist

### Student Flow
- [ ] LandingPage with grade selection cards
- [ ] StudentForm (name + class dropdown)
- [ ] MissionIntro (material + mascot greeting)
- [ ] QuestionEngine (1 question at a time, tactile answer pills)
- [ ] Confetti on correct, shake on incorrect
- [ ] MissionCheckpoint (serpentine roadmap with 64px nodes)
- [ ] SessionDone (finalize → score → review → certificate)

### Teacher Dashboard
- [ ] Sidebar navigation (4 tabs)
- [ ] GradesView: sticky name column, score chips (<60, 60-74, 75-89, 90-100)
- [ ] MaterialsView: CRUD + search + grade/mission filter
- [ ] QuizzesView: CRUD + 6 question types + target class
- [ ] EvaluationView: competency mastery bars (12px gradient)

## Testing & QA
```bash
npm run build          # Frontend build
php artisan test       # Backend tests (8 tests, 56 assertions)
# Cloudflare tunnel for public testing
cloudflared tunnel --url http://127.0.0.1:8000
```

## Pitfalls & Fixes
| Issue | Fix |
|-------|-----|
| Mixed content (HTTPS page, HTTP assets) | `URL::forceScheme('https')` in AppServiceProvider |
| Card text truncation/misread words | Do not overuse `line-clamp` on short theme/subtitle labels; allow wrapping with `break-words`, adequate card width, and visual screenshot check so words like `Petualangan` / `Laboratorium` are not perceived as typos. |
| Table header overlap | `min-w-[1100px] table-auto` + `white-space: nowrap` on th/td |
| Tab click not working | Ensure `onClick={() => setActiveTab(tab.id)}` on button, not child spans |
| Target class "all" showing raw | Map to friendly label: `all` → `Semua Kelas` |
| Checkpoint roadmap switching grade themes | Pass `gradeLevel` into `MissionCheckpoint` and use `getTheme(gradeLevel)` for all 4 mission nodes |

## Dependencies
```json
{
  "react": "^18",
  "react-dom": "^18",
  "react-router-dom": "^6",
  "lucide-react": "^0.4",
  "@vitejs/plugin-react": "^4",
  "html2canvas": "^1",
  "jspdf": "^2",
  "canvas-confetti": "^1"
}
```

## References
- `references/moodle-sokrates-harvesting.md` - Extraction of Moodle sections & iSpring SCORM materials
- `references/design-system.md` - Full DESIGN.md token implementation
- `references/audit-checklist.md` - QA checklist from dogfood session
- `references/session-flow.md` - Student game loop state machine