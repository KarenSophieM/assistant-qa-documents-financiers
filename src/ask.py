"""Outil interactif pour poser des questions en direct, utile pour une démo
en entretien (pas besoin de relire du code, juste taper une question)."""

import pathlib
import sys

# Permet d'importer generation.py/retrieval.py aussi bien en lançant ce fichier
# directement (`python src/ask.py`) qu'en l'important comme module
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generation import answer_question
from retrieval import load_index


def main():
    print("Chargement de l'index...")
    chunks, embeddings = load_index()
    print(f"Prêt ({len(chunks)} passages indexés). Tape une question, ou 'quit' pour sortir.\n")

    while True:
        try:
            question = input("Question : ").strip()
        except EOFError:
            break
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        print()
        print(answer_question(question, chunks, embeddings))
        print()


if __name__ == "__main__":
    main()
