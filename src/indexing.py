"""Indexation des passages : transformation de chaque chunk en vecteur d'embedding (Voyage AI)."""

import json
import os
import pathlib
import time

import numpy as np
import voyageai
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
EMBED_MODEL = "voyage-3.5"
BATCH_SIZE = 10
PAUSE_SECONDS = 21  # respecte la limite de 3 requêtes/minute tant que le compte est sans historique de facturation


def embed_chunks(chunks, model: str = EMBED_MODEL, batch_size: int = BATCH_SIZE) -> np.ndarray:
    """Embedde une liste de chunks, par petits lots avec pause entre chaque appel
    (limite temporaire de l'API Voyage pour les comptes récents). input_type='document'
    car ce sont des passages à indexer, pas une question (Voyage distingue les deux
    pour de meilleurs résultats de recherche)."""
    client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    texts = [c["text"] for c in chunks]

    all_embeddings = []
    n_batches = (len(texts) + batch_size - 1) // batch_size
    for batch_num, i in enumerate(range(0, len(texts), batch_size), start=1):
        batch = texts[i : i + batch_size]
        result = client.embed(batch, model=model, input_type="document")
        all_embeddings.extend(result.embeddings)
        print(f"  lot {batch_num}/{n_batches} indexé", flush=True)
        if batch_num < n_batches:
            time.sleep(PAUSE_SECONDS)

    return np.array(all_embeddings, dtype=np.float32)


if __name__ == "__main__":
    chunks_path = DATA_DIR / "processed" / "chunks.json"
    embeddings_path = DATA_DIR / "processed" / "embeddings.npy"

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    embeddings = embed_chunks(chunks)
    np.save(embeddings_path, embeddings)

    print(f"{len(chunks)} passages indexés -> {embeddings_path} (dimension {embeddings.shape[1]})")
