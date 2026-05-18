from __future__ import annotations

from typing import Optional

from backend.db.database import get_connection
from backend.db.models import Message, Session, User


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def get_user_by_id(user_id: int) -> Optional[User]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return User(**dict(row))


def get_user_by_username(username: str) -> Optional[User]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return None
    return User(**dict(row))


def list_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY id"
        ).fetchall()
    return [User(**dict(r)) for r in rows]


def create_user(username: str, password_hash: str, role: str = "user") -> User:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        conn.commit()
        user_id = cur.lastrowid
    user = get_user_by_id(user_id)
    assert user is not None
    return user


def delete_user(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

def list_sessions_by_user(user_id: int) -> list[Session]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [Session(**dict(r)) for r in rows]


def get_session(session_id: int) -> Optional[Session]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    if row is None:
        return None
    return Session(**dict(row))


def create_session(user_id: int, title: str = "新会话") -> Session:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
            (user_id, title),
        )
        conn.commit()
        session_id = cur.lastrowid
    session = get_session(session_id)
    assert session is not None
    return session


def delete_session(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()


def update_session_title(session_id: int, title: str) -> Optional[Session]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, session_id),
        )
        conn.commit()
    return get_session(session_id)


def touch_session(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Message CRUD
# ---------------------------------------------------------------------------

def list_messages_by_session(session_id: int) -> list[Message]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [Message(**dict(r)) for r in rows]


def create_message(
    session_id: int, user_id: int, role: str, content: str
) -> Message:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO messages (session_id, user_id, role, content) VALUES (?, ?, ?, ?)",
            (session_id, user_id, role, content),
        )
        conn.commit()
        msg_id = cur.lastrowid
        row = conn.execute(
            "SELECT * FROM messages WHERE id = ?", (msg_id,)
        ).fetchone()
    return Message(**dict(row))
