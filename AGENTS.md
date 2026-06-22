# AGENTS.md

## Project

WhatsApp voice agent: a FastAPI server that receives WhatsApp audio messages via Meta webhooks, runs them through a STT → LLM → TTS pipeline, and sends back a synthesized voice response.

## Commands

```bash
# Lint & type-check (run before committing)
ruff check app/
mypy app/
python3 -m pyright app/
python3 -m basedpyright app/

# Auto-fix lint issues
ruff check --fix app/

# Run locally
uvicorn app.main:app --reload --port 8000

# Run with Docker
docker compose up --build

# Run tests (none yet — add with: pytest)
```

## Architecture

```
User audio (WhatsApp)
    ↓ POST /webhook
main.py (_process_audio background task)
    ↓ download_audio
receiver.py (download_audio)
    ↓ bytes
pipeline.py (run_pipeline)
    ↓ stt.transcribe()  → text
    ↓ llm.complete()    → text
    ↓ tts.synthesize()  → bytes
sender.py (upload_audio → send_audio_message)
    ↓
User receives audio (WhatsApp)
```

### Key files

| File | Role |
|---|---|
| `app/main.py` | FastAPI app, `/webhook` GET (verify) + POST (receive), provider factories |
| `app/pipeline.py` | STT→LLM→TTS orchestrator, in-memory conversation history per phone |
| `app/providers/stt/base.py` | `BaseSTTProvider` — `transcribe(bytes) → str` |
| `app/providers/llm/base.py` | `BaseLLMProvider` — `complete(list[dict]) → str` |
| `app/providers/tts/base.py` | `BaseTTSProvider` — `synthesize(str) → bytes` |
| `app/whatsapp/receiver.py` | Parse Meta webhook JSON, download audio via Media API |
| `app/whatsapp/sender.py` | Upload audio to Meta, send WhatsApp message |

### Providers

| Layer | Options | Default |
|---|---|---|
| STT | `orchardrun`, `openai`, `deepgram` | `orchardrun` |
| LLM | `openai`, `anthropic`, `groq` | `openai` |
| TTS | `orchardrun`, `openai`, `elevenlabs` | `orchardrun` |

Switched via `STT_PROVIDER`, `LLM_PROVIDER`, `TTS_PROVIDER` env vars. All providers use raw `httpx` directly — no SDKs.

## Conventions

### Type system (STRICT — zero tolerance)

- **No `Any` types ever.** Use `dict[str, object]` for JSON and `typing.cast()` for nested access:

```python
# Wrong
data: dict = response.json()
text = data["choices"][0]["message"]["content"]

# Right
data = cast("dict[str, object]", response.json())
choices = cast("list[object]", data["choices"])
choice = cast("dict[str, object]", choices[0])
message = cast("dict[str, object]", choice["message"])
text = str(message["content"])
```

- **Class attributes must have type annotations at class level** (required by `reportUnannotatedClassAttribute`):

```python
class MyProvider(BaseProvider):
    api_key: str          # ← here, not just in __init__
    model: str

    def __init__(self) -> None:
        self.api_key = ...
```

- **All overridden methods must use `@override`** (from `typing_extensions`, required by `reportImplicitOverride`):

```python
from typing_extensions import override

class MyProvider(BaseProvider):
    @override
    async def transcribe(self, audio_bytes: bytes) -> str:
        ...
```

- **Discard unused call results explicitly** with `_ = ` (required by `reportUnusedCallResult`):

```python
_ = response.raise_for_status()
```

### Imports

- Lazy imports inside provider factory functions (in `main.py`) are intentional — avoids requiring all provider SDKs at import time. The `PLC0415` ruff rule is suppressed globally for this reason.
- Import order follows ruff's I001 (stdlib → third-party → first-party).
- `typing_extensions` goes in the third-party block (NOT stdlib, it's a pip package).

### Code style

- All text in English (docstrings, comments, logs).
- Docstrings are NOT required (D rules suppressed in ruff) — only add when explicitly requested or when it improves clarity.
- Logging via `logging.getLogger(__name__)` at module level.

## Environment variables

| Variable | Required | Default |
|---|---|---|
| `META_ACCESS_TOKEN` | Yes | — |
| `META_PHONE_NUMBER_ID` | Yes | — |
| `META_VERIFY_TOKEN` | Yes | — |
| `META_APP_SECRET` | No | — (enables signature verification when set) |
| `ORCHARD_API_KEY` | Yes (default STT+TTS) | — |
| `LLM_API_KEY` | Yes (default LLM) | — |
| `STT_PROVIDER` | No | `orchardrun` |
| `LLM_PROVIDER` | No | `openai` |
| `TTS_PROVIDER` | No | `orchardrun` |
| `SYSTEM_PROMPT` | No | Generic voice assistant prompt |
| `STT_LANGUAGE` | No | `es` |

## Config files

- `pyproject.toml` — ruff (ALL rules, ignoring D + PLC0415), mypy (strict + disallow_any_explicit), pyright/basedpyright (typeCheckingMode = all)
- `requirements.txt` — fastapi, uvicorn, httpx, typing-extensions
- `Dockerfile` — python:3.11-slim, uvicorn on :8000
- `docker-compose.yml` — single service, .env file, restart unless-stopped

## Known gaps

- In-memory conversation history — lost on restart
