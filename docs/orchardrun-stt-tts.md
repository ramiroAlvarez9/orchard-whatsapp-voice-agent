# Orchard Run — STT & TTS Reference

> Extracted from the full Orchard API docs. Only the endpoints relevant to this project.

## Base URL

```
https://api.orchardrun.com
```

## Authentication

All endpoints require `Authorization: Bearer ork_...` header.

Get your API key at https://orchardrun.com/keys

---

## Speech-to-Text (Transcribe)

### `POST /v1/audio/transcriptions`

Synchronous transcription. Blocks until the cluster returns a transcript.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | binary | yes | Audio: mp3, m4a, wav, mp4, ogg, flac, webm. Max 500 MB |
| `language` | string | no | ISO 639-1 hint (es, en, pt, fr, ...). Auto-detected if omitted |
| `response_format` | string | no | `json` (default), `verbose_json`, `text` |

**Response (json):**
```json
{
  "text": "transcribed text here",
  "language": "es",
  "duration_seconds": 12.5
}
```

**Example:**
```bash
curl -X POST https://api.orchardrun.com/v1/audio/transcriptions \
  -H "Authorization: Bearer ork_..." \
  -F file=@audio.ogg \
  -F language=es
```

---

## Text-to-Speech (Synthesize)

### `POST /v1/tts/generate`

Synchronous TTS. Returns raw WAV audio bytes.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string | yes | Max 500 chars. Split longer text client-side |
| `voice_id` | string | yes | e.g. `es_MX-claude`, `en_US-amy` |
| `voice_type` | string | no | Always `"generic"` for the public voice library |

**Response:** `200 OK`, `Content-Type: audio/wav` — 22.05 kHz / 16-bit mono WAV.

**Example:**
```bash
curl -X POST https://api.orchardrun.com/v1/tts/generate \
  -H "Authorization: Bearer ork_..." \
  -F text="Hola, ¿qué tal?" \
  -F voice_id="es_MX-claude" \
  -F voice_type="generic" \
  --output out.wav
```

---

## Common Voice IDs

| Voice ID | Language | Accent | Gender |
|---|---|---|---|
| `es_MX-claude` | Spanish | LATAM | Male |
| `es_MX-ald` | Spanish | LATAM | Male |
| `es_ES-davefx` | Spanish | Spain | Male |
| `es_ES-sharvard` | Spanish | Spain | Multi |
| `en_US-amy` | English | US | Female |
| `en_US-ryan` | English | US | Male |
| `pt_BR-faber` | Portuguese | Brazil | Male |
| `fr_FR-siwis` | French | France | Female |

Full catalog: `GET /v1/tts/voices/generic` (no auth required)

---

## Error Codes

| Code | Meaning |
|---|---|
| 401 | Missing/invalid API key |
| 402 | Balance exhausted — top up |
| 404 | Voice ID or job not found |
| 413 | Upload exceeds 500 MB |
| 429 | Rate limited |
| 504 | Sync transcription timeout (600s) |

All error responses: `{"detail": "..."}`
