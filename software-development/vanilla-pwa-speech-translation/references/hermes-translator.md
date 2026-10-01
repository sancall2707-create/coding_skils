# Hermes LLM Translator Provider

Integration pattern for using Hermes Agent's LLM endpoint (OpenAI-compatible) as a translation backend.

## Configuration (Environment Variables)

```bash
# Required for Hermes provider
HERMES_LLM_URL=https://your-hermes-endpoint/v1/chat/completions
HERMES_LLM_KEY=sk-xxxxxxxxxxxxxxxx
HERMES_LLM_MODEL=ag/gemini-3.6-flash-high   # or any model available on the endpoint
HERMES_LLM_TIMEOUT=20                        # seconds

# Optional: switch active provider
TRANSLATOR_PROVIDER=hermes
```

## PHP Implementation

```php
class HermesTranslator implements TranslatorInterface {
    private string $url;
    private string $apiKey;
    private string $model;
    private int $timeout;

    public function __construct() {
        $this->url     = getenv('HERMES_LLM_URL') ?: '';
        $this->apiKey  = getenv('HERMES_LLM_KEY') ?: '';
        $this->model   = getenv('HERMES_LLM_MODEL') ?: 'ag/gemini-3.6-flash-high';
        $this->timeout = (int)(getenv('HERMES_LLM_TIMEOUT') ?: 20);

        if ($this->url === '' || $this->apiKey === '') {
            throw new RuntimeException('Env HERMES_LLM_URL dan HERMES_LLM_KEY belum diset.');
        }
    }

    public function translate(string $text, string $sourceLang = 'auto', string $targetLang = 'id'): string {
        $text = trim($text);
        if ($text === '') {
            throw new InvalidArgumentException('Teks kosong.');
        }

        $sourceLabel = match (strtolower($sourceLang)) {
            'en'    => 'English',
            'ja'    => 'Japanese',
            'ko'    => 'Korean',
            'zh'    => 'Mandarin/Chinese',
            'es'    => 'Spanish',
            default => 'foreign language',
        };

        $payload = [
            'model' => $this->model,
            'messages' => [
                [
                    'role' => 'system',
                    'content' => 'Translate conversational speech to natural Bahasa Indonesia. Output only the Indonesian translation. No notes. No quotes. No original text.'
                ],
                [
                    'role' => 'user',
                    'content' => 'Source language: ' . $sourceLabel . "\nTarget language: Indonesian\nText: " . $text
                ]
            ],
            'temperature' => 0.2,
            'max_tokens'  => 500,
        ];

        $ch = curl_init($this->url);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $this->apiKey,
            ],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => $this->timeout,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error    = curl_error($ch);
        curl_close($ch);

        if ($response === false || $error) {
            throw new RuntimeException('Hermes API network error: ' . ($error ?: 'unknown'));
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            throw new RuntimeException('Hermes API HTTP error: ' . $httpCode);
        }

        $data = json_decode($response, true);
        $content = trim((string)($data['choices'][0]['message']['content'] ?? ''));

        if ($content === '') {
            throw new RuntimeException('Hermes API response kosong.');
        }

        return trim($content, " \t\n\r\0\x0B\"'");
    }

    public function getName(): string {
        return 'hermes';
    }
}
```

## Auto-Fallback Pattern

The main endpoint (`api/translate.php`) includes auto-fallback:

```php
try {
    $translator = getTranslator(ACTIVE_PROVIDER);  // e.g. 'hermes'
    $translation = $translator->translate(...);
    $usedProvider = $translator->getName();
} catch (Throwable $e) {
    if (ACTIVE_PROVIDER !== 'mymemory') {
        $translator = getTranslator('mymemory');
        $translation = $translator->translate(...);
        $usedProvider = $translator->getName() . ' (fallback dari ' . ACTIVE_PROVIDER . ')';
    } else { throw $e; }
}
```

This ensures the app never shows a translation error to the user — it silently falls back to the free MyMemory provider if Hermes is unavailable or misconfigured.

## Prompt Engineering Notes

- **System prompt**: "Translate conversational speech to natural Bahasa Indonesia. Output only the Indonesian translation. No notes. No quotes. No original text."
- **Temperature**: 0.2 (low for consistent, deterministic translations)
- **Max tokens**: 500 (enough for single sentences)
- **User message format**: Includes source language label for context

## Security

- API key loaded from env, never hardcoded
- Does not modify Hermes Agent's own config (`~/.hermes/config.yaml`)
- HTTPS enforced by Cloudflare Tunnel in dev; production should use named tunnel + TLS