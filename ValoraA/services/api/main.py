"""
services/api/main.py

Main FastAPI application entry point for Valora AI — a professional
AI-powered voice generation platform.

This module wires together the TTS model, inference service, and
preprocessing pipeline (services/tts/*) into a production-ready FastAPI
application, including lifespan-managed startup/shutdown, request
logging, security middleware, global exception handling, and health
diagnostics endpoints.
"""

from __future__ import annotations

import logging
from pathlib import Path
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from services.api.limiter import limiter
from services.tts.config import settings
from services.tts.inference import TTSInferenceError, get_tts_service
from services.tts.utils import get_gpu_info, get_logger

logger = get_logger("valora.api.main")

APP_TITLE = "Valora AI"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Professional AI-powered voice generation platform."

ALLOWED_HOSTS = ["*"]
ALLOWED_ORIGINS = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown lifecycle.

    On startup: loads and warms up the TTS model, verifies CUDA
    availability, and logs GPU diagnostics. On shutdown: releases GPU
    memory and gracefully shuts down the inference service's thread
    pool and underlying model.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control is yielded back to the running application.
    """
    logger.info("Starting %s v%s (env=%s)...", APP_TITLE, APP_VERSION, settings.ENV)

    try:
        gpu_info = get_gpu_info()
        if gpu_info.get("cuda_available"):
            logger.info("CUDA is available. GPU info: %s", gpu_info)
        else:
            logger.warning("CUDA is not available; running on CPU.")

        try:
            service = get_tts_service()
            service.warm_up()
            app.state.tts_service = service
            logger.info("%s startup complete. Health: %s", APP_TITLE, service.health_check())
        except Exception as tts_exc:
            logger.warning("TTS warm-up deferred: %s. Application will continue and initialize on demand.", tts_exc)
            app.state.tts_service = get_tts_service()
    except Exception as exc:
        logger.exception("Fatal error during application startup.")
        raise

    yield

    logger.info("Shutting down %s...", APP_TITLE)
    try:
        service = getattr(app.state, "tts_service", None)
        if service is not None:
            service.shutdown()
    except Exception:
        logger.exception("Error occurred while shutting down TTS inference service.")
    finally:
        logger.info("%s shutdown complete.", APP_TITLE)


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
)
app.state.limiter = limiter


# ==================================================================== #
# Middleware
# ==================================================================== #

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def request_logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Log request/response metadata and attach security headers and a
    unique request ID to every response.

    Args:
        request: The incoming HTTP request.
        call_next: The next handler in the middleware chain.

    Returns:
        Response: The outgoing HTTP response, annotated with a request
            ID and standard security headers.
    """
    request_id = uuid.uuid4().hex
    start_time = time.monotonic()

    logger.info(
        "Request started | id=%s | method=%s | path=%s | client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
    except RequestValidationError as exc:
        response = await validation_exception_handler(request, exc)
    except StarletteHTTPException as exc:
        response = await http_exception_handler(request, exc)
    except TTSInferenceError as exc:
        response = await tts_inference_exception_handler(request, exc)
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.exception(
            "Request failed | id=%s | method=%s | path=%s | elapsed_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        response = await unhandled_exception_handler(request, exc)

    elapsed_ms = (time.monotonic() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

    logger.info(
        "Request completed | id=%s | method=%s | path=%s | status=%d | elapsed_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )

    return response


# ==================================================================== #
# Global exception handlers
# ==================================================================== #


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors with a structured JSON response.

    Args:
        request: The incoming HTTP request that failed validation.
        exc: The raised validation error.

    Returns:
        JSONResponse: A 422 response describing the validation failure.
    """
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "detail": jsonable_encoder(exc.errors()),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions with a structured JSON response.

    Args:
        request: The incoming HTTP request.
        exc: The raised HTTP exception.

    Returns:
        JSONResponse: A response mirroring the exception's status code.
    """
    logger.warning("HTTP exception on %s: %s", request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "detail": exc.detail,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(TTSInferenceError)
async def tts_inference_exception_handler(
    request: Request, exc: TTSInferenceError
) -> JSONResponse:
    """
    Handle domain-specific TTS inference errors with a structured JSON
    response.

    Args:
        request: The incoming HTTP request.
        exc: The raised TTS inference error.

    Returns:
        JSONResponse: A 500 response describing the synthesis failure.
    """
    logger.error("TTS inference error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "tts_inference_error",
            "detail": str(exc),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for any unhandled exception, ensuring clients
    always receive a well-formed JSON error response.

    Args:
        request: The incoming HTTP request.
        exc: The unhandled exception instance.

    Returns:
        JSONResponse: A 500 response with a generic error message.
    """
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    Handle rate limit exceeded errors with a structured 429 JSON response
    including the remaining seconds until reset.
    """
    reset_timestamp = getattr(exc, "reset_time", None)
    if reset_timestamp:
        retry_after = max(1, int(reset_timestamp - time.time()))
    else:
        retry_after = 60

    error_detail = (
        f"Rate limit exceeded: {exc.detail}. "
        f"Please retry after {retry_after} second(s)."
        if hasattr(exc, "detail") and exc.detail
        else f"Rate limit exceeded. Please retry after {retry_after} second(s)."
    )

    logger.warning(
        "Rate limit exceeded on %s | client=%s | retry_after=%ds",
        request.url.path,
        request.headers.get("X-API-Key") or (request.client.host if request.client else "unknown"),
        retry_after,
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "detail": error_detail,
            "path": str(request.url.path),
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", tags=["General"])
@app.get("/studio", tags=["General"])
@app.get("/introduction", tags=["General"])
@app.get("/features", tags=["General"])
@app.get("/pricing", tags=["General"])
@app.get("/profile", tags=["General"])
@app.get("/voices-ui", tags=["General"])
async def read_root():
    """
    Root endpoint serving the interactive Valora AI Web Studio & platform.
    """
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"name": APP_TITLE, "status": "running"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Return clean Valora AI SVG favicon to avoid 404 logs in browser requests.
    """
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><path id="valora-arc-fav" d="M 16 36 A 36 28 0 0 1 84 36" fill="none"/></defs><text font-family="\'Times New Roman\', serif" font-size="15" font-weight="700" letter-spacing="1.1" fill="#4f46e5"><textPath href="#valora-arc-fav" startOffset="50%" text-anchor="middle">Valora</textPath></text><path d="M 40 48 C 40 42.5 44.5 38 50 38 C 55.5 38 60 42.5 60 48 L 60 62 C 60 67.5 55.5 72 50 72 C 44.5 72 40 67.5 40 62 Z" fill="#4f46e5"/><rect x="37.5" y="56" width="25" height="3" rx="1.5" fill="#4f46e5"/><path d="M 38.5 57.5 C 38.5 74 43.5 78 50 78 C 56.5 78 61.5 74 61.5 57.5" fill="none" stroke="#4f46e5" stroke-width="3.2" stroke-linecap="round"/><rect x="47.5" y="78" width="5" height="17" rx="0.6" fill="#4f46e5"/></svg>'
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/api/status", tags=["General"])
async def api_status() -> Dict[str, str]:
    """
    JSON API status endpoint.
    """
    return {"name": APP_TITLE, "status": "running"}


@app.get("/health", tags=["General"])
async def health_check() -> Dict[str, Any]:
    """
    Report the operational health of the TTS model and inference
    service, including device and GPU diagnostics.

    Returns:
        Dict[str, Any]: Structured health information.

    Raises:
        HTTPException: Implicitly via the global handler if the health
            check itself fails unexpectedly.
    """
    service = get_tts_service()
    model_health = service.health_check()
    gpu_info = get_gpu_info()

    is_healthy = bool(model_health.get("is_loaded", False))

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "environment": settings.ENV,
        "model": model_health,
        "gpu": gpu_info,
    }


@app.get("/version", tags=["General"])
async def get_version() -> Dict[str, str]:
    """
    Report the application and configured TTS model version details.

    Returns:
        Dict[str, str]: Version metadata for the service and model.
    """
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "environment": settings.ENV,
        "model_name": settings.TTS_MODEL_NAME,
    }


# ==================================================================== #
# Routers
# ==================================================================== #

from services.api.routes import tts as tts_routes  # noqa: E402
from services.api.routes import stt as stt_routes  # noqa: E402
from services.api.routes import clone as clone_routes  # noqa: E402
from services.api.routes import auth as auth_routes  # noqa: E402

app.include_router(tts_routes.router)
app.include_router(stt_routes.router)
app.include_router(clone_routes.router)
app.include_router(auth_routes.router)

# Comprehensive aliases for direct root path and /api prefix calls from external frontends
app.add_api_route("/voices", tts_routes.list_voices, methods=["GET"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/api/voices", tts_routes.list_voices, methods=["GET"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/tts/voices", tts_routes.list_voices, methods=["GET"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/api/tts/voices", tts_routes.list_voices, methods=["GET"], tags=["TTS"], include_in_schema=False)

app.add_api_route("/tts", tts_routes.generate_speech, methods=["POST"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/tts/generate", tts_routes.generate_speech, methods=["POST"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/api/tts", tts_routes.generate_speech, methods=["POST"], tags=["TTS"], include_in_schema=False)
app.add_api_route("/api/tts/generate", tts_routes.generate_speech, methods=["POST"], tags=["TTS"], include_in_schema=False)

app.add_api_route("/stt", stt_routes.transcribe_audio, methods=["POST"], tags=["STT"], include_in_schema=False)
app.add_api_route("/stt/transcribe", stt_routes.transcribe_audio, methods=["POST"], tags=["STT"], include_in_schema=False)
app.add_api_route("/api/stt", stt_routes.transcribe_audio, methods=["POST"], tags=["STT"], include_in_schema=False)
app.add_api_route("/api/stt/transcribe", stt_routes.transcribe_audio, methods=["POST"], tags=["STT"], include_in_schema=False)

app.add_api_route("/clone", clone_routes.clone_voice, methods=["POST"], tags=["Voice Cloning"], include_in_schema=False)
app.add_api_route("/api/clone", clone_routes.clone_voice, methods=["POST"], tags=["Voice Cloning"], include_in_schema=False)
app.add_api_route("/tts/clone", clone_routes.clone_voice, methods=["POST"], tags=["Voice Cloning"], include_in_schema=False)
app.add_api_route("/api/tts/clone", clone_routes.clone_voice, methods=["POST"], tags=["Voice Cloning"], include_in_schema=False)

# Ensure upload directory exists and is mounted
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)

if (STATIC_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")

if (STATIC_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")

if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

if UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )