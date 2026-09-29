# Harvesting Moodle / Sokrates Content for Educational Games

## Overview
Technique for pulling structured course content, sections, and SCORM/iSpring materials from Moodle-based LMS sites (e.g. `sokrates.id`).

## 1. Moodle Course & Section Extraction
- **Course View Parameter**: Adding `&expandall=1` to `/course/view.php?id=<ID>&expandall=1` expands all section DOM nodes without requiring interactive clicks.
- **Section Parsing (Browser Console / Fetch)**:
  ```js
  const url = `https://domain.com/course/view.php?id=${courseId}&expandall=1`;
  const html = await (await fetch(url, { credentials: 'include' })).text();
  const doc = new DOMParser().parseFromString(html, 'text/html');
  const sections = Array.from(doc.querySelectorAll('.section')).map(sec => ({
    title: sec.querySelector('.sectionname, [data-sectionname]')?.innerText?.trim(),
    items: Array.from(sec.querySelectorAll('.activityinstance, .activity-item')).map(a => a.innerText.trim())
  }));
  ```

## 2. iSpring / SCORM Decompression
- SCORM packages exported from iSpring contain `var presInfo = "..."` in `index.html`.
- `presInfo` is base64-encoded zlib stream (Deflate).
- Decompress in browser:
  ```js
  const b64 = presInfoMatch[1];
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const text = await new Response(new Blob([bin]).stream().pipeThrough(new DecompressionStream('deflate'))).text();
  const json = JSON.parse(text);
  // json.s contains slide lists, json.t contains presentation title
  ```

## 3. Workflow for User Material Ingestion
1. Ask/confirm mapping strategy when course structure (e.g. 6-8 meetings) differs from app structure (e.g. 4 missions).
2. Login to external platform via browser tool.
3. Extract meeting topics per grade/course.
4. Confirm mapping with user before bulk DB seeding or app updates.
