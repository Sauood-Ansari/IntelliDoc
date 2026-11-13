from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserOut
from app.services.auth_service import AuthService
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and issue JWT token with role claim (SRS Appendix B).
    """
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not AuthService.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthService.create_access_token(
        user_id=str(user.user_id),
        email=user.email,
        role=user.role.value
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registration endpoint to create new users for evaluation and onboarding.
    """
    if user_in.role != UserRole.PROGRAMMER or user_in.team_id is not None:
        raise HTTPException(403, "Public registration creates unassigned Programmer accounts only")
    if len(user_in.password.encode("utf-8")) > 72:
        raise HTTPException(422, "Password must be at most 72 UTF-8 bytes")
    user_in.email = user_in.email.lower()
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=AuthService.hash_password(user_in.password),
        role=user_in.role,
        team_id=user_in.team_id
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Return authenticated user profile.
    """
    return current_user

