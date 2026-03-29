from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:

    formatted_errors = [
        {"field": err.get("loc")[-1], "message": err.get("msg")}
        for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "validation_failure",
            "details": formatted_errors
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    final catch-all for unhandled server exceptions.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": "internal_server_error",
            "message": "An unexpected systemic error occurred."
        }
    )