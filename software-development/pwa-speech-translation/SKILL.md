---
name: pwa-speech-translation
description: Build and debug browser microphone speech-translation PWAs with Web Speech API, SpeechSynthesis, HTTPS deployment, provider abstraction, and LLM/free translation fallbacks.
---

# PWA Speech Translation

Use this skill when building or debugging a PWA that captures speech from the browser microphone, shows live/interim transcription, translates finalized utterances via a backend, speaks the translated result, and runs installably over HTTPS.

## Core Workflow

1. **Start with HTTPS requirement**
   - Browser microphone APIs require a secure context.
   - Local development can use `localhost`, but real device testing should use HTTPS via Cloudflare Tunnel or a real domain.

2. **Implement speech recognition first**
   - Use `window.SpeechRecognition || window.webkitSpeechRecognition`.
   - Set `continuous = true`, `interimResults = true`, `maxAlternatives = 1`.
   - Show interim results separately from final transcript.
   - Only call translation API after `event.results[i].isFinal`.

3. **Use backend provider abstraction**
   - Define a `TranslatorInterface` / equivalent contract.
   - Implement at least:
     - primary LLM provider, e.g. Hermes/custom OpenAI-compatible endpoint
     - free fallback provider, e.g. MyMemory
     - placeholder provider for development
   - Keep provider switch env-driven, not hardcoded.

4. **Keep secrets out of code**
   - Use `.env` for `HERMES_LLM_URL`, `HERMES_LLM_KEY`, `HERMES_LLM_MODEL`.
   - Do not print full API keys in logs or final response.

5. **Add PWA installability**
   - `manifest.json` with `display: standalone`, `start_url`, theme/background colors, 192/512/maskable icons.
   - `sw.js`: cache-first for static assets; network-first/no-cache for `/api/translate`.
   - Register service worker after page load.

6. **Verify each stage before continuing**
   - Static assets return HTTP 200.
   - API returns valid JSON.
   - Browser detects `secureContext`, `SpeechRecognition`, `speechSynthesis`, `serviceWorker`.
   - Real device test confirms mic permission appears.

## Provider Patterns

### Hermes / OpenAI-Compatible Streaming Endpoint
Some Hermes/custom LLM endpoints return Server-Sent Events (SSE), even when the API looks OpenAI-compatible. Do not assume a single JSON response.

Parse streaming chunks:

```php
$content = '';
foreach (explode("\n", $raw) as $line) {
    $line = trim($line);
    if (!str_starts_with($line, 'data: ')) continue;
    $jsonStr = substr($line, 6);
    if ($jsonStr === '[DONE]') break;
    $chunk = json_decode($jsonStr, true);
    $delta = $chunk['choices'][0]['delta']['content'] ?? '';
    if ($delta !== '') $content .= $delta;
}
return trim($content);
```

Use a strict translation prompt:

```text
You are a real-time speech translator. Translate the given text to natural Bahasa Indonesia. Output ONLY the Indonesian translation. No explanations, no notes, no original text.
```

### Free Translation Provider Guardrail
Free translation APIs such as MyMemory can return irrelevant long database matches for short speech snippets. Add output-length guards before showing results.

```php
$inputWords = max(1, str_word_count($input));
$outputWords = str_word_count($output);
if ($inputWords <= 6 && $outputWords > 18) {
    throw new RuntimeException('Provider returned irrelevant long match');
}
if ($inputWords <= 12 && $outputWords > ($inputWords * 5 + 12)) {
    throw new RuntimeException('Provider output disproportionate');
}
```

For common very-short English phrases, a deterministic phrase map can prevent bad free-provider matches:

```php
[
  'good morning everyone' => 'Selamat pagi semuanya.',
  'good morning' => 'Selamat pagi.',
  'hello everyone' => 'Halo semuanya.',
  'thank you' => 'Terima kasih.',
]
```

## Cloudflare Tunnel Notes

Quick tunnel for testing:

```bash
cloudflared tunnel --url http://127.0.0.1:8021
```

This gives a temporary `https://*.trycloudflare.com` URL. It is enough for microphone/PWA testing.

Custom domains require a Cloudflare Named Tunnel:
1. Domain must be managed by Cloudflare nameservers.
2. Create Zero Trust Tunnel.
3. Add Public Hostname → service `http://localhost:<port>`.
4. Run tunnel using the token/credentials.

## Testing Checklist

```bash
php -l api/translate.php
php -l api/services/*.php
node --check public/js/app.js
node --check public/sw.js
python3 -m json.tool public/manifest.json >/dev/null
curl -sI http://localhost:8021/manifest.json
curl -sI http://localhost:8021/sw.js
curl -s -X POST http://localhost:8021/api/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"good morning everyone","source_language":"en","target_language":"id"}'
```

Browser checks:

```javascript
({
  secureContext: window.isSecureContext,
  speechRecognition: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
  speechSynthesis: !!window.speechSynthesis,
  serviceWorker: 'serviceWorker' in navigator
})
```

## Pitfalls

- **Mic does not work**: page is not HTTPS or browser lacks Web Speech API support.
- **Translation too long for one short sentence**: free provider returned irrelevant corpus match; enforce output-length guard or switch to LLM provider.
- **Hermes provider returns empty translation**: endpoint may be SSE streaming; parse `data:` chunks instead of reading `choices[0].message.content` from one JSON object.
- **PWA not installable**: missing manifest icon sizes, missing service worker, or not served over HTTPS.
- **Custom domain not immediately usable with quick tunnel**: `trycloudflare.com` quick tunnel does not support custom domain; use Named Tunnel.