from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import inference
from app.services.predictor import predictor
from app.core.middleware import TimingMiddleware
from app.core.exceptions import validation_exception_handler, global_exception_handler
from app.database.client import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize ONNX runtime and Tokenizer
    predictor._initialize()
    yield
    # Safely dispose of the SQLAlchemy engine pool on shutdown
    await engine.dispose()

app = FastAPI(
    title="Bug Triage API",
    description="Stateful routing and inference service for Chromium bug report classification.",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Routers
app.include_router(inference.router)

@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe for orchestration services."""
    return {
        "status": "healthy",
        "model_loaded": predictor.session is not None
    }