# Misi Pintar Digital — Database Schema & Seeder Pattern

## Entities (14 tables)
| Table | Purpose |
|-------|---------|
| users | Auth + roles (admin, teacher, user) |
| school_classes | Kelas 1A–6C, grade_level 1–6 |
| missions | 4 misi per jenjang, theme & karakter |
| materials | Materi pembelajaran per misi |
| competencies | Kompetensi per jenjang |
| quizzes | Kuis per misi + target_class (all / specific) |
| questions | Soal 6 tipe, points, difficulty, mission_number |
| question_options | Pilihan jawaban + is_correct, pair_key, order_value |
| game_sessions | Sesi siswa anon: token_hash, current_mission, status |
| student_answers | Jawaban per soal, is_correct, points_earned |
| checkpoints | Progres per misi |
| student_results | Hasil akhir (skor 20–100) |
| competency_results | Mastery % per kompetensi per sesi |
| teachers | Profil guru linked to users |

## Key Design Decisions
- **Token security**: 32-byte random token on device; only SHA-256 hash stored (`session_token_hash`).
- **Class targeting**: `quizzes.target_class` = null / 'all' / '1A' — server-side selection.
- **Scoring**: Server-only; `StudentResult` & `CompetencyResult` are source of truth.
- **Idempotent seeding**: `firstOrCreate` on unique keys; run with `php artisan migrate:fresh --seed`.

## Seeder Highlights
```php
// Users
User::firstOrCreate(['email' => 'admin@misipintar.id'], ['role' => 'admin']);
User::firstOrCreate(['email' => 'guru@misipintar.id'], ['role' => 'teacher']);

// Classes 1A–6C
for ($g=1;$g<=6;$g++) foreach (['A','B','C'] as $p) SchoolClass::firstOrCreate(['name'=>"$g$p",'grade_level'=>$g]);

// Missions, Materials, Competencies, Quizzes, Questions per grade
foreach ($gradeThemes as $grade=>$t) {
  for ($m=1;$m<=4;$m++) { Mission::...; Material::...; }
  $comp = Competency::firstOrCreate(['grade_level'=>$grade,'code'=>"KOMP-GR$grade-01"], ...);
  for ($m=1;$m<=4;$m++) {
    $quiz = Quiz::firstOrCreate(['grade_level'=>$grade,'mission_number'=>$m,'title'=>...], ['competency_id'=>$comp->id,'target_class'=>'all']);
    // add sample questions (multiple_choice, true_false)
  }
}
```