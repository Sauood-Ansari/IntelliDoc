from typing import List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes the JWT token and returns the authenticated User entity.
    Raises 401 Unauthorized if invalid or expired (SRS FR-AUTH-001, NFR-SEC-001).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload: TokenPayload = AuthService.verify_token(token)
    if payload is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == payload.sub).first()
    if user is None:
        raise credentials_exception

    return user


class RoleChecker:
    """
    Role-Based Access Control (RBAC) dependency factory (SRS FR-AUTH-002, FR-AUTH-003).
    Enforces authorization rules from the User Access Matrix (SRS Table 3.9).
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Pre-configured Role Checkers for easy router application
allow_programmer = RoleChecker([UserRole.PROGRAMMER])
allow_team_lead = RoleChecker([UserRole.TEAM_LEAD])
allow_project_lead = RoleChecker([UserRole.PROJECT_LEAD])
allow_any_lead = RoleChecker([UserRole.TEAM_LEAD, UserRole.PROJECT_LEAD])
allow_all_roles = RoleChecker([UserRole.PROGRAMMER, UserRole.TEAM_LEAD, UserRole.PROJECT_LEAD])

