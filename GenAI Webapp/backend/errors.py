class AppError(Exception):
    status_code = 400
    message = "Request failed."

    def __init__(self, message: str | None = None, detail: str | None = None) -> None:
        self.message = message or self.message
        self.detail = detail
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400


class UnsupportedMediaError(AppError):
    status_code = 415
    message = "Unsupported audio format."


class SunbirdAPIError(AppError):
    status_code = 502
    message = "Sunbird API failed."


class SunbirdTimeoutError(SunbirdAPIError):
    status_code = 504
    message = "Sunbird API timed out."
