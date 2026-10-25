"""IntelliDoc — FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import create_tables
from app.routers import auth, scans, dashboard, teams

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="IntelliDoc API",
    description=(
        "AI-Assisted Documentation Drift Detector with Team Code-Quality Oversight. "
        "Detects drift between Python docstrings and function signatures using AST analysis."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    create_tables()
    print("✅ IntelliDoc backend started. Database tables ready.")


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(teams.router, prefix="/api")


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "IntelliDoc API",
        "version": "1.0.0",
        "ai_groq": bool(settings.GROQ_API_KEY),
        "ai_gemini": bool(settings.GEMINI_API_KEY),
    }


@app.get("/", tags=["Root"])
def root():
    return {"message": "IntelliDoc API — see /api/docs for documentation"}
