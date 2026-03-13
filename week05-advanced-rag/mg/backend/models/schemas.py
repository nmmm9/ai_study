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
    dimension: int
    embed_time_ms: int
    store_time_ms: int
    total_time_ms: int
    embed_cost: float


class CollectionItem(BaseModel):
    name: str
    count: int


class CollectionsResponse(BaseModel):
    collections: list[CollectionItem]


class PipelineStep(BaseModel):
    name: str
    label: str
    time_ms: int
    detail: str | None = None


class SourceChunk(BaseModel):
    index: int
    text: str
    score: float
    rerank_score: float | None = None


class RagRequest(BaseModel):
    question: str
    collection_name: str
    top_k: int = 5
    model: str = "gpt-4o-mini"
    mode: str = "basic"


class RagResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    steps: list[PipelineStep]
    timing: dict[str, int]
    cost_usd: float
    total_tokens: int
    mode: str
    hyde_query: str | None = None


class CompareRequest(BaseModel):
    question: str
    collection_name: str
    top_k: int = 5
    model: str = "gpt-4o-mini"


class CompareResponse(BaseModel):
    basic: RagResponse
    advanced: RagResponse
