---
name: vanilla-pwa-speech-translation
description: Build installable PWAs with Web Speech API (SpeechRecognition + SpeechSynthesis) using vanilla HTML/CSS/JS + lightweight PHP backend. Covers secure-context HTTPS via Cloudflare Tunnel, mobile-first dark UI, service worker, manifest, translation API abstraction, and localStorage history.
---

# Skill: Vanilla PWA Speech Translation

## Overview
Pattern for building real-time speech-to-text translation PWAs without heavy frameworks:
- **Frontend**: Vanilla HTML/CSS/JS (ES6 modules optional)
- **API**: PHP router + endpoint files (can swap to Node/Go/Python)
- **Speech**: Web Speech API `SpeechRecognition` + `SpeechSynthesis`
- **PWA**: manifest.json + service worker (workbox or custom)
- **HTTPS**: Cloudflare Tunnel for local dev (mic requires secure context)

## When to Use
- Rapid prototyping of voice-enabled PWAs
- Lightweight projects where Laravel/React overhead is unjustified
- Offline-first translation/history with localStorage
- Indonesian-language UI requirements (mobile-first, dark theme)

## Architecture

```
/project-root
├── public/
│   ├── index.html          # SPA entry
│   ├── css/app.css         # Dark mobile-first theme
│   ├── js/app.js           # Speech API + UI state + TTS
│   ├── manifest.json       # PWA manifest
│   ├── sw.js               # Service worker
│   └── icons/              # 72-512px PNG icons
├── api/
│   └── translate.php       # POST /api/translate endpoint
├── router.php              # PHP built-in server router
└── .env (optional)         # Provider keys for Tahap 3+
```

## Key Patterns

### 1. SpeechRecognition Setup (Continuous, Interim Results)
```javascript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-US'; // BCP-47 from language selector

recognition.onresult = (event) => {
  let interim = '', final = '';
  for (let i = event.resultIndex; i < event.results.length; ++i) {
    const t = event.results[i][0].transcript;
    event.results[i].isFinal ? final += t : interim += t;
  }
  state.interimText = interim;
  if (final.trim()) { state.finalText = final.trim(); onSentenceComplete(final.trim()); }
  renderTranscript();
};
recognition.onend = () => { if (state.isListening) recognition.start(); else updateUI(); };
```

### 2. Language → BCP-47 Mapping
```javascript
const LANG_MAP = {
  auto: { bcp47: 'en-US', label: 'Auto', flag: '🌐' },
  en:   { bcp47: 'en-US', label: 'English',  flag: '🇺🇸' },
  ja:   { bcp47: 'ja-JP', label: 'Japanese', flag: '🇯🇵' },
  ko:   { bcp47: 'ko-KR', label: 'Korean',   flag: '🇰🇷' },
  zh:   { bcp47: 'zh-CN', label: 'Mandarin', flag: '🇨🇳' },
  es:   { bcp47: 'es-ES', label: 'Spanish',  flag: '🇪🇸' }
};
```

### 3. SpeechSynthesis TTS (Indonesian)
```javascript
function speak(text) {
  if (!window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'id-ID'; u.rate = 1.0; u.pitch = 1.0;
  u.onstart = () => state.isSpeaking = true;
  u.onend = u.onerror = () => state.isSpeaking = false;
  window.speechSynthesis.speak(u);
}
```

### 4. PHP Router (Static + API + SPA Fallback)
```php
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$base = __DIR__;

if (strpos($uri, '/api/') === 0) {
    $file = $base . '/api' . substr($uri, 4) . '.php';
    if (file_exists($file)) { require $file; exit; }
    http_response_code(404); echo json_encode(['error'=>'Not found']); exit;
}

$static = $base . '/public' . $uri;
if (file_exists($static) && is_file($static)) {
    // MIME map → header + readfile + exit
}

header('Content-Type: text/html; charset=UTF-8');
readfile($base . '/public/index.html');
```

