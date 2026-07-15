"""
main.py — FastAPI Application Entry Point
------------------------------------------
Responsibilities:
  - Create the FastAPI app instance
  - Configure CORS for local development
  - Register all API routers
  - Add global exception handlers
  - Run database table creation on startup
  - Serve the frontend static files (optional convenience)

Run the server:
  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Interactive API docs:
  http://localhost:8000/docs      (Swagger UI)
  http://localhost:8000/redoc     (ReDoc)
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

# ── Internal imports ──────────────────────────────────────────
from backend.database import create_all_tables
from backend.routers import profile, chat, workouts, meals, motivation, habits, fitness, dashboard

# ── Logging configuration ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("fitness_buddy")


# ── Startup / shutdown lifecycle ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run setup tasks on startup, cleanup on shutdown."""
    logger.info("🏋️  Fitness Buddy starting up…")
    create_all_tables()
    logger.info("✅  Database tables ready.")
    logger.info("📄  API docs: http://localhost:8000/docs")
    yield
    logger.info("👋  Fitness Buddy shutting down.")


# ── FastAPI app instance ──────────────────────────────────────
app = FastAPI(
    title="Fitness Buddy API",
    description=(
        "AI-powered fitness coach built with FastAPI and IBM watsonx.ai (Granite models). "
        "Provides personalised home workout plans, meal suggestions, BMI calculation, "
        "habit tracking, and daily motivation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ─────────────────────────────────────────────────────
# allow_origins=["*"] covers every localhost port and any origin
# during local development.
# In production, replace "*" with your exact frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register all API routers ──────────────────────────────────
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(workouts.router)
app.include_router(meals.router)
app.include_router(motivation.router)
app.include_router(habits.router)
app.include_router(fitness.router)
app.include_router(dashboard.router)


# ── Global exception handlers ─────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected server errors."""
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handle IBM credential / model errors with a helpful message."""
    msg = str(exc)
    logger.error("RuntimeError: %s", msg)

    if "IBM_API_KEY" in msg or "WATSONX_PROJECT_ID" in msg:
        code   = "MISSING_CREDENTIALS"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif "authentication" in msg.lower() or "401" in msg:
        code   = "AUTH_FAILURE"
        status_code = status.HTTP_401_UNAUTHORIZED
    else:
        code   = "SERVICE_ERROR"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={"detail": msg, "code": code},
    )


# ── Health check ──────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """Simple health endpoint for load balancers / uptime monitors."""
    return {
        "status": "ok",
        "service": "Fitness Buddy API",
        "version": "1.0.0",
    }


# ── Serve frontend static files at the root ──────────────────
#
# Mount AFTER all /api/* routes so the static handler never
# shadows the API.  StaticFiles(html=True) automatically serves
# index.html for "/" and any unknown path — which is exactly
# what a single-page app needs.
#
# Browser requests:
#   GET /              → frontend/index.html
#   GET /css/style.css → frontend/css/style.css
#   GET /js/app.js     → frontend/js/app.js

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info("📁  Frontend mounted at / (serving %s)", os.path.abspath(frontend_dir))
else:
    # Fallback JSON response when frontend folder is missing
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "Fitness Buddy API running. Visit /docs for API documentation."}
