# MyMemory Translator Provider — Implementation Notes

This provider uses the free public MyMemory API (api.mymemory.translated.net).
No API key required. Good for prototyping / Tahap 2 validation.

## Endpoint
```
GET https://api.mymemory.translated.net/get?q={text}&langpair={src}|{tgt}
```

## Request example
```
https://api.mymemory.translated.net/get?q=Hello+world&langpair=en|id
```

## Response (success)
```json
{
  "responseData": { "translatedText": "Halo dunia", "match": 0.99 },
  "responseStatus": 200
}
```

## Response (error)
```json
{
  "responseStatus": 400,
  "responseDetails": "Invalid langpair"
}
```

## Language code mapping
| Frontend code | MyMemory code |
|---------------|---------------|
| auto          | en            |
| en            | en            |
| ja            | ja            |
| ko            | ko            |
| zh            | zh-CN         |
| es            | es            |
| id            | id            |

## Implementation quirks
- `file_get_contents` with `stream_context_create` timeout 10s.
- Decode HTML entities in response (`html_entity_decode`).
- Empty translation → throw `RuntimeException`.
- Non-200 status → throw `RuntimeException` with `responseDetails`.
- Throttling: not documented; don't spam.

## File
`api/services/MyMemoryTranslator.php`