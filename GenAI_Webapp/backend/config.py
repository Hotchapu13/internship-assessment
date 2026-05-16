from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    sunbird_api_key: str
    sunbird_base_url: str
    frontend_origin: str
    public_backend_url: str
    default_stt_language: str
    tts_temperature: float
    tts_max_new_audio_tokens: int
    generated_audio_dir: Path

    def __init__(self) -> None:
        self.sunbird_api_key = os.getenv("SUNBIRD_API_KEY", "")
        self.sunbird_base_url = os.getenv("SUNBIRD_BASE_URL", "https://api.sunbird.ai").rstrip("/")
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "https://internship-assessment-5ds5dkat9-hotchapu13s-projects.vercel.app/")
        self.public_backend_url = os.getenv("PUBLIC_BACKEND_URL", "https://internship-assessment-qjw6.onrender.com").rstrip("/")
        self.default_stt_language = os.getenv("SUNBIRD_STT_LANGUAGE", "lug")
        self.tts_temperature = float(os.getenv("SUNBIRD_TTS_TEMPERATURE", "0.7"))
        self.tts_max_new_audio_tokens = int(os.getenv("SUNBIRD_TTS_MAX_NEW_AUDIO_TOKENS", "2000"))
        self.generated_audio_dir = Path(__file__).resolve().parent / "generated_audio"

    def require_sunbird_key(self) -> None:
        if not self.sunbird_api_key:
            raise RuntimeError("SUNBIRD_API_KEY is not configured.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
