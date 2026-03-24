"""Agent API router — SSE streaming with real-time tool activity."""

import asyncio
import json
import queue
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.event_stream import event_queue_var
from app.agents.regulatory_agent import create_agent

router = APIRouter(prefix="/api", tags=["agent"])

_SESSION_TTL = 3600
_SENTINEL = object()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: str | None = None


class _Session:
    __slots__ = ("agent", "last_used")

    def __init__(self):
        self.agent = create_agent()
        self.last_used = time.monotonic()

    def touch(self):
        self.last_used = time.monotonic()


_sessions: dict[str, _Session] = {}


def _get_or_create_session(session_id: str) -> _Session:
    if session_id not in _sessions:
        _sessions[session_id] = _Session()
    session = _sessions[session_id]
    session.touch()
    return session


def _evict_stale_sessions():
    now = time.monotonic()
    stale = [sid for sid, s in _sessions.items() if now - s.last_used > _SESSION_TTL]
    for sid in stale:
        _sessions.pop(sid, None)


def _run_agent_with_events(session: _Session, user_message: str, eq: queue.Queue):
    """Run agent in a thread; tool events flow through the contextvars queue."""
    token = event_queue_var.set(eq)
    try:
        result = session.agent(user_message)
        eq.put({"type": "response", "content": str(result)})
    except Exception as e:
        eq.put({"type": "error", "message": str(e)})
    finally:
        event_queue_var.reset(token)
        eq.put(_SENTINEL)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    _evict_stale_sessions()

    session_id = request.session_id or str(uuid.uuid4())

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    user_message = request.messages[-1].content
    session = _get_or_create_session(session_id)

    eq: queue.Queue = queue.Queue()

    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, _run_agent_with_events, session, user_message, eq)

    async def generate() -> AsyncGenerator[str, None]:
        yield _sse({"type": "status", "message": "エージェントが分析を開始しました..."})

        while True:
            try:
                event = await asyncio.to_thread(eq.get, timeout=0.2)
            except Exception:
                continue

            if event is _SENTINEL:
                break

            if event.get("type") == "response":
                yield _sse({
                    "type": "response",
                    "session_id": session_id,
                    "content": event["content"],
                })
            elif event.get("type") == "error":
                yield _sse({"type": "error", "message": event["message"]})
            else:
                yield _sse(event)

        yield _sse({"type": "done", "session_id": session_id})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"status": "ok"}
