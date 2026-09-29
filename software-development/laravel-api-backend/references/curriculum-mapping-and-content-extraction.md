# Curriculum Mapping & Content Extraction for Educational Games

## Sokrates CODESIGN Semester 1 → 4-Mission Mapping

**Source**: https://content2.sokrates.id/ (Moodle LMS)
**Courses**: SD CODESIGN I.1 through VI.1 (Grades 1-6)
**Pattern**: 14-16 pertemuan per kelas → 4 misi per kelas (~3-4 pertemuan per misi)

### Mapping Strategy
| Misi | Peran | Pertemuan Typical |
|------|-------|-------------------|
| 1 | Pondasi & Konsep Dasar | 1-3 (dasar teknologi/etika/OS) |
| 2 | Keterampilan Inti | 3-5 (tool/teknik spesifik) |
| 3 | Aplikasi Lanjutan | 5-7 (problem solving) |
| 4 | Proyek Akhir (Capstone) | 8-16 (proyek integratif) |

### Grade-by-Grade Mapping (Summary)

**Kelas 1 - Digi** (Petualangan Teknologi)
- M1: Teknologi Digital + Perangkat Keras + Berpikir Kritis
- M2: Algoritma Sehari-hari + Computational Thinking 1&2 + Logical Thinking
- M3: Mewarnai & Menggambar Dasar (Tema Jepang)
- M4: Proyek Gambar Sekolah + Kartu Ucapan + Pemandangan

**Kelas 2 - Nexa** (Penjaga Dunia Digital)
- M1: Etika Berinternet & Jejak Digital
- M2: WWW & Mesin Pencari + Pencarian Aman
- M3: Pengenalan Paint + Menggambar Binatang
- M4: Kombinasi Warna & Gradasi + Proyek Kreatif

**Kelas 3 - Byte** (Laboratorium Komputer)
- M1: Windows OS + Manajemen File/Folder
- M2: Jaringan Komunikasi + Aplikasi Presentasi
- M3: Tools Photoscape + Desain Kartu Ucapan
- M4: Proyek Desain Digital Lanjutan

**Kelas 4 - Guard** (Cyber Safety Mission)
- M1: Internet Aman & Proteksi Akun (Strong Password)
- M2: Bullying vs Cyberbullying (STOP & REPORT)
- M3: Computational Thinking (Dekomposisi & Abstraksi)
- M4: Blockly Games (Loop, Conditional, Visual Programming)

**Kelas 5 - Nova** (Digital Explorer)
- M1: Dampak Teknologi + E-Waste (3R: Reduce/Reuse/Recycle)
- M2: Karya dari E-Waste (Daun Ulang Kreatif)
- M3: Video Editing Dasar (Movie Maker: Cut, Transition, Text)
- M4: Produksi Film (Pra/Produksi/Pasca + Video Profil)

**Kelas 6 - Orbit** (Digital Master Mission)
- M1: Arsitektur Jaringan (Client-Server, Router/Switch)
- M2: ISP & Search Engine (Crawling → Indexing → Ranking)
- M3: Cyber Security (Malware, Phishing) + Biometrik
- M4: Database (Field/Record, Tipe Data) + Form Input

---

## SCORM Content Extraction from Moodle (Sokrates)

### Technique: Browser Console Decompression

iSpring SCORM packages embed content in `presInfo` (zlib-compressed JSON):

```javascript
// 1. Get the SCORM player page
const html = await fetch('https://content2.sokrates.id/pluginfile.php/XXX/mod_scorm/content/2/res/index.html').then(r=>r.text());

// 2. Extract base64 presInfo
const b64 = html.match(/var presInfo = "([^"]+)"/)[1];

// 3. Decompress (zlib/deflate)
const bin = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
const ds = new DecompressionStream('deflate');
const json = await new Response(new Blob([bin]).stream().pipeThrough(ds)).text();
const data = JSON.parse(json);

// 4. data.s contains slides with .s (JS file), .c (CSS), .T (thumbnail)
//    Slide content in data/slideN.js via loadHandler
```

### Course Structure Discovery

```javascript
// Get all sections with expandall=1
const html = await fetch(`https://content2.sokrates.id/course/view.php?id=${courseId}&expandall=1`).then(r=>r.text());
const doc = new DOMParser().parseFromString(html,'text/html');
const sections = Array.from(doc.querySelectorAll('.sectionname, [data-sectionname]'))
  .map(e=>e.innerText.trim())
  .filter(t=>t.toUpperCase().includes('PERTEMUAN'));

// Get activities per section
const items = Array.from(sec.querySelectorAll('.activityinstance, .instancename'))
  .map(a=>a.innerText.trim().replace(/\s+/g,' '));
