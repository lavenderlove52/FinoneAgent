from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str
    created_at: str


@dataclass
class Session:
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str


@dataclass
class Message:
    id: int
    session_id: int
    user_id: int
    role: str
    content: str
    created_at: str
