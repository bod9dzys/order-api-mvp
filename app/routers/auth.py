from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..database import SessionLocal
from .. import crud, schemas
from ..security import create_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_MIN = 5
REFRESH_MIN = 1440

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ErrorSchema = schemas.ErrorSchema


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a user account with email and password (stored as a bcrypt hash).",
    responses={
        400: {
            "model": ErrorSchema,
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "Email exists"}
                }
            },
        }
    },
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.UserRead:
    """
    Registers a new user.
    """
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email exists"
        )
    return crud.create_user(db, user)


@router.post(
    "/login",
    summary="Authenticate user and return tokens",
    description="Validates credentials and returns access and refresh JWT tokens.",
    responses={
        401: {
            "model": ErrorSchema,
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Bad credentials"}
                }
            },
        }
    },
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Logs in a user and issues JWT tokens.
    """
    db_user = crud.get_user_by_email(db, form.username)
    if not db_user or not crud.verify_password(form.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad credentials"
        )
    access = create_token({"sub": str(db_user.id)}, ACCESS_MIN)
    refresh = create_token({"sub": str(db_user.id)}, REFRESH_MIN)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Exchanges a valid refresh token for a new access token.",
    responses={
        401: {
            "model": ErrorSchema,
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid token"}
                }
            },
        }
    },
)
def refresh(token: str) -> Dict[str, str]:
    """
    Generates a new access token using the provided refresh token.
    """
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    new_token = create_token({"sub": payload["sub"]}, ACCESS_MIN)
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
