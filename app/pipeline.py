"""Orchestrate the STT → LLM → TTS pipeline with in-memory conversation history."""

import logging
import shutil
import subprocess

from app.providers.llm.base import BaseLLMProvider
from app.providers.stt.base import BaseSTTProvider
from app.providers.tts.base import BaseTTSProvider

logger = logging.getLogger(__name__)

conversation_history: dict[str, list[dict[str, str]]] = {}

MAX_HISTORY_MESSAGES = 20

FFMPEG_TIMEOUT_SECONDS = 30

_FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"


def get_history(phone: str) -> list[dict[str, str]]:
    """Return the conversation history for a given phone number."""
    if phone not in conversation_history:
        conversation_history[phone] = []
    return conversation_history[phone]


def add_to_history(phone: str, role: str, content: str) -> None:
    """Append a message to the conversation history, trimming old entries."""
    history = get_history(phone)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY_MESSAGES:
        conversation_history[phone] = history[-MAX_HISTORY_MESSAGES:]


def convert_to_ogg(audio_bytes: bytes) -> bytes:
    if audio_bytes[:4] != b"RIFF":
        return audio_bytes
    result = subprocess.run(  # noqa: S603
        [
            _FFMPEG_PATH,
            "-i", "pipe:0",
            "-c:a", "libopus",
            "-f", "ogg",
            "pipe:1",
            "-loglevel", "error",
        ],
        input=audio_bytes,
        capture_output=True,
        timeout=FFMPEG_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        logger.error("ffmpeg conversion failed: %s", result.stderr.decode())
        return audio_bytes
    logger.info(
        "Converted WAV to OGG, %d → %d bytes",
        len(audio_bytes), len(result.stdout),
    )
    return result.stdout


async def run_pipeline(
    audio_bytes: bytes,
    sender_phone: str,
    stt: BaseSTTProvider,
    llm: BaseLLMProvider,
    tts: BaseTTSProvider,
) -> bytes:
    """Transcribe audio, generate a response with the LLM, and synthesize speech."""
    text = await stt.transcribe(audio_bytes)
    logger.info("STT result: %s", text[:200])

    history = get_history(sender_phone)
    add_to_history(sender_phone, "user", text)

    response_text = await llm.complete(history)
    logger.info("LLM response: %s", response_text[:200])

    add_to_history(sender_phone, "assistant", response_text)

    audio_response = await tts.synthesize(response_text)
    logger.info("TTS generated %d bytes", len(audio_response))

    return convert_to_ogg(audio_response)
