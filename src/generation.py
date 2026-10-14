"""Génération encadrée : Claude répond à une question à partir des passages
récupérés par retrieval.py, avec citation de page et refus honnête si
l'information n'est pas présente dans le document."""

import os

import anthropic
from dotenv import load_dotenv

from retrieval import load_index, retrieve

load_dotenv()

GEN_MODEL = "claude-haiku-4-5"
TOP_K = 5

SYSTEM_PROMPT = """Tu es un assistant qui répond à des questions sur un document financier public (BNP Paribas).

Règles strictes :
- Réponds uniquement à partir des extraits fournis ci-dessous, jamais à partir de connaissances générales.
- Cite systématiquement le ou les numéros de page d'où vient ta réponse, au format (page X).
- Si l'information n'est pas présente dans les extraits fournis, réponds exactement :
  "Je ne trouve pas cette information dans le document."
- Ne complète jamais une réponse partielle avec des suppositions."""


def build_context(passages) -> str:
    return "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in passages)


def answer_question(question: str, chunks, embeddings, top_k: int = TOP_K) -> str:
    passages = retrieve(question, chunks, embeddings, top_k=top_k)
    context = build_context(passages)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=GEN_MODEL,
        max_tokens=500,
        # pas de "temperature" (retiré du SDK) ni de "output_config.effort" (non supporté par Haiku 4.5) :
        # la consigne stricte du system prompt suffit à garder une réponse factuelle sur cette tâche fermée
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extraits du document :\n\n{context}\n\nQuestion : {question}",
            }
        ],
    )
    return response.content[0].text


if __name__ == "__main__":
    chunks, embeddings = load_index()

    questions = [
        "Quel est le résultat net du Groupe au premier semestre 2026 ?",
        "Quel est l'effectif total du Groupe BNP Paribas ?",  # question piège : hors périmètre du document retenu
    ]
    for q in questions:
        print(f"Q: {q}")
        print(answer_question(q, chunks, embeddings))
        print()
