from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from apps.auth.service.auth import AuthService
from apps.auth.api.deps import get_current_user
from apps.auth.models.admin_user import AdminUser
from apps.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenResponse,
    UserMeResponse,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=LoginResponse)
async def token(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        access, refresh = await service.login(
            username=data.username,
            password=data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        access = await service.refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return TokenResponse(access_token=access)


@router.post("/logout")
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    await service.logout(data.refresh_token)
    return {"ok": True}


@router.get("/me", response_model=UserMeResponse)
async def me(
    current_user: AdminUser = Depends(get_current_user),
):
    return UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        access, refresh = await service.register(
            username=data.username,
            password=data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
    )
