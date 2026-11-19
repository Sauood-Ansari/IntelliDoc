from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import RequestLimits
from app.database import engine
from app.models.base import Base
# Import all models so Base.metadata knows about them
import app.models

from app.routers.auth import router as auth_router
from app.routers.codebases import router as codebases_router
from app.routers.scans import router as scans_router
from app.routers.functions import router as functions_router
from app.routers.scores import router as scores_router
from app.routers.organization import router as organization_router
from app.routers.memberships import router as memberships_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist (portable setup for evaluation)
    if settings.ENVIRONMENT != "production":
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IntelliDoc: AI-Assisted Documentation Drift Detector with Team Code-Quality Oversight",
    lifespan=lifespan
)

app.add_middleware(RequestLimits)

# CORS Middleware (supports local development with Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(codebases_router, prefix=settings.API_V1_PREFIX)
app.include_router(scans_router, prefix=settings.API_V1_PREFIX)
app.include_router(functions_router, prefix=settings.API_V1_PREFIX)
app.include_router(scores_router, prefix=settings.API_V1_PREFIX)
app.include_router(organization_router, prefix=settings.API_V1_PREFIX)
app.include_router(memberships_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "message": "Welcome to IntelliDoc API",
        "documentation": "/docs",
        "version": settings.VERSION
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "IntelliDoc Backend"
    }

