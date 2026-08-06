"""API transport translation for application-layer errors."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.observability.redaction import sanitize_mapping, sanitize_text


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
    if error.code == ApplicationErrorCode.INVARIANT_VIOLATION:
        return 409
    if error.code == ApplicationErrorCode.STALE_PROJECTION:
        return 503
    if error.code == ApplicationErrorCode.UNCERTAIN_RESULT:
        return 503
    if error.code == ApplicationErrorCode.COMMAND_REJECTED:
        return 422
    if error.code == ApplicationErrorCode.DEPENDENCY_UNAVAILABLE:
        return 503
    if error.code == ApplicationErrorCode.TRANSIENT_FAILURE:
        return 503
    return 500


def application_error_payload(error: ApplicationError) -> dict[str, object]:
    protected_codes = {
        ApplicationErrorCode.DEPENDENCY_UNAVAILABLE,
        ApplicationErrorCode.TRANSIENT_FAILURE,
        ApplicationErrorCode.EXECUTION_FAILED,
        ApplicationErrorCode.INFRASTRUCTURE_FAILURE,
        ApplicationErrorCode.INTERNAL_ERROR,
    }
    return {
        "code": error.code.value,
        "message": "request could not be completed" if error.code in protected_codes else sanitize_text(error.message),
        "details": sanitize_mapping(error.details),
    }


def to_http_exception(error: ApplicationError) -> HTTPException:
    return HTTPException(status_code=error_to_http_status(error), detail=application_error_payload(error))


async def application_error_handler(_: Request, error: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=error_to_http_status(error),
        content=application_error_payload(error),
    )


async def unhandled_application_exception_handler(_: Request, __: Exception) -> JSONResponse:
    """Prevent untrusted exception details from becoming an API response."""

    error = ApplicationError(
        code=ApplicationErrorCode.INFRASTRUCTURE_FAILURE,
        message="request could not be completed",
    )
    return JSONResponse(status_code=500, content=application_error_payload(error))
