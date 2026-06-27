import logging
import os
from typing import Annotated, cast

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request

from app.pipeline import run_pipeline
from app.providers.llm.base import BaseLLMProvider
from app.providers.loader import load_provider
from app.providers.stt.base import BaseSTTProvider
from app.providers.tts.base import BaseTTSProvider
from app.whatsapp.receiver import WebhookPayload, download_audio
from app.whatsapp.sender import send_audio_message, upload_audio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Voice Agent")

VERIFY_TOKEN = os.environ["META_VERIFY_TOKEN"]


stt_provider = cast(
    "BaseSTTProvider",
    load_provider("stt", "STT_PROVIDER", "orchardrun", BaseSTTProvider),
)
llm_provider = cast(
    "BaseLLMProvider",
    load_provider("llm", "LLM_PROVIDER", "openai", BaseLLMProvider),
)
tts_provider = cast(
    "BaseTTSProvider",
    load_provider("tts", "TTS_PROVIDER", "orchardrun", BaseTTSProvider),
)

logger.info(
    "Providers loaded: STT=%s LLM=%s TTS=%s",
    os.environ.get("STT_PROVIDER", "orchardrun"),
    os.environ.get("LLM_PROVIDER", "openai"),
    os.environ.get("TTS_PROVIDER", "orchardrun"),
)


@app.get("/webhook")
async def verify_webhook(
    hub_mode: Annotated[str, Query(alias="hub.mode")],
    hub_challenge: Annotated[str, Query(alias="hub.challenge")],
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")],
) -> int:
    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid hub.mode")
    if hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    return int(hub_challenge)


@app.post("/webhook")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    try:
        body = cast("dict[str, object]", await request.json())
    except Exception as err:
        raise HTTPException(status_code=400, detail="Invalid JSON") from err

    try:
        payload = WebhookPayload(body)
    except ValueError as e:
        logger.info("Skipping non-audio or invalid message: %s", e)
        return {"status": "ignored"}

    logger.info(
        "Audio message from %s (media_id=%s)",
        payload.sender_phone,
        payload.media_id,
    )

    background_tasks.add_task(
        _process_audio,
        media_id=payload.media_id,
        sender_phone=payload.sender_phone,
    )
    return {"status": "accepted"}


async def _process_audio(media_id: str, sender_phone: str) -> None:
    try:
        audio_bytes = await download_audio(media_id)
        logger.info("Downloaded %d bytes of audio", len(audio_bytes))

        response_audio = await run_pipeline(
            audio_bytes=audio_bytes,
            sender_phone=sender_phone,
            stt=stt_provider,
            llm=llm_provider,
            tts=tts_provider,
        )

        media_id_out = await upload_audio(response_audio, mime_type="audio/ogg")
        logger.info("Uploaded response audio (media_id=%s)", media_id_out)

        _ = await send_audio_message(sender_phone, media_id_out)
        logger.info("Sent response to %s", sender_phone)
    except Exception:
        logger.exception("Failed to process audio for %s", sender_phone)
