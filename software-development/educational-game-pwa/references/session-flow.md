# Student Game Loop State Machine

## Flow States
`Landing` → `StudentForm` → `MissionIntro` → `QuestionEngine` → `MissionCheckpoint` → `SessionDone` → `Review/Certificate`

## LocalStorage Sesi Siswa
Key: `mpd_active_session`
Payload:
```json
{
  "id": 1,
  "token": "a1b2c3...32bytes-hex",
  "student_name": "Budi",
  "class_name": "1A",
  "grade_level": 1,
  "current_mission": 1
}
```

## Backend RPC Endpoints
- `POST /api/student/session` - Create session (sends `session_token_hash`)
- `POST /api/student/session/resume` - Check in-progress session status
- `POST /api/student/mission/load` - Get material & questions (no answer keys)
- `POST /api/student/answer/submit` - Grade single answer (returns is_correct + explanation)
- `POST /api/student/session/finalize` - Finalize all 4 missions, compute 20-100 score
- `POST /api/student/session/review` - Get false answer explanations post-finalize

## Resume Flow Logic
1. On page load, check `localStorage`.
2. If `mpd_active_session` exists, call `/resume`.
3. If status is `in_progress`, open modal "Lanjutkan Misi?".
4. "BUKAN SAYA" button: `localStorage.removeItem('mpd_active_session')`. DB untouched.
5. "LANJUTKAN" button: jump directly to `current_mission`.
6. "Kembali ke Beranda" button at end of game loop: clear `localStorage` so next lab student can use device.