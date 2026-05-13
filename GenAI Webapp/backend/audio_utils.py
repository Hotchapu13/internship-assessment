from io import BytesIO
import wave

from fastapi import UploadFile
from mutagen import File as MutagenFile

from errors import BadRequestError, UnsupportedMediaError


MAX_AUDIO_SECONDS = 5 * 60
SUPPORTED_CONTENT_TYPES = {
    "audio/aac",
    "audio/mp4",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/wav",
    "audio/wave",
    "audio/x-m4a",
    "audio/x-wav",
}
SUPPORTED_EXTENSIONS = {".aac", ".m4a", ".mp3", ".ogg", ".wav"}


def is_supported_audio(filename: str | None, content_type: str | None) -> bool:
    suffix = ""
    if filename and "." in filename:
        suffix = filename[filename.rfind(".") :].lower()

    return (content_type in SUPPORTED_CONTENT_TYPES) or (suffix in SUPPORTED_EXTENSIONS)


def get_audio_duration_seconds(audio_bytes: bytes, filename: str | None = None) -> float:
    suffix = ""
    if filename and "." in filename:
        suffix = filename[filename.rfind(".") :].lower()

    if suffix == ".wav":
        try:
            with wave.open(BytesIO(audio_bytes), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                if rate:
                    return frames / float(rate)
        except wave.Error:
            pass

    audio = MutagenFile(BytesIO(audio_bytes))
    if audio is None or audio.info is None or not getattr(audio.info, "length", None):
        raise BadRequestError("We could not read the audio duration.")

    return float(audio.info.length)


async def read_and_validate_audio(upload: UploadFile) -> bytes:
    if not is_supported_audio(upload.filename, upload.content_type):
        raise UnsupportedMediaError(
            "Unsupported audio format.",
            "Please upload an mp3, wav, ogg, m4a, or aac file.",
        )

    audio_bytes = await upload.read()
    if not audio_bytes:
        raise BadRequestError("Upload an audio file before sending.")

    duration = get_audio_duration_seconds(audio_bytes, upload.filename)
    if duration > MAX_AUDIO_SECONDS:
        raise BadRequestError("Audio files must be 5 minutes or shorter.")

    return audio_bytes
