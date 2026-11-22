from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import LoginRequest, RegisterRequest

app = FastAPI(title="User Service")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "user-service"}


@app.post("/auth/register", status_code=501)
def register(_request: RegisterRequest) -> None:
    raise HTTPException(
        status_code=501,
        detail="Registration is unavailable because user storage is not configured.",
    )


@app.post("/auth/login", status_code=501)
def login(_request: LoginRequest) -> None:
    raise HTTPException(
        status_code=501,
        detail="Authentication is unavailable because credentials are not stored or verified.",
    )
