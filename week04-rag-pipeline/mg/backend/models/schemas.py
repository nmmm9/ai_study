from pydantic import BaseModel


# ─── Samples ───

class SampleInfo(BaseModel):
    id: str
    title: str
    length: int

class SamplesResponse(BaseModel):
    samples: list[SampleInfo]

class SampleDetailResponse(BaseModel):
    id: str
    title: str
    content: str


# ─── Embed ───

class EmbedRequest(BaseModel):
    document: str
    chunk_size: int = 500
    chunk_overlap: int = 50

class EmbedResponse(BaseModel):
    collection_name: str
    chunk_count: int
    dimension: int
    embed_time_ms: int
    store_time_ms: int
    total_time_ms: int
    embed_cost: float


# ─── Collections ───

class CollectionItem(BaseModel):
    name: str
    count: int

class CollectionsResponse(BaseModel):
    collections: list[CollectionItem]


# ─── Pipeline ───

class PipelineStep(BaseModel):
    name: str
    label: str
    time_ms: int
    detail: str | None = None

class SourceChunk(BaseModel):
    index: int
    text: str
    score: float

class RagResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    steps: list[PipelineStep]
    timing: dict
    cost_usd: float
    total_tokens: int


# ─── Requests ───

class RagRequest(BaseModel):
    question: str
    collection_name: str
    top_k: int = 5
    model: str = "gpt-4o-mini"

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    collection_name: str
    history: list[ChatMessage] = []
    top_k: int = 5
    model: str = "gpt-4o-mini"
