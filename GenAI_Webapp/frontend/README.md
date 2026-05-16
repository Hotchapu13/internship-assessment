# GenAI Local Summary Frontend

Next.js frontend for a small GenAI app that accepts text or audio, sends it to a FastAPI backend, and displays the transcript, summary, translated summary, and generated audio.

## Setup

```bash
npm install
npm run dev
```

Create `.env.local` from `.env.example`:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

The frontend submits requests to:

```text
POST /api/process
```

Expected successful response shape:

```json
{
  "transcript": "Only present for audio input",
  "summary": "Short summary",
  "translated_summary": "Translated summary",
  "audio_url": "https://example.com/generated-audio.wav"
}
```
