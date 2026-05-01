from __future__ import annotations

import re


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 180) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        window = cleaned[start:end]
        split_at = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("; "))
        if split_at > max_chars * 0.45 and end < len(cleaned):
            end = start + split_at + 1
            window = cleaned[start:end]

        chunks.append(window.strip())
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)

    return [chunk for chunk in chunks if chunk]
