"use client";

import { ChangeEvent, DragEvent, FormEvent, useRef, useState } from "react";
import { FileAudio, Pause, Play, Send } from "lucide-react";
import { targetLanguages } from "@/lib/languages";

type InputMode = "text" | "audio";

type ProcessResult = {
  transcript?: string;
  summary: string;
  translatedSummary: string;
  audioUrl: string;
};

const MAX_AUDIO_SECONDS = 5 * 60;

export default function Home() {
  const [inputMode, setInputMode] = useState<InputMode>("text");
  const [targetLanguage, setTargetLanguage] = useState(targetLanguages[0].value);
  const [text, setText] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const selectedLanguage =
    targetLanguages.find((language) => language.value === targetLanguage)?.label ??
    "selected language";

  async function getAudioDuration(file: File) {
    return new Promise<number>((resolve, reject) => {
      const audio = document.createElement("audio");
      const objectUrl = URL.createObjectURL(file);

      audio.preload = "metadata";
      audio.onloadedmetadata = () => {
        URL.revokeObjectURL(objectUrl);
        resolve(audio.duration);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error("We could not read the audio duration."));
      };
      audio.src = objectUrl;
    });
  }

  async function acceptAudioFile(file: File) {
    setError(null);

    if (!file.type.startsWith("audio/")) {
      setError("Please upload an audio file.");
      return;
    }

    try {
      const duration = await getAudioDuration(file);
      if (duration > MAX_AUDIO_SECONDS) {
        setAudioFile(null);
        setError("Audio files must be 5 minutes or shorter.");
        return;
      }

      setInputMode("audio");
      setAudioFile(file);
    } catch (durationError) {
      setAudioFile(null);
      setError(
        durationError instanceof Error
          ? durationError.message
          : "We could not read the audio duration."
      );
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      await acceptAudioFile(file);
    }
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];
    if (file) {
      await acceptAudioFile(file);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);

    if (inputMode === "text" && !text.trim()) {
      setError("Enter text before sending.");
      return;
    }

    if (inputMode === "audio" && !audioFile) {
      setError("Upload an audio file before sending.");
      return;
    }

    const formData = new FormData();
    formData.append("mode", inputMode);
    formData.append("target_language", targetLanguage);

    if (inputMode === "text") {
      formData.append("text", text.trim());
    }

    if (inputMode === "audio" && audioFile) {
      formData.append("audio", audioFile);
    }

    try {
      setIsProcessing(true);
      const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
      const response = await fetch(`${baseUrl}/api/process`, {
        method: "POST",
        body: formData
      });

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          payload?.detail ?? payload?.error ?? "The backend could not process this request."
        );
      }

      setResult({
        transcript: payload.transcript,
        summary: payload.summary,
        translatedSummary: payload.translated_summary ?? payload.translatedSummary,
        audioUrl: payload.audio_url ?? payload.audioUrl
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong while processing your request."
      );
    } finally {
      setIsProcessing(false);
    }
  }

  function resetFlow() {
    setResult(null);
    setError(null);
    setIsPlaying(false);
  }

  async function toggleAudio() {
    if (!audioRef.current) {
      return;
    }

    if (audioRef.current.paused) {
      await audioRef.current.play();
      setIsPlaying(true);
    } else {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }

  return (
    <main className="page-shell">
      <div className="language-control">
        <select
          aria-label="Target language"
          value={targetLanguage}
          onChange={(event) => setTargetLanguage(event.target.value)}
        >
          {targetLanguages.map((language) => (
            <option key={language.value} value={language.value}>
              {language.label}
            </option>
          ))}
        </select>
      </div>

      {!result ? (
        <section className="input-state" aria-label="Input composer">
          <form className="composer-wrap" onSubmit={handleSubmit}>
            <div
              className={`composer ${isDragging ? "is-dragging" : ""}`}
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              {inputMode === "text" ? (
                <textarea
                  aria-label="Text to summarise and translate"
                  placeholder="Enter text or drop an audio file here..."
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  rows={1}
                />
              ) : (
                <label className="dropzone">
                  <FileAudio size={22} aria-hidden="true" />
                  <span className={audioFile ? "file-name" : "dropzone-text"}>
                    {audioFile
                      ? audioFile.name
                      : "Drop audio here or click to upload. Maximum length is 5 minutes."}
                  </span>
                  <input accept="audio/*" type="file" onChange={handleFileChange} />
                </label>
              )}

              <button className="send-button" type="submit" disabled={isProcessing}>
                <Send size={22} aria-hidden="true" />
                <span className="sr-only">Send</span>
              </button>
            </div>

            <div className="mode-switcher" aria-label="Input mode">
              <button
                aria-pressed={inputMode === "text"}
                type="button"
                onClick={() => {
                  setInputMode("text");
                  setError(null);
                }}
              >
                Text
              </button>
              <button
                aria-pressed={inputMode === "audio"}
                type="button"
                onClick={() => {
                  setInputMode("audio");
                  setError(null);
                }}
              >
                Audio
              </button>
            </div>

            <p className="status-text">
              {isProcessing ? `Processing your input for ${selectedLanguage}...` : ""}
            </p>

            {error ? <div className="error-banner">{error}</div> : null}
          </form>
        </section>
      ) : (
        <section className="results-state" aria-label="Generated results">
          <div className="results-header">
            <h1>Results</h1>
            <button className="secondary-button" type="button" onClick={resetFlow}>
              Try another input
            </button>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="result-grid">
            {result.transcript ? (
              <article className="result-card">
                <h2>Transcript</h2>
                <p>{result.transcript}</p>
              </article>
            ) : null}

            <article className="result-card">
              <h2>Summary</h2>
              <p>{result.summary}</p>
            </article>

            <article className="result-card">
              <h2>Translated Summary</h2>
              <p>{result.translatedSummary}</p>
            </article>

            <article className="result-card">
              <h2>Audio</h2>
              <div className="audio-ui">
                <button className="play-button" type="button" onClick={toggleAudio}>
                  {isPlaying ? (
                    <Pause size={20} aria-hidden="true" />
                  ) : (
                    <Play size={20} aria-hidden="true" />
                  )}
                  <span className="sr-only">{isPlaying ? "Pause" : "Play"}</span>
                </button>
                <audio
                  ref={audioRef}
                  controls
                  src={result.audioUrl}
                  onPause={() => setIsPlaying(false)}
                  onPlay={() => setIsPlaying(true)}
                  onEnded={() => setIsPlaying(false)}
                />
              </div>
            </article>
          </div>
        </section>
      )}
    </main>
  );
}
