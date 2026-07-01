# WhatsApp Voice Agent

A production-ready FastAPI server that processes WhatsApp voice messages through a
configurable **STT → LLM → TTS** pipeline and replies with synthesized speech.

```
User sends voice note (WhatsApp)
    ↓
Meta POSTs webhook to /webhook
    ↓              ↓
Download audio     HMAC signature verification (optional)
    ↓
STT  →  text      (Orchard Run / OpenAI / Deepgram)
    ↓
LLM  →  text      (OpenAI / Anthropic / Groq)
    ↓
TTS  →  audio     (Orchard Run / OpenAI / ElevenLabs)
    ↓
Upload audio → Send message (Meta API)
    ↓
User hears the response (WhatsApp)
```

## Quickstart

```bash
cp .env.example .env
# Fill in your API keys (see table below)
docker compose up --build
```

Point your Meta WhatsApp webhook to `https://your-domain.com/webhook`.

## Providers

Every layer is pluggable via environment variables. No SDKs — raw `httpx` throughout.

| Layer | Providers | Env var | Default |
|-------|-----------|---------|---------|
| STT   | `orchardrun`, `openai`, `deepgram` | `STT_PROVIDER` | `orchardrun` |
| LLM   | `openai`, `anthropic`, `groq` | `LLM_PROVIDER` | `openai` |
| TTS   | `orchardrun`, `openai`, `elevenlabs` | `TTS_PROVIDER` | `orchardrun` |

Defaults: **Orchard Run** for STT & TTS (shared API key), **OpenAI** for LLM.

### Adding a provider

1. Create `app/providers/<type>/<name>.py` with a class extending the base provider
2. Implement the single required method (`transcribe`, `complete`, or `synthesize`)
3. Set `<TYPE>_PROVIDER=<name>` in `.env` — the dynamic loader discovers it automatically

## Environment variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `META_ACCESS_TOKEN` | Yes | — | From Meta Developer Console |
| `META_PHONE_NUMBER_ID` | Yes | — | From Meta Developer Console |
| `META_VERIFY_TOKEN` | Yes | — | Arbitrary string you choose |
| `META_APP_SECRET` | No | — | Enables HMAC-SHA256 webhook verification |
| `META_API_VERSION` | No | `v24.0` | Meta Graph API version |
| `STT_PROVIDER` | No | `orchardrun` | `orchardrun` / `openai` / `deepgram` |
| `STT_LANGUAGE` | No | `es` | Language code for STT |
| `LLM_PROVIDER` | No | `openai` | `openai` / `anthropic` / `groq` |
| `LLM_API_KEY` | Yes | — | API key for the configured LLM provider |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model name |
| `LLM_BASE_URL` | No | provider default | Override base URL (e.g. proxies, compatible APIs) |
| `TTS_PROVIDER` | No | `orchardrun` | `orchardrun` / `openai` / `elevenlabs` |
| `TTS_VOICE_ID` | No | `es_MX-claude` | Voice identifier |
| `ORCHARD_API_KEY` | Yes* | — | Required if STT or TTS is `orchardrun` |
| `ORCHARD_BASE_URL` | No | `https://api.orchardrun.com` | Override base URL |
| `SYSTEM_PROMPT` | No | Generic assistant prompt | System prompt for the LLM |

## Running with Docker

```bash
docker compose up --build
```

- `Dockerfile` is based on `python:3.11-slim` with **ffmpeg** installed (WAV → Opus OGG conversion)
- `docker-compose.yml` includes a `restart: unless-stopped` policy
- Optionally add an `ngrok` service to expose the webhook publicly:

```yaml
# docker-compose.override.yml
services:
  ngrok:
    image: ngrok/ngrok:latest
    command: http agent:8000
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    ports:
      - "4040:4040"
    depends_on:
      - agent
```

Then visit `http://localhost:4040` to get the public URL.

## Local development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Lint & type-check

```bash
ruff check app/
ruff check --fix app/     # auto-fix
mypy app/
python3 -m pyright app/
python3 -m basedpyright app/
```

All four tools pass with **zero warnings** — strictest settings across the board.

## Project structure

```
/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml              # ruff, mypy, pyright, basedpyright config
├── requirements.txt            # fastapi, uvicorn, httpx, typing-extensions
├── .env.example
├── README.md
│
└── app/
    ├── main.py                 # FastAPI app, /webhook GET (verify) + POST (receive)
    ├── pipeline.py             # STT → LLM → TTS orchestrator + conversation history
    ├── retry.py                # Exponential backoff retry wrapper for all HTTP calls
    │
    ├── providers/
    │   ├── stt/
    │   │   ├── base.py         # BaseSTTProvider — transcribe(bytes) → str
    │   │   ├── orchardrun.py   # Default STT
    │   │   ├── openai.py
    │   │   └── deepgram.py
    │   ├── llm/
    │   │   ├── base.py         # BaseLLMProvider — complete(list[dict]) → str
    │   │   ├── openai.py       # Default LLM
    │   │   ├── anthropic.py
    │   │   └── groq.py
    │   └── tts/
    │       ├── base.py         # BaseTTSProvider — synthesize(str) → bytes
    │       ├── orchardrun.py   # Default TTS (outputs WAV, auto-converted to Opus OGG)
    │       ├── openai.py
    │       └── elevenlabs.py
    │
    └── whatsapp/
        ├── __init__.py         # META_API_VERSION, META_BASE_URL
        ├── receiver.py         # Webhook parse, signature verification, audio download
        └── sender.py           # Audio upload, message send
```

## How it works — per request

1. **`GET /webhook`** — Meta verifies the webhook with `hub.mode=subscribe&hub.challenge=X`
2. **`POST /webhook`** — Meta sends a JSON payload; the agent parses `media_id` and `sender_phone`
3. **Download** — Fetches the audio file from Meta's Media API (2 HTTP calls)
4. **STT** — Transcribes the OGG audio to text via the configured provider
5. **LLM** — Sends the conversation history (system prompt + all user/assistant turns) to the LLM
6. **TTS** — Synthesizes the LLM response into audio (WAV from Orchard Run, MP3 from OpenAI)
7. **Conversion** — Detects WAV header (`b"RIFF"`) and converts to Opus OGG via ffmpeg subprocess
8. **Upload** — Posts the OGG audio to Meta's Media API
9. **Send** — Delivers the audio message to the user via Meta's Messages API

All 9 HTTP calls use automatic retry with exponential backoff (1s → 2s → 4s).

## Conversation history

- Per phone number, in-memory only
- Capped at 20 messages
- **Lost on restart** — a persistent store (Redis, Postgres) is a future enhancement

## Known limitations

- No persistent conversation storage — history resets on restart
- No WhatsApp message queueing or rate limiting
- No unit tests

## License

MIT
