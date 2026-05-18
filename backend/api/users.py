from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.deps import get_current_user, require_admin
from backend.db import crud
from backend.db.models import User

router = APIRouter(prefix="/api/users", tags=["users"])


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@router.get("", response_model=list[UserOut])
def list_users(admin: User = Depends(require_admin)) -> list[UserOut]:
    users = crud.list_users()
    return [UserOut(id=u.id, username=u.username, role=u.role, created_at=u.created_at) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest, admin: User = Depends(require_admin)
) -> UserOut:
    existing = crud.get_user_by_username(body.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="用户名已存在"
        )
    if body.role not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="role 必须为 user 或 admin"
        )
    password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = crud.create_user(body.username, password_hash, body.role)
    return UserOut(id=user.id, username=user.username, role=user.role, created_at=user.created_at)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    current_user: User = Depends(get_current_user),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己"
        )
    target = crud.get_user_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    crud.delete_user(user_id)
