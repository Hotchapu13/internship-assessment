from pydantic import BaseModel, Field


SUPPORTED_LANGUAGES = {"ach", "teo", "eng", "lug", "lgg", "nyn"}


class StageError(BaseModel):
    stage: str
    message: str
    detail: str | None = None


class ProcessResult(BaseModel):
    summary: str | None = None
    translated_summary: str | None = Field(default=None, alias="translatedSummary")
    audio_url: str | None = Field(default=None, alias="audioUrl")
    transcript: str | None = None
    stage_errors: list[StageError] = Field(default_factory=list, alias="stageErrors")

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
