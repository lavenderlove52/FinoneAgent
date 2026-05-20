from __future__ import annotations

import os
import warnings
from datetime import timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.db.crud import get_user_by_id
from backend.db.models import User

_DEFAULT_DEV_SECRET = "finone-dev-secret"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_DEV_SECRET)

_env = os.getenv("APP_ENV", "development").lower()

_KNOWN_WEAK_KEYS = {_DEFAULT_DEV_SECRET, "your-secret-key-here", "secret", "password", ""}

# 通用：空串始终拒绝
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY 不能为空，请设置强随机密钥。")

# 生产：禁止已知弱密钥
if _env == "production" and SECRET_KEY in _KNOWN_WEAK_KEYS:
    raise RuntimeError(
        "生产环境禁止使用默认或已知弱密钥，请通过 JWT_SECRET_KEY 设置强随机密钥。"
    )

# 通用：弱密钥警告（不中断，但记录）
if len(SECRET_KEY) < 32:
    warnings.warn(
        f"JWT_SECRET_KEY 长度为 {len(SECRET_KEY)} 字符，建议使用至少 32 字符的随机密钥。",
        stacklevel=2,
    )

# JWT 时钟偏差容差（秒），应对服务器 NTP 偏差
_JWT_LEEWAY = timedelta(seconds=30)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

bearer_scheme = HTTPBearer()


def create_access_token(user_id: int) -> str:
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], leeway=_JWT_LEEWAY
        )
        user_id = int(payload["sub"])
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已过期")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 Token")
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("decode_token 意外错误: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 验证失败")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    user_id = decode_token(credentials.credentials)
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return user
