from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.sessions import router as sessions_router
from backend.api.users import router as users_router
from backend.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(title="FinoneAgent API", version="0.1.0", lifespan=lifespan)

_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# 通过环境变量追加额外来源，例如 CORS_EXTRA_ORIGINS=http://192.168.1.5:5173
_extra = os.getenv("CORS_EXTRA_ORIGINS", "")
if _extra:
    _CORS_ORIGINS.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=r"http://\d+\.\d+\.\d+\.\d+:5173",  # 允许局域网任意 IP:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(chat_router)


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "FinoneAgent API"}
