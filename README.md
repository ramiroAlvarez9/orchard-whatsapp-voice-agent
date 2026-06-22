# WhatsApp Voice Agent

Receive WhatsApp audio messages, process them through a configurable AI pipeline (STT → LLM → TTS), and respond with a synthesized voice — all with one Docker command.

## Quickstart

```bash
cp .env.example .env
# Fill in your API keys
docker compose up --build
```

## How it works

```
User sends audio (WhatsApp)
    ↓
Meta POSTs to /webhook
    ↓
Server downloads audio via Meta API
    ↓
STT → text (default: Orchard Run)
    ↓
LLM → response text (default: OpenAI)
    ↓
TTS → audio file (default: Orchard Run)
    ↓
Server sends audio back via Meta API
    ↓
User receives voice response (WhatsApp)
```

## Environment variables

See `.env.example` for all options. The defaults use Orchard Run for STT + TTS and OpenAI for the LLM.

### Provider options

| Layer | Options |
|---|---|
| STT | `orchardrun`, `openai`, `deepgram` |
| LLM | `openai`, `anthropic`, `groq` |
| TTS | `orchardrun`, `openai`, `elevenlabs` |

Set `STT_PROVIDER`, `LLM_PROVIDER`, and `TTS_PROVIDER` to switch providers.

### Shared Orchard Run key

When using `orchardrun` for both STT and TTS (the default), you only need one API key:

```env
ORCHARD_API_KEY=ork_your_key
```

Get one at [orchardrun.com/keys](https://orchardrun.com/keys).

## Local testing with ngrok

1. Start the server: `docker compose up --build`
2. Start ngrok: `ngrok http 8000`
3. Copy the ngrok HTTPS URL (e.g. `https://abc123.ngrok.io`)
4. In Meta Developer Console, set the webhook URL to `https://abc123.ngrok.io/webhook`
5. Set the verify token to whatever you put in `META_VERIFY_TOKEN`
6. Send a WhatsApp audio message to your test number

## Project structure

```
/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── README.md
│
├── /app
│   ├── main.py               # FastAPI app, /webhook endpoint
│   ├── pipeline.py           # STT → LLM → TTS orchestrator
│   │
│   ├── /providers
│   │   ├── /stt               # Speech-to-Text providers
│   │   ├── /llm               # LLM providers
│   │   └── /tts               # Text-to-Speech providers
│   │
│   └── /whatsapp
│       ├── receiver.py        # Parses webhook, downloads audio
│       └── sender.py          # Uploads audio, sends message
│
└── /docs
    ├── orchardrun-stt-tts.md  # Orchard Run STT & TTS reference
    └── orchardrun-api-doc.md  # Full Orchard Run API docs
```
