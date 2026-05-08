from dotenv import load_dotenv

load_dotenv()

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import tools to trigger registration
import tools  # noqa: F401

from tools.registry import list_tool_names
from services.react_agent import react_stream

app = FastAPI(title="K-Agent ReAct")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    model: str = "gpt-4o-mini"
    history: list[dict] = []


@app.get("/api/tools")
async def get_tools():
    return {"tools": list_tool_names(), "count": len(list_tool_names())}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE streaming with ReAct traces — Thought → Action → Observation → Answer."""
    async def event_generator():
        async for event_type, data in react_stream(
            req.question, req.model, req.history
        ):
            yield f"data: {json.dumps({'type': event_type, 'data': data}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
