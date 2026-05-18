from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.deep_research import DeepResearchAgent
from backend.api.deps import get_current_user
from backend.db import crud
from backend.db.models import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str


async def _event_stream(
    agent: DeepResearchAgent,
    query: str,
    session_id: int,
    user_id: int,
) -> AsyncGenerator[str, None]:
    full_content = ""
    try:
        for chunk in agent.ask_stream(query):
            full_content += chunk
            data = json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        msg = crud.create_message(session_id, user_id, "assistant", full_content)
        crud.touch_session(session_id)
        done_data = json.dumps({"type": "done", "message_id": msg.id}, ensure_ascii=False)
        yield f"data: {done_data}\n\n"
    except Exception as exc:
        error_data = json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"


@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: int,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = crud.get_session(session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    crud.create_message(session_id, current_user.id, "user", body.query)
    crud.touch_session(session_id)

    agent = DeepResearchAgent()

    return StreamingResponse(
        _event_stream(agent, body.query, session_id, current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