### 5. Translation API Contract & Abstraction Pattern (with Auto-Fallback)
```php
// api/services/TranslatorInterface.php
interface TranslatorInterface {
    public function translate(string $text, string $sourceLang = 'auto', string $targetLang = 'id'): string;
    public function getName(): string;
}

// api/translate.php — Provider switcher with auto-fallback
define('ACTIVE_PROVIDER', getenv('TRANSLATOR_PROVIDER') ?: 'hermes');

function getTranslator(string $provider): TranslatorInterface {
    return match ($provider) {
        'hermes'      => new HermesTranslator(),
        'placeholder' => new PlaceholderTranslator(),
        default       => new MyMemoryTranslator(),
    };
}

// Auto-fallback execution:
try {
    $translator = getTranslator(ACTIVE_PROVIDER);
    $translation = $translator->translate($text, $sourceLang, $targetLang);
    $usedProvider = $translator->getName();
} catch (Throwable $e) {
    if (ACTIVE_PROVIDER !== 'mymemory') {
        $translator = getTranslator('mymemory');
        $translation = $translator->translate($text, $sourceLang, $targetLang);
        $usedProvider = $translator->getName() . ' (fallback dari ' . ACTIVE_PROVIDER . ')';
    } else { throw $e; }
}
```

```json
// POST /api/translate
{ "text": "Hello", "source_language": "en", "target_language": "id" }

// Response
{ "translation": "Halo", "original": "Hello", "source_language": "en", "target_language": "id", "provider": "hermes" }
```

### 8. PWA Icon Generator via Python Pillow (No ImageMagick required)
```python
from PIL import Image, ImageDraw

def make_icon(size, filename):
    img = Image.new('RGBA', (size, size), color=(15, 23, 42, 255)) # #0f172a
    draw = ImageDraw.Draw(img)
    # Circle container & rounded mic shapes
    margin = int(size * 0.08)
    draw.ellipse([(margin, margin), (size - margin, size - margin)], fill=(26, 86, 219, 255))
    img.save(filename, 'PNG')

make_icon(192, 'public/icons/icon-192.png')
make_icon(512, 'public/icons/icon-512.png')
make_icon(512, 'public/icons/maskable-icon-512.png')
```

### 6. Cloudflare Tunnel for HTTPS Dev
```bash
php -S 0.0.0.0:8021 router.php &      # Background PHP server
cloudflared tunnel --url http://127.0.0.1:8021
# → https://random-name.trycloudflare.com (secure context ✅)
```

### 7. Mobile-First Dark Theme CSS Variables
```css
:root {
  --bg: #0f172a; --surface: #1e293b; --surface2: #293548;
  --primary: #1a56db; --accent: #f59e0b; --danger: #ef4444; --success: #10b981;
  --text: #f1f5f9; --text-muted: #94a3b8; --border: #334155; --radius: 14px;
}
@media (min-width: 480px) { .lang-grid { grid-template-columns: repeat(6, 1fr); } }
```

### 9. Frontend Responsiveness & Request Controls (Debounce + AbortController)
Use this pattern when speech recognition produces finalized snippets faster than the translation provider can answer. It prevents stale translations, request pileups, and Cloudflare Tunnel `Incoming request ended abruptly: context canceled` noise.

```javascript
const state = {
  activeController: null,
  translateDebounce: null,
  isTranslating: false,
};

function onSentenceComplete(text) {
  if (!text || !text.trim()) return;
  if (state.translateDebounce) clearTimeout(state.translateDebounce);
  if (state.activeController) {
    state.activeController.abort();
    state.activeController = null;
  }
  state.translateDebounce = setTimeout(() => executeTranslation(text.trim()), 350);
}

async function executeTranslation(text) {
  state.isTranslating = true;
  const controller = new AbortController();
  state.activeController = controller;
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const translation = await translateText(text, state.selectedLang, 'id', controller.signal);
    clearTimeout(timeoutId);
    state.activeController = null;
    state.isTranslating = false;
    renderTranslation(translation);
  } catch (err) {
    clearTimeout(timeoutId);
    state.activeController = null;
    state.isTranslating = false;
    if (err.name === 'AbortError') return; // request replaced or timed out
    renderTranslation('[Gagal menerjemahkan: ' + (err.message || 'Koneksi lambat') + ']');
  }
}

async function translateText(text, sourceLang, targetLang, signal) {
  const res = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({ text, source_language: sourceLang, target_language: targetLang })
  });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return (await res.json()).translation;
}
```

