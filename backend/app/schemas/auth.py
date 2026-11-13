from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    name: str
    email: str
    role: UserRole


class TokenPayload(BaseModel):
    sub: str  # user email
    user_id: str
    role: str

