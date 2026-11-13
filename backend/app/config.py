import secrets
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    PROJECT_NAME: str = "IntelliDoc API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./intellidoc.db"
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_TIMEOUT: int = 30
    MAX_AI_CONTEXT: int = 24000
    MAX_SOURCE_SIZE: int = 10 * 1024 * 1024
    MAX_EXPANDED_SIZE: int = 30 * 1024 * 1024
    MAX_FILE_SIZE: int = 1024 * 1024
    MAX_ARCHIVE_FILES: int = 1000

    @model_validator(mode="after")
    def secure_production(self):
        if self.ENVIRONMENT == "production" and ("JWT_SECRET_KEY" not in self.model_fields_set or len(self.JWT_SECRET_KEY) < 32):
            raise ValueError("Production requires a persistent JWT_SECRET_KEY of at least 32 characters")
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = secrets.token_urlsafe(48)
        return self

settings = Settings()

