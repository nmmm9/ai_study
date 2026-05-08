from pydantic import BaseModel


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


class EmbedRequest(BaseModel):
    document: str
    chunk_size: int = 500
    chunk_overlap: int = 50


class EmbedResponse(BaseModel):
    collection_name: str
    chunk_count: int


class CollectionItem(BaseModel):
    name: str
    count: int


class CollectionsResponse(BaseModel):
    collections: list[CollectionItem]


class ChatRequest(BaseModel):
    question: str
    collection_names: list[str]
    top_k: int = 5
    model: str = "gpt-4o-mini"
    history: list[dict] = []


class SourceChunk(BaseModel):
    index: int
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    tokens: int
    cost_usd: float
    time_ms: int
