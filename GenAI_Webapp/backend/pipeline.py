from fastapi import UploadFile

from audio_utils import read_and_validate_audio
from config import Settings
from errors import AppError, BadRequestError
from schemas import ProcessResult, StageError, SUPPORTED_LANGUAGES
from sunbird_client import SunbirdClient


def validate_target_language(target_language: str) -> None:
    if target_language not in SUPPORTED_LANGUAGES:
        raise BadRequestError(
            "Unsupported target language.",
            f"Choose one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}.",
        )


def public_audio_url(settings: Settings, filename: str) -> str:
    return f"{settings.public_backend_url}/audio/{filename}"


def stage_error(stage: str, exc: Exception, fallback: str) -> StageError:
    if isinstance(exc, AppError):
        return StageError(stage=stage, message=exc.message, detail=exc.detail)
    return StageError(stage=stage, message=fallback, detail=str(exc))


async def process_text(text: str, target_language: str, settings: Settings) -> ProcessResult:
    validate_target_language(target_language)

    cleaned_text = text.strip()
    if not cleaned_text:
        raise BadRequestError("Enter text before sending.")

    client = SunbirdClient(settings)
    errors: list[StageError] = []

    try:
        summary = await client.summarise(cleaned_text)
    except Exception as exc:
        errors.append(stage_error("summary", exc, "Summarisation failed."))
        return ProcessResult(stageErrors=errors)

    source_language = await client.detect_language(summary) or "eng"

    try:
        translated_summary = await client.translate(summary, source_language, target_language)
    except Exception as exc:
        errors.append(stage_error("translation", exc, "Translation failed."))
        return ProcessResult(summary=summary, stageErrors=errors)

    try:
        audio_path = await client.text_to_speech(
            translated_summary,
            target_language,
            settings.generated_audio_dir,
        )
    except Exception as exc:
        errors.append(stage_error("audio", exc, "Audio generation failed."))
        return ProcessResult(
            summary=summary,
            translatedSummary=translated_summary,
            stageErrors=errors,
        )

    return ProcessResult(
        summary=summary,
        translatedSummary=translated_summary,
        audioUrl=public_audio_url(settings, audio_path.name),
        stageErrors=errors,
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
    errors: list[StageError] = []

    try:
        transcript = await client.transcribe(
            audio_bytes,
            filename=audio.filename or "audio-upload",
            content_type=audio.content_type or "application/octet-stream",
            language=stt_language,
        )
    except Exception as exc:
        errors.append(stage_error("transcript", exc, "Speech-to-text failed."))
        return ProcessResult(stageErrors=errors)

    try:
        summary = await client.summarise(transcript)
    except Exception as exc:
        errors.append(stage_error("summary", exc, "Summarisation failed."))
        return ProcessResult(transcript=transcript, stageErrors=errors)

    source_language = await client.detect_language(summary) or "eng"

    try:
        translated_summary = await client.translate(summary, source_language, target_language)
    except Exception as exc:
        errors.append(stage_error("translation", exc, "Translation failed."))
        return ProcessResult(
            transcript=transcript,
            summary=summary,
            stageErrors=errors,
        )

    try:
        audio_path = await client.text_to_speech(
            translated_summary,
            target_language,
            settings.generated_audio_dir,
        )
    except Exception as exc:
        errors.append(stage_error("audio", exc, "Audio generation failed."))
        return ProcessResult(
            transcript=transcript,
            summary=summary,
            translatedSummary=translated_summary,
            stageErrors=errors,
        )

    return ProcessResult(
        transcript=transcript,
        summary=summary,
        translatedSummary=translated_summary,
        audioUrl=public_audio_url(settings, audio_path.name),
        stageErrors=errors,
    )
