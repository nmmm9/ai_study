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
    length: int


class AskRawRequest(BaseModel):
    document: str
    question: str
    model: str = "gpt-4o-mini"


class AskChunkedRequest(BaseModel):
    document: str
    question: str
    model: str = "gpt-4o-mini"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3


class Stats(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    time_ms: int
    cost_usd: float
    document_tokens: int
    model_limit: int | None = None


class RawResponse(BaseModel):
    answer: str | None = None
    error: str | None = None
    message: str | None = None
    stats: Stats


class ScoredChunkSchema(BaseModel):
    index: int
    text: str
    score: float
    start: int
    end: int


class ChunksInfo(BaseModel):
    total_count: int
    used: list[ScoredChunkSchema]


class ChunkedResponse(BaseModel):
    answer: str
    stats: Stats
    chunks: ChunksInfo
