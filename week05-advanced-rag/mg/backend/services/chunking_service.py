from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    index: int
    text: str
    start: int
    end: int


def chunk_text(
    text: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    texts = splitter.split_text(text)

    chunks = []
    pos = 0
    for i, chunk_content in enumerate(texts):
        start = text.find(chunk_content, pos)
        if start == -1:
            start = text.find(chunk_content[:80])
            if start == -1:
                start = pos
        end = start + len(chunk_content)
        chunks.append(Chunk(index=i, text=chunk_content, start=start, end=end))
        pos = start + max(1, len(chunk_content) - chunk_overlap)

    return chunks
