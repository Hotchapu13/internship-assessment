from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from errors import AppError, BadRequestError
from pipeline import process_audio, process_text
from schemas import ErrorResponse, ProcessResult


settings = get_settings()
settings.generated_audio_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="GenAI Local Summary API",
    description="FastAPI backend for text/audio summarisation, translation, and TTS through Sunbird APIs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=settings.generated_audio_dir), name="audio")


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.message, detail=exc.detail).model_dump(exclude_none=True),
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Backend configuration error.", detail=str(exc)).model_dump(),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/process",
    response_model=ProcessResult,
    responses={
        400: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def process_input(
    mode: str = Form(...),
    target_language: str = Form(...),
    text: str | None = Form(None),
    audio: UploadFile | None = File(None),
) -> ProcessResult:
    if mode == "text":
        return await process_text(text or "", target_language, settings)

    if mode == "audio":
        if audio is None:
            raise BadRequestError("Upload an audio file before sending.")
        return await process_audio(audio, target_language, settings)

    raise BadRequestError("Choose either text input or audio upload.")
