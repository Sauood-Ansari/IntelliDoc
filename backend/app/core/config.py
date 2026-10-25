"""IntelliDoc — Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://intellidoc:intellidoc@localhost:5432/intellidoc")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-minimum-32chars")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # AI Providers
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # App
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    MAX_SOURCE_SIZE_MB: int = int(os.getenv("MAX_SOURCE_SIZE_MB", "10"))
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    MAX_AI_CONTEXT_CHARS: int = int(os.getenv("MAX_AI_CONTEXT_CHARS", "8000"))

    # Score weights
    COMPLETENESS_MAX: int = 40
    PARAM_CONSISTENCY_MAX: int = 40
    RETURN_CONSISTENCY_MAX: int = 20

    # Finding penalties
    PENALTY_MISSING_PARAM: float = 5.0
    PENALTY_OBSOLETE_PARAM: float = 8.0
    PENALTY_MISSING_RETURN: float = 4.0
    PENALTY_NO_DOCSTRING: float = 0.0  # handled by completeness component


settings = Settings()
