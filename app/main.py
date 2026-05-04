from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import TimingMiddleware
from app.core.exceptions import validation_exception_handler, global_exception_handler
from app.database.client import engine
from app.services.predictor import predictor
from app.api.routers import auth, teams, labels, tickets, collaboration, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize predictor asynchronously (loads ONNX + tokenizer)
    await predictor.initialize()
    yield
    # Shutdown: Safely dispose of the SQLAlchemy engine pool
    await engine.dispose()

app = FastAPI(
    title="Bug Triage API",
    description="Enterprise issue tracking backend with multi-task CodeBERT routing.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your React app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# --- Routers ---
# Identity and Access
app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(labels.router)

# Core Operations & Telemetry
app.include_router(tickets.router)
app.include_router(collaboration.router)
app.include_router(analytics.router)

# --- System Probes ---
@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe for infrastructure monitoring."""
    return {
        "status": "healthy",
        "database_pool": "initialized",
        "model_loaded": getattr(predictor, "_initialized", False)
    }
