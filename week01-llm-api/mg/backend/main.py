from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest, ModelsResponse, ModelInfo
from services.llm_service import stream_chat, AVAILABLE_MODELS

app = FastAPI(title="LLM Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    models = [ModelInfo(**m) for m in AVAILABLE_MODELS]
    return ModelsResponse(models=models)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    return StreamingResponse(
        stream_chat(messages, request.model, request.temperature),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
