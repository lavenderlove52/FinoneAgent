from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.deps import get_current_user
from backend.db import crud
from backend.db.models import Message, Session, User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionOut(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: int
    session_id: int
    user_id: int
    role: str
    content: str
    created_at: str


class CreateSessionRequest(BaseModel):
    title: str = "新会话"


class UpdateSessionRequest(BaseModel):
    title: str


def _session_out(s: Session) -> SessionOut:
    return SessionOut(
        id=s.id,
        user_id=s.user_id,
        title=s.title,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _message_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        session_id=m.session_id,
        user_id=m.user_id,
        role=m.role,
        content=m.content,
        created_at=m.created_at,
    )


@router.get("", response_model=list[SessionOut])
def list_sessions(current_user: User = Depends(get_current_user)) -> list[SessionOut]:
    sessions = crud.list_sessions_by_user(current_user.id)
    return [_session_out(s) for s in sessions]


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest, current_user: User = Depends(get_current_user)
) -> SessionOut:
    session = crud.create_session(current_user.id, body.title)
    return _session_out(session)


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    body: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    session = crud.get_session(session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    updated = crud.update_session_title(session_id, body.title)
    assert updated is not None
    return _session_out(updated)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int, current_user: User = Depends(get_current_user)
) -> None:
    session = crud.get_session(session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    crud.delete_session(session_id)


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def list_messages(
    session_id: int, current_user: User = Depends(get_current_user)
) -> list[MessageOut]:
    session = crud.get_session(session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    messages = crud.list_messages_by_session(session_id)
    return [_message_out(m) for m in messages]
