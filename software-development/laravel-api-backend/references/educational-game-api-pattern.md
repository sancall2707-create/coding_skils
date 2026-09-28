# Educational Game API Pattern (Laravel)

Use when building a student game / quiz backend where students do not log in, but teacher/admin dashboard uses Sanctum.

## Core Pattern
- Student area: anonymous session + raw token stored on device + SHA-256 token hash stored server-side.
- Teacher/admin area: normal `users` table + `role` field + Sanctum bearer token.
- Never expose answer keys in student `loadMissionContent` response.
- Send only question text, points, difficulty, and sanitized option text/id to browser.
- Return `explanation` only after `submitAnswer`, and full correct answer review only after session completed.
- Keep official score server-side only.

## Useful Tables
- `school_classes`: class label (`1A`) + `grade_level`.
- `missions`: grade + mission metadata.
- `materials`: grade + mission + published content.
- `competencies`: grade-level competencies.
- `quizzes`: grade + mission + `target_class` (`all`, `Semua Kelas <N>`, or exact class).
- `questions`, `question_options`: keep `is_correct`, `pair_key`, `order_value` server-side.
- `game_sessions`: anonymous student identity + class + token hash + status/current position.
- `student_answers`, `checkpoints`, `student_results`, `competency_results`.

## Services Worth Extracting
- `SessionAuth`: generate raw token, hash with SHA-256, verify via `hash_equals`.
- `ClassTarget`: select class-specific quiz before general quiz.
- `SessionScoring`: dedupe answers by `question_id`, compute score `round(20 + earned/max * 80)`, persist result idempotently, build review list only after completed.

## Testing Pattern
Create one feature test for full flow:
1. seed classes, teacher user, missions, quizzes, questions;
2. create student session;
3. resume session;
4. load mission content and assert no answer-key fields exposed;
5. submit all mission answers;
6. finalize;
7. fetch review/certificate payload;
8. login teacher via Sanctum;
9. read grades, detail, answer history, evaluation.

With in-memory test DB, add to the test class:

```php
use RefreshDatabase;
protected bool $seed = true;
```

## Pitfalls
- If you alter the original `users` migration after it already ran locally, run `php artisan migrate:fresh --seed` in dev/test, or create a new migration for non-destructive environments.
- Do not call `last()` directly on an Eloquent relation builder. Use `->get()->last()` or query ordering with `first()`.
- Controller delete methods must accept `Request $request` if they call authorization helpers using `$request`.
- Route cache can hide API route edits. Run `php artisan route:clear && php artisan route:cache` after changing API routes when verifying.