## Testing Checklist (Tahap 1)
- [ ] `php -l` syntax clean on router.php + api/*.php
- [ ] `curl -I /css/app.css /js/app.js` → 200 OK + correct MIME
- [ ] `curl -X POST /api/translate` → 200 JSON with placeholder
- [ ] Cloudflare tunnel → HTTPS URL loads in browser
- [ ] Browser console: `secureContext=true`, `SpeechRecognition` exists, `speechSynthesis` exists, `serviceWorker` exists
- [ ] Visual QA: dark theme, mobile layout, 6 language buttons, start/stop/speak buttons, history list

## Pitfalls & Fixes
| Issue | Fix |
|-------|-----|
| CSS/JS 404 on PHP built-in server | Router `return false` only works if `-t public` is passed. When running from project root with `router.php`, must explicitly `readfile($base . '/public' . $uri)` with MIME header — do NOT rely on `return false` |
| Internal reasoning leaks into user reply | Never stream thinking/self-talk as plain text — if planning is needed, do it silently in tool calls, not in prose |
| MyMemory translates common phrases incorrectly | MyMemory can return corpus matches that are semantically wrong (e.g. `I love you` → unrelated sentence). Keep deterministic short phrase dictionary for common conversational phrases; validate against source length/meaning before accepting. |
| Free provider returns wrong long match | Short speech phrases trigger corpus matches 10× longer than expected. Add output-length guard: if input ≤6 words and output >18 words → reject/fallback. Also keep a deterministic phrase map for ≤4-word greetings |
| LLM provider too slow for real-time use | Measure latency before making LLM default. Custom endpoints through Tailscale/proxy can take 15–18s. Use free fast provider (MyMemory ~1s) as default; keep LLM as optional quality upgrade |
| LLM returns translation in wrong language | Enforce in system prompt: "Output ONLY the Indonesian translation. NEVER output English or original language." Set `temperature: 0.0` |
| LLM endpoint returns SSE even with stream:false | Some custom endpoints always stream. Parse `data:` lines manually; do not rely on single JSON body |
| Request stacking / slow spinner | Use debounce (350ms) + AbortController + 8s client timeout (see Pattern 9) |
| SpeechRecognition not continuous | `recognition.continuous = true` + restart in `onend` if still listening |
| Mic permission denied | Ensure HTTPS (Cloudflare tunnel), user gesture on button click |
| Interim text flicker | Separate `state.interimText` from `state.finalText`; render combined |
| TTS queue overlap | Check `speechSynthesis.speaking`; `cancel()` before new utterance |
| localStorage quota exceeded | Cap history at 20 items; wrap in try/catch |

## Next Phases (Template)
- **Tahap 2**: Implement real translation provider in `api/translate.php` (Google, LibreTranslate, custom)
- **Tahap 3**: Add Hermes provider abstraction → `services/Translator.php` with interface
- **Tahap 4**: Generate manifest.json, sw.js, icons (72-512px); test `beforeinstallprompt`
- **Tahap 5**: Deploy to VPS with Caddy + systemd + Cloudflare Tunnel (named tunnel)

## References
- `references/web-speech-api.md` — Browser support matrix, BCP-47 codes, event flow
- `references/cloudflare-tunnel.md` — Quick tunnel vs named tunnel, systemd service
- `references/pwa-checklist.md` — manifest, sw, icons, Lighthouse audit steps
- `references/mymemory-translator.md` — no-key MyMemory API provider notes for Tahap 2 prototyping
- `references/hermes-translator.md` — Hermes/OpenAI-compatible LLM translator provider with env config + auto-fallback pattern