# Assistant Q&A sur documents financiers publics

Assistant qui répond à des questions sur des documents financiers publics (extraits du Document d'Enregistrement Universel 2025 de BNP Paribas), en citant systématiquement la page source et en répondant honnêtement "je ne trouve pas" quand l'information n'est pas présente dans le document.

Projet construit dans le cadre d'une candidature pour un poste Développeur Agent IA / Agentic AI, en collaboration avec [Lionel](https://github.com/llunda).

## Fonctionnement

Le projet s'appuie sur une architecture RAG (Retrieval-Augmented Generation) :

1. **Ingestion** : extraction du texte des documents PDF sources, avec conservation du numéro de page
2. **Chunking** : découpage du texte en passages de taille raisonnable
3. **Indexation** : transformation de chaque passage en vecteur d'embedding (Voyage AI)
4. **Retrieval** : récupération des passages les plus pertinents pour une question donnée
5. **Génération encadrée** : réponse de Claude à partir des seuls passages récupérés, avec citation de page

## Statut

En cours de construction. Détails techniques et résultats d'évaluation à venir.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Licence

Projet pédagogique, à but de démonstration de compétences.
