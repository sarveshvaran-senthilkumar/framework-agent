import time
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from logger import logger
from mappers.mapper import ObjectMapper

app = FastAPI(
    title="Object Mapper Service",
    description="",
    version="1.0.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"-> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/map")
def map_object(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    logger.info(f"Mapping payload with keys={list(payload.keys())}")
    mapped = ObjectMapper.map_payload(payload)
    logger.info(f"Mapped result: {mapped}")
    return mapped


if __name__ == "__main__":
    import uvicorn

    logger.info("")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
