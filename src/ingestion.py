"""Extraction du texte d'un PDF, page par page, avec conservation du numéro de page."""

import json
import pathlib
from typing import Dict, List

from pypdf import PdfReader

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def extract_pages(pdf_path: str) -> List[Dict]:
    """Retourne une liste de {"page": numéro (1-indexé), "text": texte brut de la page}."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page": i, "text": text})
    return pages


if __name__ == "__main__":
    pdf_path = DATA_DIR / "raw" / "bnp-paribas-amendement-s1-2026.pdf"
    out_path = DATA_DIR / "processed" / "pages.json"

    pages = extract_pages(str(pdf_path))
    out_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

    non_empty = sum(1 for p in pages if p["text"].strip())
    print(f"{len(pages)} pages extraites ({non_empty} avec du texte) -> {out_path}")
