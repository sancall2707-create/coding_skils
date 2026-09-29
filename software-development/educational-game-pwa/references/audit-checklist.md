# Educational Game PWA Audit Checklist

Use after implementing Laravel + React educational game features, before saying done.

## Public preview
- If user expects a tester link, expose a public URL when feasible (Cloudflare Tunnel acceptable).
- Open the public URL in browser and verify actual render, not just local build.
- Check console after navigation and key interactions.
- Blank page behind HTTPS tunnel often means mixed-content assets (`http://.../build/...`); fix Laravel URL scheme/proxy handling.

## Student flow
- Start with fresh `localStorage`; test resume modal separately.
- Verify `BUKAN SAYA` removes only `localStorage`, never DB records.
- Complete at least one mission path if seed data allows.
- Check labels: `Kelas` = grade/class, `Misi` = mission progress. Do not let roadmap imply advancing from Kelas 1 to Kelas 2.
- Checkpoint roadmap must use the student's `grade_level` theme for all 4 mission nodes.

## Teacher dashboard
- Long names must truncate or wrap within sidebar/cards; never overflow.
- Tables need min-width, horizontal scroll, non-wrapping headers/cells, and clear padding.
- Long seeded lists (24 materials/quizzes) need search/filter by grade/mission before being accepted.
- Internal values like `all` must be localized for UI (`Semua Kelas`).
- Destructive actions need confirmation.

## Visual QA
- Inspect cards for clipped subtitles, icon/text collisions, cramped footers, and inconsistent badges.
- Verify score chips/status badges are readable and aligned.
- Re-run `npm run build` and backend tests after UI changes.
