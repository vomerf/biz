from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token
from app.core.config import settings
from app.crud import create_user, get_user_by_email, verify_password
from app.deps import current_superuser, get_current_user, get_session
from app.models.auth import User
from app.schemas.auth import (
    RefreshRequest, TokenResponse, UserCreate, UserRead
)

router = APIRouter()


@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, db: AsyncSession = Depends(get_session)):
    """Регистрация пользователя"""
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует."
        )
    new_user = await create_user(db, user.email, user.password)
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(user: UserCreate, db: AsyncSession = Depends(get_session)):
    """Логинимся пользователем

    Получаем access_token и refresh_token токен.
    """
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалижные учетные данные")
    access_token = create_access_token(db_user.email)
    refresh_token = create_refresh_token(db_user.email)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    """Проверка токена и получаение своих данных"""
    return current_user


@router.get("/admin")
async def is_superuser(current_user: User = Depends(current_superuser)):
    """Проверяем, что пользователь является суперпользователем"""
    return {"is_superuser": current_user.is_superuser}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """С помощью refersh_token получаем новый access_token"""
    try:
        payload = jwt.decode(
            req.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный тип токена")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh токен")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh токен")

    new_access = create_access_token(email)

    return TokenResponse(access_token=new_access, refresh_token=req.refresh_token)