```

### Key URLs Pattern
- Course: `https://content2.sokrates.id/course/view.php?id={496-501}`
- Section: `...&section={3-15}`
- SCORM: `https://content2.sokrates.id/mod/scorm/view.php?id={activityId}`
- SCORM Player: `https://content2.sokrates.id/pluginfile.php/{fileId}/mod_scorm/content/2/res/index.html`

---

## Comprehensive Seeder Pattern (Mission + Material + Quiz + Questions)

Single seeder creates full educational content graph:

```php
foreach ($missionsData as $grade => $gData) {
    foreach ($gData['missions'] as $mNum => $mData) {
        // 1. Mission
        $mission = Mission::firstOrCreate(
            ['grade_level'=>$grade, 'mission_number'=>$mNum],
            ['title'=>$mData['title'], 'subtitle'=>$mData['subtitle'], ...]
        );
        
        // 2. Material
        Material::firstOrCreate(
            ['grade_level'=>$grade, 'mission_number'=>$mNum],
            ['title'=>$mData['material_title'], 'content'=>$mData['material_content']]
        );
        
        // 3. Quiz
        $quiz = Quiz::firstOrCreate(
            ['grade_level'=>$grade, 'mission_number'=>$mNum, 'target_class'=>'all'],
            ['title'=>"Kuis {$mData['title']}", 'is_published'=>true]
        );
        
        // 4. Questions + Options
        foreach ($questionsSeed as $qData) {
            $question = Question::firstOrCreate(
                ['quiz_id'=>$quiz->id, 'text'=>$qData['text']],
                ['type'=>'multiple_choice', 'difficulty'=>$qData['difficulty'], ...]
            );
            foreach ($qData['options'] as $idx=>$opt) {
                QuestionOption::firstOrCreate(
                    ['question_id'=>$question->id, 'option_text'=>$opt['text']],
                    ['is_correct'=>$opt['correct'], 'order_value'=>$idx+1]
                );
            }
        }
    }
    // 5. Competency per grade
    Competency::firstOrCreate(...);
}
```

### Idempotency
- Use `firstOrCreate(['unique_fields'], ['defaults'])` everywhere
- Run `php artisan migrate:fresh --seed` for clean rebuilds
- SQLite CHECK constraints: question `type` must match enum (`multiple_choice`, `true_false`, `classification`, `matching`, `ordering`, `case_study`)

---

## Design Token Integration (gradeThemes.js)

Each grade has consistent visual identity across all missions:

```javascript
// resources/js/data/gradeThemes.js
export const gradeThemes = {
  1: { character:'Digi', theme:'Petualangan Teknologi', accent:'#06B6D4', color:'cyan', emoji:'🤖', ... },
  2: { character:'Nexa', theme:'Penjaga Dunia Digital', accent:'#8B5CF6', color:'violet', emoji:'🧩', ... },
  3: { character:'Byte', theme:'Laboratorium Komputer', accent:'#F59E0B', color:'amber', emoji:'💾', ... },
  4: { character:'Guard', theme:'Cyber Safety Mission', accent:'#EF4444', color:'red', emoji:'🛡️', ... },
  5: { character:'Nova', theme:'Digital Explorer', accent:'#10B981', color:'emerald', emoji:'🚀', ... },
  6: { character:'Orbit', theme:'Digital Master Mission', accent:'#6366F1', color:'indigo', emoji:'🛰️', ... },
};
```

Usage in components:
```jsx
const theme = getTheme(gradeLevel);
// theme.accent, theme.emoji, theme.character, theme.borderClass, theme.textClass
```

---

## Verification Checklist

After curriculum update:
- [ ] `php artisan migrate:fresh --seed` succeeds
- [ ] `php artisan test` → 8 passed (56 assertions)
- [ ] `npm run build` succeeds
- [ ] Visual check: Landing cards show correct grade themes
- [ ] MissionIntro shows correct mascot + material
- [ ] QuestionEngine loads questions without answer keys
- [ ] MissionCheckpoint roadmap uses grade theme (not hardcoded)
- [ ] Teacher dashboard GradesView/EvaluationView render data
- [ ] Cloudflare Tunnel HTTPS works (URL::forceScheme('https'))

---

## Related Files

- `database/seeders/DatabaseSeeder.php` — Full implementation
- `resources/js/data/gradeThemes.js` — Visual tokens
- `resources/js/components/mission/MissionCheckpoint.jsx` — Uses gradeLevel prop
- `app/Providers/AppServiceProvider.php` — HTTPS force for tunnel
- `app/Functions/LoadMissionContent.php` — Server-side content loading