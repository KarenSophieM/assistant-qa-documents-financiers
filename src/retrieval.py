"""Retrieval : recherche des passages les plus pertinents pour une question donnée."""

import json
import os
import pathlib
from typing import Dict, List

import numpy as np
import voyageai
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
EMBED_MODEL = "voyage-3.5"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return a_norm @ b_norm.T


def load_index():
    chunks = json.loads((DATA_DIR / "processed" / "chunks.json").read_text(encoding="utf-8"))
    embeddings = np.load(DATA_DIR / "processed" / "embeddings.npy")
    return chunks, embeddings


def retrieve(question: str, chunks: List[Dict], embeddings: np.ndarray, top_k: int = 8) -> List[Dict]:
    """input_type='query' (asymétrique par rapport à l'indexation en 'document'),
    recommandé par Voyage AI pour de meilleurs résultats de recherche."""
    client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    result = client.embed([question], model=EMBED_MODEL, input_type="query")
    query_vec = np.array(result.embeddings, dtype=np.float32)

    scores = cosine_similarity(query_vec, embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]

    return [{**chunks[i], "score": float(scores[i])} for i in top_indices]


if __name__ == "__main__":
    chunks, embeddings = load_index()
    question = "Quel est le résultat net du Groupe au premier semestre 2026 ?"
    results = retrieve(question, chunks, embeddings, top_k=3)

    print(f"Question : {question}\n")
    for r in results:
        print(f"[page {r['page']}, score {r['score']:.3f}]")
        print(r["text"][:300])
        print()
