from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.deep_research import DeepResearchAgent, THINKING_PREFIX
from backend.api.deps import get_current_user
from backend.db import crud
from backend.db.models import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str


async def _run_ask_stream(agent: DeepResearchAgent, query: str):
    """在独立线程中运行同步 ask_stream，通过有界 asyncio.Queue 传递 chunks。"""
    # 有界队列：最多缓冲 64 个 chunk，避免生产者无限堆积
    result_queue: asyncio.Queue[str | BaseException | None] = asyncio.Queue(maxsize=64)
    loop = asyncio.get_running_loop()  # 使用当前运行循环（Python 3.10+ 推荐）

    def run_sync() -> None:
        try:
            for chunk in agent.ask_stream(query):
                # 保持阻塞直到队列有空位
                asyncio.run_coroutine_threadsafe(result_queue.put(chunk), loop).result()
        except BaseException as exc:  # 保留原始异常类型与 traceback
            asyncio.run_coroutine_threadsafe(result_queue.put(exc), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(result_queue.put(None), loop).result()

    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()

    while True:
        item = await result_queue.get()
        if item is None:
            break
        if isinstance(item, BaseException):
            raise item
        yield item


async def _event_stream(
    agent: DeepResearchAgent,
    query: str,
    session_id: int,
    user_id: int,
) -> AsyncGenerator[str, None]:
    full_content = ""
    full_thinking = ""
    try:
        async for chunk in _run_ask_stream(agent, query):
            if chunk.startswith(THINKING_PREFIX):
                # 思考进度：单独事件，不计入最终消息内容
                thinking_piece = chunk[len(THINKING_PREFIX):]
                full_thinking += thinking_piece
                data = json.dumps(
                    {"type": "thinking", "content": thinking_piece},
                    ensure_ascii=False,
                )
                yield f"data: {data}\n\n"
            else:
                # 最终答案 chunk
                full_content += chunk
                data = json.dumps(
                    {"type": "chunk", "content": chunk},
                    ensure_ascii=False,
                )
                yield f"data: {data}\n\n"

        msg = crud.create_message(session_id, user_id, "assistant", full_content)
        crud.touch_session(session_id)
        done_data = json.dumps(
            {"type": "done", "message_id": msg.id, "thinking": full_thinking},
            ensure_ascii=False,
        )
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
