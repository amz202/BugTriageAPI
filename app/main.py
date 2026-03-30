import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import inference
from app.services.predictor import predictor_service
from app.core.middleware import TimingMiddleware
from app.core.exceptions import validation_exception_handler, global_exception_handler
from app.database.client import db_state
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_state.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    predictor_service.load_artifacts()
    yield
    await db_state.pool.close()

app = FastAPI(
    title="Bug Triage API",
    description="Inference service for Chromium bug report classification.",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(TimingMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(inference.router)

@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe for orchestration services."""
    return {
        "status": "healthy",
        "model_loaded": predictor_service.is_loaded
    }