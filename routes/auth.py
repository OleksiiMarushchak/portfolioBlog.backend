from fastapi import APIRouter, Depends, Request, Response, status, HTTPException

import config
from shemas.auth import Auth, CreateUserWithToken
from core.database import AsyncSession, get_db
from sqlalchemy import select, insert
from models.user import User
from config import settings
from datetime import datetime, timedelta, timezone
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from models.sessions import Session

from core.dependencies import get_current_user
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def create_user(
    data: CreateUserWithToken,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.username == data.username)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    if len(data.password) <= 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too short",
        )
    passwordHash = hash_password(data.password)
    ins = insert(User).values(username=data.username, password=passwordHash)
    await db.execute(ins)
    await db.commit()

    return {"message": "User created successfully"}

@router.post("/login")
async def login_user(
    data: Auth,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(
        User.username == data.username
    )

    result = await db.execute(stmt)

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(
        data.password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Access JWT
    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    # Refresh token
    refresh_token = create_refresh_token()

    refresh_token_hash = hash_refresh_token(
        refresh_token
    )

    now = datetime.now(timezone.utc)

    session = Session(
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        user_agent=request.headers.get("user-agent"),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        created_at=now,
        last_used_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(session)

    await db.commit()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="Strict",
        secure=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
        }
    }

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    stmt = select(Session).where(
        Session.refresh_token_hash == hash_refresh_token(refresh_token),
        Session.expires_at > datetime.now(timezone.utc),
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    # Access JWT
    access_token = create_access_token(
        {
            "sub": str(session.user_id),
        }
    )

    # Refresh token
    refresh_token = create_refresh_token()

    refresh_token_hash = hash_refresh_token(
        refresh_token
    )

    now = datetime.now(timezone.utc)

    session = Session(
        user_id=session.user_id,
        refresh_token_hash=refresh_token_hash,
        user_agent=request.headers.get("user-agent"),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        created_at=now,
        last_used_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(session)

    await db.commit()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="Strict",
        secure=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    
    return {
        "message": "Token refreshed successfully",
    }

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
    }