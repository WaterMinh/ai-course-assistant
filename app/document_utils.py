import os
from pypdf import PdfReader


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        texts = []

        for page in reader.pages:
            texts.append(page.extract_text() or "")

        return "\n".join(texts)

    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise ValueError("Only PDF, TXT, and MD files are supported.")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def simple_score(query: str, text: str) -> int:
    query_words = set(query.lower().split())
    text_lower = text.lower()

    return sum(1 for word in query_words if word in text_lower)


def find_relevant_chunks(db, query: str, course_id: int, limit: int = 4) -> list[str]:
    from app.models import DocumentChunk

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.course_id == course_id)
        .all()
    )

    ranked = sorted(
        chunks,
        key=lambda c: simple_score(query, c.chunk_text),
        reverse=True
    )

    relevant = [
        c.chunk_text
        for c in ranked
        if simple_score(query, c.chunk_text) > 0
    ]

    if relevant:
        return relevant[:limit]

    # fallback: if keyword search fails, return first chunks from this course
    fallback_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.course_id == course_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .limit(limit)
        .all()
    )

    return [chunk.chunk_text for chunk in fallback_chunks]

def get_course_context(db, course_id: int, limit: int = 12) -> str:
    from app.models import DocumentChunk

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.course_id == course_id)
        .order_by(DocumentChunk.document_id.asc(), DocumentChunk.chunk_index.asc())
        .limit(limit)
        .all()
    )

    return "\n\n---\n\n".join(chunk.chunk_text for chunk in chunks)