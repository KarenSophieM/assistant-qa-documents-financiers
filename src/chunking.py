"""Découpage du texte de chaque page en passages de taille raisonnable (chunking).

Chaque passage reste associé à sa page d'origine, et chevauche légèrement le
passage précédent pour éviter qu'une idée ne soit coupée en deux.
"""

import json
import pathlib
from typing import Dict, List

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

CHUNK_SIZE_WORDS = 400
OVERLAP_WORDS = 60


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(chunk_size - overlap, 1)
    start = 0
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks


def chunk_pages(pages: List[Dict], chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> List[Dict]:
    """Découpe chaque page en passages. Ne découpe jamais à cheval entre deux pages,
    pour que chaque passage reste rattaché à un seul numéro de page."""
    result = []
    chunk_id = 0
    for page in pages:
        for chunk in chunk_text(page["text"], chunk_size, overlap):
            result.append({"chunk_id": chunk_id, "page": page["page"], "text": chunk})
            chunk_id += 1
    return result


if __name__ == "__main__":
    in_path = DATA_DIR / "processed" / "pages.json"
    out_path = DATA_DIR / "processed" / "chunks.json"

    pages = json.loads(in_path.read_text(encoding="utf-8"))
    chunks = chunk_pages(pages)
    out_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    word_counts = [len(c["text"].split()) for c in chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    print(f"{len(chunks)} passages -> {out_path} (moyenne {avg_words:.0f} mots/passage)")
