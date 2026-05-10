from pathlib import Path
import json
import re

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 설정 파일 읽기
config_path = Path("config.json")
config = json.loads(config_path.read_text(encoding="utf-8"))


data_dir = Path(config["data_dir"])
output_dir = Path(config["output_dir"])
output_json_file = output_dir / config["output_json_file"]
output_report_file = output_dir / config["output_report_file"]


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=config["chunk_size"],
    chunk_overlap=config["chunk_overlap"],
    separators=config["separators"],
)


all_chunks = []
chunk_id = 1


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def split_markdown_by_section(text: str) -> list[dict]:
    sections = []
    current_title = None
    current_lines = []

    lines = text.split("\n")

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if heading_match:
            if current_lines:
                sections.append({
                    "section": current_title,
                    "text": "\n".join(current_lines).strip(),
                })

            current_title = heading_match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "section": current_title,
            "text": "\n".join(current_lines).strip(),
        })

    return [section for section in sections if section["text"]]


def add_chunks(
    chunk_texts: list[str],
    file_path: Path,
    document_type: str,
    page_number: int | None = None,
    section: str | None = None,
):
    global chunk_id

    for chunk_text in chunk_texts:
        metadata = {
            "source": file_path.name,
            "file_path": str(file_path),
            "document_type": document_type,
            "chunk_id": chunk_id,
            "char_count": len(chunk_text),
        }

        if page_number is not None:
            metadata["page"] = page_number

        if section is not None:
            metadata["section"] = section

        all_chunks.append({
            "text": chunk_text,
            "metadata": metadata,
        })

        chunk_id += 1


def process_markdown(file_path: Path):
    text = file_path.read_text(encoding="utf-8")
    text = clean_text(text)

    sections = split_markdown_by_section(text)

    for section_data in sections:
        section_text = section_data["text"]
        section_title = section_data["section"]

        chunk_texts = text_splitter.split_text(section_text)

        add_chunks(
            chunk_texts=chunk_texts,
            file_path=file_path,
            document_type="markdown",
            section=section_title,
        )


def process_pdf(file_path: Path):
    reader = PdfReader(str(file_path))

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if not page_text:
            continue

        page_text = clean_text(page_text)
        chunk_texts = text_splitter.split_text(page_text)

        add_chunks(
            chunk_texts=chunk_texts,
            file_path=file_path,
            document_type="pdf",
            page_number=page_number,
        )


def create_report(chunks: list[dict]) -> str:
    report_lines = []

    report_lines.append("Chunk 품질 점검 리포트")
    report_lines.append("=" * 50)
    report_lines.append(f"총 Chunk 개수: {len(chunks)}")
    report_lines.append(f"chunk_size 설정값: {config['chunk_size']}")
    report_lines.append(f"chunk_overlap 설정값: {config['chunk_overlap']}")
    report_lines.append("")

    if chunks:
        char_counts = [chunk["metadata"]["char_count"] for chunk in chunks]

        report_lines.append(f"가장 짧은 Chunk 길이: {min(char_counts)}자")
        report_lines.append(f"가장 긴 Chunk 길이: {max(char_counts)}자")
        report_lines.append(f"평균 Chunk 길이: {sum(char_counts) // len(char_counts)}자")
        report_lines.append("")

    source_counts = {}

    for chunk in chunks:
        source = chunk["metadata"]["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    report_lines.append("파일별 Chunk 개수")
    report_lines.append("-" * 50)

    for source, count in source_counts.items():
        report_lines.append(f"{source}: {count}개")

    report_lines.append("")
    report_lines.append("Chunk 상세 목록")
    report_lines.append("=" * 50)

    for chunk in chunks:
        metadata = chunk["metadata"]

        report_lines.append(f"[Chunk {metadata['chunk_id']}]")
        report_lines.append(f"source: {metadata['source']}")
        report_lines.append(f"type: {metadata['document_type']}")
        report_lines.append(f"length: {metadata['char_count']}자")

        if "page" in metadata:
            report_lines.append(f"page: {metadata['page']}")

        if "section" in metadata:
            report_lines.append(f"section: {metadata['section']}")

        preview = chunk["text"].replace("\n", " ")
        report_lines.append(f"preview: {preview[:120]}")
        report_lines.append("-" * 50)

    return "\n".join(report_lines)


for file_path in data_dir.glob("*"):
    if file_path.suffix.lower() == ".md":
        process_markdown(file_path)

    elif file_path.suffix.lower() == ".pdf":
        process_pdf(file_path)


output_dir.mkdir(exist_ok=True)

output_json_file.write_text(
    json.dumps(all_chunks, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

report_text = create_report(all_chunks)

output_report_file.write_text(
    report_text,
    encoding="utf-8"
)


md_count = len(list(data_dir.glob("*.md")))
pdf_count = len(list(data_dir.glob("*.pdf")))

print(f"처리한 Markdown 파일 수: {md_count}")
print(f"처리한 PDF 파일 수: {pdf_count}")
print(f"총 Chunk 개수: {len(all_chunks)}")
print(f"JSON 저장 위치: {output_json_file}")
print(f"리포트 저장 위치: {output_report_file}")
print(f"현재 chunk_size: {config['chunk_size']}")
print(f"현재 chunk_overlap: {config['chunk_overlap']}")