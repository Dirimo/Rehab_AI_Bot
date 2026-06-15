"""Extract plain text from PDF documents (hospital livrets)."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(data: bytes, max_chars: int = 8000) -> str:
    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
        if sum(len(p) for p in parts) >= max_chars:
            break
    content = "\n\n".join(parts)
    return content[:max_chars]
