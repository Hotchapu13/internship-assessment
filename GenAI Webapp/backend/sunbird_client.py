from pathlib import Path
from uuid import uuid4

import httpx

from config import Settings
from errors import SunbirdAPIError, SunbirdTimeoutError


SPEAKER_IDS = {
    "acholi": 241,
    "teo": 242,
    "nyn": 243,
    "lgg": 245,
    "lug": 248,
    # "swh": 246,
}


class SunbirdClient:
    def __init__(self, settings: Settings) -> None:
        settings.require_sunbird_key()
        self.settings = settings
        self.headers = {"Authorization": f"Bearer {settings.sunbird_api_key}"}

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
        language: str,
    ) -> str:
        data = {
            "language": language,
            "adapter": language,
            "recognise_speakers": "false",
            "whisper": "false",
        }
        files = {
            "audio": (
                filename or "audio-upload",
                audio_bytes,
                content_type or "application/octet-stream",
            )
        }
        payload = await self._post_multipart("/tasks/modal/stt", data=data, files=files)
        transcript = payload.get("audio_transcription") or payload.get("formatted_diarization_output")
        if not transcript:
            raise SunbirdAPIError("Speech-to-text failed.", "Sunbird returned no transcript.")
        return transcript

    async def summarise(self, text: str) -> str:
        payload = await self._post_json("/tasks/summarise", {"text": text})
        summary = payload.get("summarized_text")
        print(f"Summary: {summary}")
        if not summary:
            raise SunbirdAPIError("Summarisation failed.", "Sunbird returned no summary.")
        return summary

    async def detect_language(self, text: str) -> str | None:
        try:
            payload = await self._post_json("/tasks/language_id", {"text": text})
        except SunbirdAPIError:
            return None

        language = payload.get("language")
        if isinstance(language, str) and language != "language not detected":
            print(f"Language detected: {language}")
            return language
        return None

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text

        print("[Starting form request]")
        payload = await self._post_form(
            "/tasks/sunflower_simple",
            {"instruction": f"Translate the following text from {source_language} to {target_language}: {text}"}
        )
        print("[Acquired response]")

        output = payload.get("response") or {}
        if output.get("Error"):
            raise SunbirdAPIError("Translation failed.", str(output["Error"]))

        translated = output.get("translated_text")
        if not translated:
            raise SunbirdAPIError("Translation failed.", "Sunbird returned no translated text.")
        return translated

    async def text_to_speech(self, text: str, target_language: str, output_dir: Path) -> Path:
        speaker_id = SPEAKER_IDS.get(target_language)
        if speaker_id is None:
            raise SunbirdAPIError("Text-to-speech failed.", f"No TTS speaker for {target_language}.")

        payload = await self._post_json(
            "/tasks/tts",
            {
                "text": text,
                "speaker_id": speaker_id,
            },
        )
        output = payload.get("output") or {}
        audio_url = output.get("audio_url")
        audio_format = output.get("format") or "mp3"
        if not audio_url:
            raise SunbirdAPIError("Text-to-speech failed.", "Sunbird returned no audio URL.")

        return await self._download_audio(audio_url, audio_format, output_dir)

    async def _post_json(self, path: str, payload: dict) -> dict:
        return await self._post(path, json=payload)

    async def _post_form(self, path: str, data: dict) -> dict:
        return await self._post(path, data=data)

    async def _post_multipart(self, path: str, data: dict, files: dict) -> dict:
        return await self._post(path, data=data, files=files)

    async def _post(
        self,
        path: str,
        json: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
    ) -> dict:
        try:
            print(f"DEBUG: Attempting POST to {self.settings.sunbird_base_url}{path}")
            async with httpx.AsyncClient(timeout=300) as client:
                kwargs = {"follow_redirects": True}
                
                # Set appropriate headers and request parameters
                if json is not None:
                    kwargs["headers"] = {**self.headers, "Content-Type": "application/json"}
                    kwargs["json"] = json
                elif files is not None:
                    # For multipart, let httpx set the Content-Type automatically
                    kwargs["headers"] = self.headers
                    kwargs["data"] = data
                    kwargs["files"] = files
                else:
                    # For form-urlencoded
                    kwargs["headers"] = {**self.headers, "Content-Type": "application/x-www-form-urlencoded"}
                    kwargs["data"] = data

                response = await client.post(
                    f"{self.settings.sunbird_base_url}{path}",
                    **kwargs
                )
        except httpx.TimeoutException as exc:
            raise SunbirdTimeoutError(detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise SunbirdAPIError(detail=str(exc)) from exc

        return self._parse_response(response)

    async def _download_audio(self, audio_url: str, audio_format: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = audio_format if audio_format.startswith(".") else f".{audio_format}"
        output_path = output_dir / f"{uuid4().hex}{suffix}"

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                response = await client.get(audio_url)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise SunbirdTimeoutError("Audio download timed out.", str(exc)) from exc
        except httpx.HTTPError as exc:
            raise SunbirdAPIError("Audio download failed.", str(exc)) from exc

        output_path.write_bytes(response.content)
        return output_path

    def _parse_response(self, response: httpx.Response) -> dict:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if response.status_code >= 400:
            detail = payload.get("detail") if isinstance(payload, dict) else None
            if response.status_code in {408, 503, 504}:
                raise SunbirdTimeoutError(detail=detail or response.text)
            raise SunbirdAPIError(detail=detail or response.text)

        if not isinstance(payload, dict):
            raise SunbirdAPIError(detail="Sunbird returned an unexpected response.")

        return payload
