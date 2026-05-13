from pydantic import BaseModel, Field


SUPPORTED_LANGUAGES = {"ach", "teo", "eng", "lug", "lgg", "nyn"}


class ProcessResult(BaseModel):
    summary: str
    translated_summary: str = Field(alias="translatedSummary")
    audio_url: str = Field(alias="audioUrl")
    transcript: str | None = None

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
