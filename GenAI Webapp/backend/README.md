# GenAI Local Summary Backend

FastAPI backend for the GenAI local-language summary app. It receives text or audio from the Next.js frontend, calls Sunbird APIs, and returns visible intermediate results plus a playable generated audio URL.

## Setup

```bash
cd "GenAI Webapp/backend"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your Sunbird API key to `.env`:

```env
SUNBIRD_API_KEY=your_sunbird_api_key_here
```

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

## Endpoint

```text
POST /api/process
```

The endpoint expects multipart form data:

```text
mode=text|audio
target_language=lug|ach|teo|lgg|nyn
text=...       # text mode only
audio=<file>   # audio mode only
```

Successful response:

```json
{
  "transcript": "Only present for audio input",
  "summary": "Short summary",
  "translatedSummary": "Translated summary",
  "audioUrl": "http://localhost:8000/audio/generated.mp3"
}
```

The frontend accepts both camelCase and snake_case response fields.

## Notes

- Audio is rejected if it is longer than 5 minutes.
- Supported upload types are mp3, wav, ogg, m4a, and aac.
- Sunbird TTS returns a short-lived signed URL, so this backend downloads the audio immediately and serves it from `/audio`.
- The UI currently chooses the target language only. `SUNBIRD_STT_LANGUAGE` controls the STT source language/adapter for uploaded audio.
