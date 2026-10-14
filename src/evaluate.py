"""Évaluation chiffrée : fait tourner la pipeline complète (retrieval + génération)
sur un jeu de questions (certaines répondables, d'autres pièges), et mesure
automatiquement le pourcentage de bonnes réponses."""

import json
import pathlib
import re

from generation import answer_question
from retrieval import load_index

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
REFUSAL_PHRASE = "je ne trouve pas"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def check_answer(answer: str, item: dict) -> bool:
    normalized = normalize(answer)
    if item["type"] == "trap":
        return REFUSAL_PHRASE in normalized
    return any(normalize(kw) in normalized for kw in item["expected_keywords"])


def run_evaluation():
    chunks, embeddings = load_index()
    questions = json.loads((DATA_DIR / "eval" / "questions.json").read_text(encoding="utf-8"))

    results = []
    for item in questions:
        answer = answer_question(item["question"], chunks, embeddings)
        correct = check_answer(answer, item)
        results.append({**item, "answer": answer, "correct": correct})

        status = "OK" if correct else "ECHEC"
        print(f"[{status}] #{item['id']} ({item['type']}) {item['question']}")
        if not correct:
            print(f"        réponse obtenue : {answer[:250]}")

    n_correct = sum(r["correct"] for r in results)
    n_answerable = sum(1 for r in results if r["type"] == "answerable")
    n_trap = sum(1 for r in results if r["type"] == "trap")
    n_correct_answerable = sum(1 for r in results if r["type"] == "answerable" and r["correct"])
    n_correct_trap = sum(1 for r in results if r["type"] == "trap" and r["correct"])

    print()
    print(f"Score global : {n_correct}/{len(results)} ({n_correct / len(results) * 100:.0f}%)")
    print(f"  dont questions répondables : {n_correct_answerable}/{n_answerable}")
    print(f"  dont questions pièges (refus honnête attendu) : {n_correct_trap}/{n_trap}")

    out_path = DATA_DIR / "eval" / "results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDétail complet sauvegardé -> {out_path}")


if __name__ == "__main__":
    run_evaluation()
