Get started

*   [Quickstart](#quickstart)
*   [TypeScript SDK](#sdk)
*   [Authentication](#auth)

Transcribe

*   [Sync API](#sync-api)
*   [Async jobs](#async)
*   [Webhooks & n8n](#webhooks)
*   [Editor integrations](#editors)

Synthesize

*   [TTS endpoint](#synthesize)
*   [Voice catalog](#voices)
*   [Clone Voice](#clone-voice)

Reference

*   [Response formats](#formats)
*   [Performance](#performance)
*   [Error codes](#errors)
*   [Limits & pricing](#limits)

Reference · v1

Orchard API
===========

Voice infrastructure on a private inference cluster. Three products, one balance, one API. **Transcribe** audio to text in **60+ languages** (sync / async / webhooks), **Synthesize** text to audio across 17 languages, and **Clone Voice** from a 6-60 s reference. All three endpoints debit the same per-second balance, so your plan covers everything without separate quotas. Every request lives under `/v1`.

Base URL · https://api.orchardrun.comJSON over HTTPSBearer authUnified balance

Quickstart
----------

Three steps to your first request — same flow whether you start with Transcribe or Synthesize. One API key, one balance.

1.  Sign up at [/signup](/signup).
2.  Activate a plan at [/billing](/billing) — Free includes 500 min/month (covers both products), paid plans start at $1.
3.  Generate an API key at [/keys](/keys). The raw key (`ork_…`) is shown _once_ — copy it.

Then, transcribe an MP3 — or jump to [Synthesize](#synthesize) for text-to-speech:

curlpythonnode

    curl -X POST https://api.orchardrun.com/v1/audio/transcriptions \
      -H "Authorization: Bearer ork_..." \
      -F file=@audio.mp3 \
      -F language=es \
      -F response_format=verbose_json

TypeScript SDK
--------------

Skip the raw HTTP plumbing. The official `@orchardrun/sdk` package wraps every endpoint with typed methods, automatic retries on 5xx, and typed errors you can `instanceof` instead of string-matching. Universal — Node 18+, Bun, Deno, browsers, Cloudflare Workers, Vercel Edge.

### Install

pnpmnpmbun

    pnpm add @orchardrun/sdk

### Quickstart

Set `ORCHARD_API_KEY` in your env (or pass `apiKey` directly to the constructor) and you're three lines from a transcript.

ESMCJS

    import Orchard from "@orchardrun/sdk";
    import fs from "node:fs";
    
    const orchard = new Orchard({ apiKey: process.env.ORCHARD_API_KEY });
    
    // Speech to text
    const { text } = await orchard.transcribe({
      file: fs.readFileSync("./call.wav"),
      language: "es",
    });
    console.log(text);
    
    // Text to speech
    const audio = await orchard.tts.generate({
      text: "Hola mundo",
      voice: "es_MX-claude",
    });
    await fs.promises.writeFile(
      "./out.wav",
      Buffer.from(await audio.arrayBuffer()),
    );
    
    // Voice cloning: register once, synth many times
    const voice = await orchard.voices.create({
      name: "Mateo · founder",
      file: fs.readFileSync("./sample.wav"),
      language: "es",
    });
    const synth = await orchard.voices.synthesize(voice.id, {
      text: "Hola, soy Mateo.",
    });

### Vercel AI SDK provider

Orchard ships a first-class provider for the [Vercel AI SDK](https://sdk.vercel.ai/). If you already use `transcribe()` or `generateSpeech()` from `ai`, switching to Orchard is a one-line provider swap.

transcribegenerateSpeechcreateOrchard

    import { experimental_transcribe as transcribe } from "ai";
    import { orchard } from "@orchardrun/sdk/ai-sdk";
    import fs from "node:fs";
    
    const { text, language, durationInSeconds } = await transcribe({
      model: orchard.transcription(),
      audio: fs.readFileSync("./call.wav"),
      mediaType: "audio/wav",
      providerOptions: { orchard: { language: "es" } },
    });

### Typed errors

Every non-2xx maps to an `OrchardError` subclass. Catch the specific one for retry / upgrade-CTA logic — no string matching on `error.message` needed.

TypeScript

    import {
      OrchardRateLimitError,
      OrchardQuotaError,
      OrchardAuthError,
    } from "@orchardrun/sdk";
    
    try {
      await orchard.tts.generate({ text, voice });
    } catch (e) {
      if (e instanceof OrchardRateLimitError) {
        await sleep((e.retryAfterSeconds ?? 5) * 1000);
        return retry();
      }
      if (e instanceof OrchardQuotaError) {
        // 402 — out of balance. Surface upgrade CTA to your user.
        return showUpgradeBanner();
      }
      if (e instanceof OrchardAuthError) {
        // 401/403 — rotate the API key.
        return null;
      }
      throw e;
    }

### Cancellation

Every method accepts an `AbortSignal` via the optional second argument. Useful when you're wiring up a "cancel transcription" button on a long upload.

TypeScript

    const ac = new AbortController();
    setTimeout(() => ac.abort(), 5_000); // 5-second hard cap
    
    await orchard.transcribe(
      { file: bigAudioBuffer, language: "es" },
      { signal: ac.signal },
    );

Full API surface, changelog and contributing guide on [npm](https://www.npmjs.com/package/@orchardrun/sdk) and [GitHub](https://github.com/Mateobustamante1/orchardrun/tree/main/sdk/typescript).

Authentication
--------------

Every endpoint except `POST /v1/auth/*` and `/v1/billing/webhook` requires authentication. Two interchangeable methods:

*   **API key** (recommended for programmatic access): `Authorization: Bearer ork_...` or `X-API-Key: ork_...`.
*   **JWT** (used by the web dashboard, obtainable via `POST /v1/auth/login`): `Authorization: Bearer eyJhbGciOi...`.

Keys are SHA-256 hashed at rest and revocable instantly from [/keys](/keys). The raw token is shown _only on creation_ — there is no recovery flow.

Sync API
--------

`POST /v1/audio/transcriptions` accepts a standard multipart upload and blocks until the cluster returns a transcript. **60+ languages supported** with automatic detection. Request and response shape follows the public transcription-API conventions, so any SDK that speaks that format plugs in by pointing its base URL at Orchard.

curlpython

    curl -X POST https://api.orchardrun.com/v1/audio/transcriptions \
      -H "Authorization: Bearer ork_..." \
      -F file=@audio.mp3 \
      -F language=es \
      -F response_format=verbose_json

### Multipart fields

file

binary, required

Audio file. mp3, m4a, wav, mp4, ogg, flac, webm. Max 500 MB.

model

string

Accepted for client-library compatibility and ignored — every request runs on our latest STT engine, kept up to date by us.

language

string

ISO 639-1 hint, 60+ supported (es, en, pt, fr, de, it, hi, zh, ja, ar, ru, pl, nl, tr, ko, and more). Auto-detected when omitted.

response\_format

string

json (default) · verbose\_json · text

prompt

string

Accepted for parity; ignored.

temperature

number

Accepted for parity; ignored (decoder is greedy).

**Blocking:** the request waits for the cluster to finish (timeout 600s). For long audio prefer the async endpoints below.

Async jobs
----------

For long audio (or YouTube URLs) submit a job, get back a `job_id`, and poll until `status` is`success`. Concurrency is capped per plan (see [Limits](#limits)); excess requests queue rather than fail.

### POST /v1/transcriptions · YouTube URL

curlpython

    curl -X POST https://api.orchardrun.com/v1/transcriptions \
      -H "Authorization: Bearer ork_..." \
      -H "Content-Type: application/json" \
      -d '{"url":"https://youtu.be/dQw4w9WgXcQ","language":"en"}'
    
    # → 202 Accepted
    # {"job_id": "abc123...", "status": "queued"}

### POST /v1/transcriptions/upload · file

curl

    curl -X POST https://api.orchardrun.com/v1/transcriptions/upload \
      -H "Authorization: Bearer ork_..." \
      -F file=@interview.mp3 \
      -F language=es
    
    # → 202 Accepted
    # {"job_id": "...", "status": "queued"}

### GET /v1/transcriptions/{id} · poll

Returns the job's status plus a live `progress` snapshot while running, and the full `result` payload once succeeded.

curlpython

    curl https://api.orchardrun.com/v1/transcriptions/abc123 \
      -H "Authorization: Bearer ork_..."
    
    # {"job_id":"abc123","status":"running",
    #  "progress":{"current_ms":699000,"total_ms":1099000,"percent":63}}
    
    # Once done:
    # {"job_id":"abc123","status":"success",
    #  "result":{"text":"...","language":"es","duration_seconds":1099, ...}}

### GET /v1/transcriptions/{id}/download · formatted

Same job, rendered in the format you ask for. Returns the file with a `Content-Disposition: attachment` header.

curl

    # Plain text
    curl "https://api.orchardrun.com/v1/transcriptions/abc123/download?format=text" \
      -H "Authorization: Bearer ork_..." -O
    
    # SRT subtitles
    curl "https://api.orchardrun.com/v1/transcriptions/abc123/download?format=srt" \
      -H "Authorization: Bearer ork_..." -O
    
    # Markdown with YAML frontmatter
    curl "https://api.orchardrun.com/v1/transcriptions/abc123/download?format=md" \
      -H "Authorization: Bearer ork_..." -O

Webhooks & n8n
--------------

Pass `webhook_url` when you create a job and Orchard **POSTs the result** to that URL when the job finishes. No polling needed — perfect for n8n / Zapier / Make.

### Sending a job with a webhook

curlpython

    curl -X POST https://api.orchardrun.com/v1/transcriptions \
      -H "Authorization: Bearer ork_..." \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://youtu.be/dQw4w9WgXcQ",
        "language": "en",
        "webhook_url": "https://your.n8n.instance/webhook/orchard-result"
      }'

### Payload Orchard POSTs to your URL

Same shape as `GET /v1/transcriptions/{id}`:

json

    {
      "job_id": "abc123...",
      "status": "success",         // or "failed"
      "result": {
        "text": "...",
        "language": "en",
        "duration_seconds": 1099,
        "segments": [ ... ],
        "provider": "local",
        "model": "orchard-stt-v1",
        "elapsed_ms": 17430,
        "post_processed": true
      },
      "error": null               // string when status="failed"
    }

### Headers we send

User-Agent

Orchard-Webhook/1.0

Identify Orchard in your logs.

X-Orchard-Job-Id

abc123...

Same id you got back from the POST.

X-Orchard-Attempt

1, 2 or 3

Retry counter — handle idempotently using job\_id.

Content-Type

application/json

### Retry & idempotency

*   3 attempts total with exponential backoff: `1s · 5s · 25s`.
*   `2xx` = success. We stop retrying.
*   `4xx` = permanent failure. We do _not_ retry — fix your endpoint.
*   `5xx` or network errors = retried up to 3 attempts.
*   Use `X-Orchard-Job-Id` to dedupe — same id may arrive more than once.

### Ready-made n8n workflows

Importable JSON — open n8n → _Workflows_ → _Import from File_. Replace the placeholder API key and destination IDs before running.

*   [orchard-youtube-to-notion.json](/n8n/orchard-youtube-to-notion.json) — Webhook trigger → POST YouTube URL → wait for result → save to a Notion DB.
*   [orchard-upload-to-airtable.json](/n8n/orchard-upload-to-airtable.json) — Webhook trigger receiving an audio file → POST to /upload → wait → save row in Airtable.

Both templates use n8n's `Wait` node in webhook mode. The `{{$execution.resumeUrl}}` expression resolves to a unique URL per run, so each transcription resumes the right execution.

Editor integrations
-------------------

**Orchard Dictate** for VS Code / Cursor — hit a hotkey, speak, get the transcript inserted at your cursor. Built for dictating prompts to AI coding agents (Cursor, Copilot, Claude) without breaking flow.

### Requirements

*   `sox` installed (provides the `rec` binary the extension uses to capture mic audio).
    *   macOS: `brew install sox`
    *   Debian / Ubuntu: `sudo apt-get install sox`
*   An Orchard API key (create one at [/keys](/keys)).
*   Microphone permission for VS Code / Cursor in your OS privacy settings.

### Install

1.  Install from the [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=Orchardrun.orchard-dictate) — click _Install_, or in VS Code / Cursor open the Extensions sidebar and search `Orchard Dictate`. From the command line:
    
    bash
    
        code --install-extension Orchardrun.orchard-dictate
    
2.  Run the command `Orchard: Set API Key` (or click the `⚙️` next to the `🎤 Dictate` status bar item) and paste your `ork_…` key. That's it — the extension ships pointed at `https://api.orchardrun.com`.

### Usage

*   `Cmd+Shift+8` (macOS) / `Ctrl+Shift+8` (Win/Linux) — start recording.
*   Same shortcut again — stop, transcribe, insert at cursor.

### Settings

orchardDictate.apiUrl

string

Orchard backend URL. Default https://api.orchardrun.com — override only if you're self-hosting.

orchardDictate.language

auto | es | en | pt | fr | de | it | hi

Language hint passed to the model.

orchardDictate.insertMode

cursor | clipboard

Paste at cursor (default) or copy to clipboard for manual paste.

orchardDictate.notifyOnSuccess

boolean

Show a toast on every success. Off by default — the inserted text is feedback enough.

### Troubleshooting

*   **Nothing happens on the hotkey:** sox is probably not installed. The extension probes `/opt/homebrew/bin/rec`, `/usr/local/bin/rec`, and `/usr/bin/rec` before falling back to `PATH`, so install location shouldn't matter as long as one of those exists.
*   **Recording runs but transcript is empty:** mic permission missing for your editor in OS settings.

Synthesize · Text-to-Speech
---------------------------

`POST /v1/tts/generate` takes text + a voice id and returns a WAV. Synchronous — request blocks for ~1-2s on common short texts (the response body IS the audio file). Served by the same private inference cluster that handles transcription.

### Request

curlpythonnode

    curl -X POST https://api.orchardrun.com/v1/tts/generate \
      -H "Authorization: Bearer ork_..." \
      -F text="Hola, ¿qué tal todo por allá?" \
      -F voice_id="es_MX-claude" \
      -F voice_type="generic" \
      --output out.wav

### Form fields

text

string · required · max 500 chars

What you want spoken. Punctuation and capitalisation are respected — they shape prosody. Longer texts: split into ≤500-char chunks and concatenate the WAVs client-side.

voice\_id

string · required

One of the entries from the voice catalog below (e.g. "en\_US-amy", "es\_MX-claude"). The voice's language is implicit in the id.

voice\_type

"generic" · default "clone"

Use "generic" for the public voice library. Voice cloning is not exposed in v2.0 — leave at "generic".

source\_language

ISO 639-1 code · optional

Language hint for the input text when it differs from the voice's language. If set + different from voice language, the text is auto-translated before synthesis. Skip for same-language use.

translate

"auto" · "force" · "off" · default "auto"

Translation policy: auto = translate only when source\_language ≠ voice language; force = always; off = synthesize the literal text in the voice's phoneme set even if mismatched.

### Response

*   `200 OK` with `Content-Type: audio/wav` — body is the raw 22.05 kHz / 16-bit mono WAV. Stream-friendly to disk or to a browser `<audio>` tag.
*   `404` if `voice_id` is unknown.
*   `402` if your balance is exhausted (see Limits & pricing).
*   `429` if you exceed the concurrent-request limit for your plan.

### Billing

Each request debits the user's balance by the **duration of the generated audio**. A 30-second synthesized clip costs 30 seconds from the same balance Transcribe uses. The audio is generated at roughly 1000 characters / minute of speech, so a 500-char input consumes ~30 seconds.

### Cross-language synthesis

If your input text is in one language but you pick a voice in another, Orchard auto-translates before synthesis:

curl

    # Input is Spanish, voice is American English →
    # server translates to English then synthesizes with Amy.
    curl -X POST https://api.orchardrun.com/v1/tts/generate \
      -H "Authorization: Bearer ork_..." \
      -F text="Hola, ¿cómo estás?" \
      -F voice_id="en_US-amy" \
      -F source_language=es \
      -F translate=force \
      --output greeting_en.wav

Auto-translation falls back to the original text if the translation provider is unreachable — same-language synthesis always works.

Voice catalog
-------------

Generic voices available out of the box. Hit `GET /v1/tts/voices/generic` at runtime for the canonical list (it's public — no auth required, useful for populating a voice picker in your UI).

en\_US-amy

🇺🇸 English (US)

Female · friendly, conversational

en\_US-ryan

🇺🇸 English (US)

Male · professional, narration

es\_ES-davefx

🇪🇸 Spanish (Spain)

Male · neutral broadcast tone

es\_ES-sharvard

🇪🇸 Spanish (Spain)

Multi-speaker · documentation reading

es\_MX-claude

🇲🇽 Spanish (Mexico)

Male · conversational LATAM

es\_MX-ald

🇲🇽 Spanish (Mexico)

Male · alternate LATAM voice

pt\_BR-faber

🇧🇷 Portuguese (Brazil)

Male · warm narration

fr\_FR-siwis

🇫🇷 French (France)

Female · neutral conversational

de\_DE-thorsten

🇩🇪 German

Male · clean broadcast

it\_IT-paola

🇮🇹 Italian

Female · narration

hi\_IN-pratham

🇮🇳 Hindi

Male · standard pronunciation

hi\_IN-priyamvada

🇮🇳 Hindi

Female · standard pronunciation

### Picking the right voice for your audience

The country code in the voice id (`es_ES` vs `es_MX`) drives accent. A LATAM audience listening to `es_ES-davefx` will hear a Castilian accent (the _θ_ sound on c/z); for neutral LATAM use the `es_MX` voices.

### Programmatic listing

curlpython

    curl https://api.orchardrun.com/v1/tts/voices/generic | jq

Returns an array of objects with `voice_id`, `language` (ISO 639-1), `locale` (e.g. `es_MX`), `flag`, `gender`, and `description`. Use this in production rather than hard-coding — the catalog grows as new voices ship.

Clone Voice
-----------

Upload a 6-60 s reference recording, give it a name, and Orchard regenerates any text in that speaker's voice. Two-step flow: _create_ persists the voice (one-time embed compute); _synthesize_ generates audio from cached state on every subsequent call.

**Engine routing is server-side.** Spanish references route to our _Premium_ engine (tier-1 speaker fidelity); other languages route to our _Multilingual_engine. You don't pick — we pick the right engine for the language. The tier is shown in the GET response (`"premium-es"` or `"multilingual"`) so you can reason about expected quality and latency.

### POST /v1/voices · create from audio

curlpython

    curl -X POST https://api.orchardrun.com/v1/voices \
      -H "Authorization: Bearer $ORCHARD_KEY" \
      -F "audio=@reference.wav" \
      -F "name=My voice" \
      -F "language=es"

### Form fields

audio

file (required)

Reference audio: 6-60 s, any codec ffmpeg decodes (wav/webm/m4a/mp3). Normalised server-side to 24 kHz mono PCM.

name

string (required)

1-80 chars. Shown in the playground voice list + the rename endpoint can change it later.

language

string (required)

ISO 639-1 of the reference: es / en / pt / fr / de / it / pl / tr / ru / nl / cs / ar / zh-cn / ja / hu / ko / hi. Drives engine routing (es → Premium, else Multilingual).

### Response

Returns `201 Created` + JSON with `id`, `name`, `language`, `tier` (`"premium-es"` or `"multilingual"`), `embed_bytes`, `created_at`.

Returns `402` when you've hit your plan's cloned-voice quota — delete an existing voice (frees a slot) or upgrade. See the per-plan limits in [Limits & pricing](#limits).

### GET /v1/voices · list + quota

curl

    curl https://api.orchardrun.com/v1/voices \
      -H "Authorization: Bearer $ORCHARD_KEY"

Response shape: `{ voices: [...], quota: { used: 2, limit: 3 } }`. The quota block lets you render an "X of Y used" UI without an extra round-trip.

### POST /v1/voices/{id}/synthesize · generate audio

curlpython

    curl -X POST https://api.orchardrun.com/v1/voices/$VOICE_ID/synthesize \
      -H "Authorization: Bearer $ORCHARD_KEY" \
      -F "text=Hola mundo, esta es mi voz clonada." \
      -F "language=es" \
      --output out.wav

### Form fields

text

string (required)

1-500 chars.

language

string (required)

Same set as create. Multilingual voices can synthesize cross-lingually (your English voice speaking Italian); Premium ES voices stay in Spanish.

Returns `audio/wav` bytes (16-bit PCM, 24 kHz mono). Debits from your shared per-second balance. Sampling hyperparameters are tuned server-side and not exposed — they're calibrated per engine for max fidelity.

### PATCH /v1/voices/{id} · rename

curl

    curl -X PATCH https://api.orchardrun.com/v1/voices/$VOICE_ID \
      -H "Authorization: Bearer $ORCHARD_KEY" \
      -F "name=My better name"

Embedding stays intact — only the label changes. Avoids the delete-and-recreate workflow that would force a re-record.

### DELETE /v1/voices/{id}

curl

    curl -X DELETE https://api.orchardrun.com/v1/voices/$VOICE_ID \
      -H "Authorization: Bearer $ORCHARD_KEY"

Returns `204`. Frees a slot in your quota immediately. The embedding bytes are deleted — recreating the same voice requires a fresh reference recording.

### Privacy notes

For Premium ES voices, the source WAV is persisted alongside the transcribed reference text — both are required for every synth on that tier. For Multilingual voices, only a compact conditioning embedding (~130 KB) is stored; the source WAV is discarded after the one-time embed compute. Either way: **DELETE removes all artefacts permanently.**

Response formats
----------------

Five formats supported on the download endpoint. The sync API uses `response_format` and supports `json`, `verbose_json`, and `text`.

text

text/plain

Just the cleaned text. No metadata.

md

text/markdown

Cleaned text + YAML frontmatter (language, duration, node).

srt

application/x-subrip

SubRip subtitles, one cue per segment.

vtt

text/vtt

WebVTT subtitles.

json

application/json

Full payload: text, raw\_text, segments, language, duration\_seconds, elapsed\_ms, post\_processed, node\_id.

verbose\_json

application/json

Standard shape: {task, language, duration, text, segments\[\]}.

Performance tips
----------------

We accept any audio container ffmpeg can decode (mp3, m4a, ogg, opus, flac, wav, mp4, webm). The format you pick changes upload latency, not transcription quality — every request runs on the same model.

### Send Opus instead of WAV

WAV is uncompressed PCM. A 15-minute speech file is ~27 MB as WAV and only ~2 MB as Opus 32kbps. The transcription is identical (Opus at speech bitrates is perceptually lossless for our STT engine); the upload is ~8x faster and you stop bumping into upload limits on long audios.

ffmpegpython

    # Convert before upload
    ffmpeg -i recording.wav -c:a libopus -b:a 32k recording.opus
    # 27 MB → ~2 MB. Then upload normally.

**Already using Opus?** WhatsApp voicenotes (.ogg) and browser `MediaRecorder` defaults are already Opus — pass them through directly.

### Use sync vs async deliberately

*   **Sync** (`POST /v1/audio/transcriptions`) blocks. Best for short clips (≤2 min) where waiting on the response is fine.
*   **Async + webhook** (`POST /v1/transcriptions/upload` with `webhook_url`) frees the caller immediately and pushes the result when ready. Best for n8n / Zapier and audio over a couple of minutes.
*   **Avoid polling** when you can use a webhook — polling every 1-2s adds the same cumulative wait but burns request quota.

### Hint header

Sync responses include `X-Orchard-Hint` when we notice an inefficient upload (e.g. WAV \> 5 MB). Surface it in your client logs the first time it appears and you'll catch slow paths before they show up as user-visible latency.

Error codes
-----------

401 Unauthorized

—

Missing or invalid credentials.

402 Payment Required

—

Account balance is 0 or negative. Top up at /billing.

404 Not Found

—

Job, key, or user not found (also returned for jobs you don't own).

409 Conflict

—

Download requested before the job finished.

413 Payload Too Large

—

Upload exceeds 500 MB.

504 Gateway Timeout

—

Sync transcription exceeded the cluster's timeout (600s).

5xx

—

Server error — typically a worker or DB issue. Safe to retry.

All error responses share the same shape: `{ "detail": "..." }`.

Limits & pricing
----------------

One **unified balance** per plan, metered in seconds of audio. A 30-second transcription consumes 30 seconds; a 30-second synthesized clip consumes 30 seconds; a 30-second voice clone consumes 30 seconds. Mix the three products freely — no per-product cap to juggle.

Plans

Free · $1 · $10 · $25 · Enterprise

Free (500 min/mo, opt-in), Hobby, Starter, Pro, custom Enterprise. See /billing.

Balance unit

1 second of audio

Applies to Transcribe (input audio length), Synthesize (generated audio length), and Clone Voice (generated audio length). 1000 characters of TTS ≈ 60 seconds.

Effective rate

from $0.00042 / min on Pro

Pro tier ($25/mo for 60,000 min). Free tier requires explicit activation in the dashboard.

Cloned voices

1 / 3 / 10 / 50 / ∞

Free / Hobby / Starter / Pro / Enterprise. Each voice held costs ~130-500 KB of DB storage; the limit caps that + creates a natural upgrade moment.

Concurrency

1 / 1 / 3 / 10 / 24

Free / Hobby / Starter / Pro / Enterprise. Counts STT + TTS + Clone Voice in the same bucket. Excess requests queue rather than fail.

Rate limit

30 / 60 / 300 / 900 / 5000 rpm

Free / Hobby / Starter / Pro / Enterprise.

Sync timeout

600 seconds

POST /v1/audio/transcriptions blocks up to this long.

Async timeout

1800 seconds

Per-job wall-clock cap. Practical audio length per file is ~2 hours.

Upload size (STT)

500 MB

Per file.

Supported audio (STT)

mp3, m4a, wav, ogg, flac, mp4, webm

Anything ffmpeg can decode.

Languages (STT)

60+

Whisper-class engine: Spanish, English, Portuguese, French, German, Italian, Hindi, Chinese, Japanese, Arabic, Russian, Polish, Dutch, Turkish, Korean, Catalan, Romanian, Greek, Hebrew, Indonesian, Vietnamese, Thai, and 40+ more. Pass ISO 639-1 code as \`language\` hint or omit for auto-detect.

Languages (TTS)

17

Generic voices: en, es, pt, fr, de, it, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi. See /v1/tts/voices/generic for the canonical catalog.

TTS text length

500 chars per request

Split longer text client-side and concatenate the WAVs.

Clone Voice reference

6-60 seconds

