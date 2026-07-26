"""API transport translation for application-layer errors."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode


def error_to_http_status(error: ApplicationError) -> int:
    if error.code == ApplicationErrorCode.VALIDATION_FAILED:
        return 400
    if error.code == ApplicationErrorCode.AUTHORIZATION_DENIED:
        return 403
    if error.code == ApplicationErrorCode.PRECONDITION_FAILED:
        return 412
    if error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND:
        return 404
    if error.code == ApplicationErrorCode.CONFLICT:
        return 409
    if error.code == ApplicationErrorCode.DEPENDENCY_UNAVAILABLE:
        return 503
    if error.code == ApplicationErrorCode.TRANSIENT_FAILURE:
        return 503
    return 500


def application_error_payload(error: ApplicationError) -> dict[str, object]:
    return {
        "code": error.code.value,
        "message": error.message,
        "details": error.details,
    }


def to_http_exception(error: ApplicationError) -> HTTPException:
    return HTTPException(status_code=error_to_http_status(error), detail=application_error_payload(error))


async def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=error_to_http_status(error),
        content=application_error_payload(error),
    )
