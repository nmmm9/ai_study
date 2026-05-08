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
    length: int


# ─── Embed ───
class EmbedRequest(BaseModel):
    document: str
    chunk_size: int = 500
    chunk_overlap: int = 50
    collection_name: str | None = None


class EmbedResponse(BaseModel):
    collection_name: str
    chunk_count: int
    dimension: int
    embed_time_ms: int
    store_time_ms: int
    total_time_ms: int
    embed_cost: float


# ─── Search ───
class VectorDBSearchRequest(BaseModel):
    question: str
    collection_name: str
    model: str = "gpt-4o-mini"
    top_k: int = 3


class MemorySearchRequest(BaseModel):
    question: str
    document: str
    model: str = "gpt-4o-mini"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3


class ScoredChunkSchema(BaseModel):
    index: int
    text: str
    score: float


class TimingBreakdown(BaseModel):
    embed_ms: int
    search_ms: int
    llm_ms: int
    total_ms: int


class SearchResponse(BaseModel):
    answer: str
    timing: TimingBreakdown
    cost_usd: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    used_chunks: list[ScoredChunkSchema]
    chunk_count: int


# ─── Visualization ───
class VizChunkPoint(BaseModel):
    x: float
    y: float
    index: int
    text_preview: str


class Point2D(BaseModel):
    x: float
    y: float


class VizResponse(BaseModel):
    points: list[VizChunkPoint]
    query_point: Point2D | None = None


# ─── Collections ───
class CollectionItem(BaseModel):
    name: str
    count: int


class CollectionsResponse(BaseModel):
    collections: list[CollectionItem]
