from fastapi import UploadFile

from audio_utils import read_and_validate_audio
from config import Settings
from errors import BadRequestError
from schemas import ProcessResult, SUPPORTED_LANGUAGES
from sunbird_client import SunbirdClient


def validate_target_language(target_language: str) -> None:
    if target_language not in SUPPORTED_LANGUAGES:
        raise BadRequestError(
            "Unsupported target language.",
            f"Choose one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}.",
        )


def public_audio_url(settings: Settings, filename: str) -> str:
    return f"{settings.public_backend_url}/audio/{filename}"


async def process_text(text: str, target_language: str, settings: Settings) -> ProcessResult:
    validate_target_language(target_language)

    cleaned_text = text.strip()
    if not cleaned_text:
        raise BadRequestError("Enter text before sending.")

    client = SunbirdClient(settings)
    summary = await client.summarise(cleaned_text)
    source_language = await client.detect_language(summary) or "eng"
    translated_summary = await client.translate(summary, source_language, target_language)
    audio_path = await client.text_to_speech(
        translated_summary,
        target_language,
        settings.generated_audio_dir,
    )

    return ProcessResult(
        summary=summary,
        translatedSummary=translated_summary,
        audioUrl=public_audio_url(settings, audio_path.name),
    )


async def process_audio(
    audio: UploadFile,
    target_language: str,
    settings: Settings,
) -> ProcessResult:
    validate_target_language(target_language)

    audio_bytes = await read_and_validate_audio(audio)
    stt_language = settings.default_stt_language

    client = SunbirdClient(settings)
    transcript = await client.transcribe(
        audio_bytes,
        filename=audio.filename or "audio-upload",
        content_type=audio.content_type or "application/octet-stream",
        language=stt_language,
    )
    summary = await client.summarise(transcript)
    source_language = await client.detect_language(summary) or stt_language
    translated_summary = await client.translate(summary, source_language, target_language)
    audio_path = await client.text_to_speech(
        translated_summary,
        target_language,
        settings.generated_audio_dir,
    )

    return ProcessResult(
        transcript=transcript,
        summary=summary,
        translatedSummary=translated_summary,
        audioUrl=public_audio_url(settings, audio_path.name),
    )
