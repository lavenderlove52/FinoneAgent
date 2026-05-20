from __future__ import annotations

import time
from collections import defaultdict

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from backend.api.deps import create_access_token, get_current_user
from backend.db.crud import get_user_by_username
from backend.db.models import User

# 简单内存限速：每个 IP 每分钟最多 10 次登录尝试
_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 60

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # 清理过期记录
    _login_attempts[client_ip] = [
        t for t in _login_attempts[client_ip] if now - t < _WINDOW_SECONDS
    ]

    if len(_login_attempts[client_ip]) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请 {_WINDOW_SECONDS} 秒后重试",
        )

    _login_attempts[client_ip].append(now)

    user = get_user_by_username(body.username)
    if user is None or not bcrypt.checkpw(
        body.password.encode(), user.password_hash.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token(user.id)
    return LoginResponse(
        access_token=token,
        user=UserInfo(id=user.id, username=user.username, role=user.role),
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)) -> UserInfo:
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
    )
