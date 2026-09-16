import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from .database import Base, engine
from .routers.patients import router as patients_router
from .routers.vapi import router as vapi_router
from .routers.dashboard import router as dashboard_router

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Voice AI Patient Registration API",
    version="1.0.0",
    description="REST API and Vapi tool server for the take-home Voice AI patient registration assessment.",
)

app.include_router(patients_router)
app.include_router(vapi_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"data": {"service": "voice-patient-agent", "docs": "/docs", "health": "/health"}, "error": None}


@app.get("/health")
def health():
    return {"data": {"status": "ok"}, "error": None}


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "details": None}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": {"code": "VALIDATION_ERROR", "message": "Invalid request", "details": exc.errors()}},
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logging.getLogger("voice_patient_agent.db").exception("Database error")
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": {"code": "DATABASE_ERROR", "message": "Database operation failed", "details": None}},
    )
