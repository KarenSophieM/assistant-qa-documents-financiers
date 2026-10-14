# Assistant Q&A sur documents financiers publics

Assistant qui répond à des questions en langage naturel sur un document financier public (extraits du 2ème amendement au Document d'Enregistrement Universel de BNP Paribas, résultats du 1er semestre 2026), en citant systématiquement la page source et en répondant honnêtement **"je ne trouve pas"** quand l'information n'est pas présente dans le document.

Projet construit dans le cadre d'une candidature pour un poste Développeur Agent IA / Agentic AI.

**Score mesuré : 17/20 (85%)** sur un jeu de 20 questions (dont 5 questions pièges, 100% de bonnes réponses dessus). Détail dans [Résultats de l'évaluation](#résultats-de-lévaluation).

---

## Sommaire

- [Le problème que ça résout](#le-problème-que-ça-résout)
- [Fonctionnement (architecture RAG)](#fonctionnement-architecture-rag)
- [Structure du projet](#structure-du-projet)
- [Rôle de chaque fichier](#rôle-de-chaque-fichier)
- [Installation](#installation)
- [Comment tout tester, étape par étape](#comment-tout-tester-étape-par-étape)
- [Résultats de l'évaluation](#résultats-de-lévaluation)
- [Limites connues](#limites-connues)
- [Pistes d'amélioration](#pistes-damélioration)
- [Stack technique et justification des choix](#stack-technique-et-justification-des-choix)
- [Glossaire](#glossaire)
- [Comment en parler en entretien](#comment-en-parler-en-entretien)

---

## Le problème que ça résout

Un LLM seul n'a aucune connaissance du contenu précis d'un document qu'on ne lui fournit pas. Si on lui demande "quel est le résultat net de BNP Paribas au premier semestre 2026" sans lui donner le rapport, il va soit refuser, soit **halluciner** un chiffre plausible mais faux, avec la même assurance qu'une bonne réponse.

La solution standard de l'industrie s'appelle le **RAG** (Retrieval-Augmented Generation) : au lieu de laisser le LLM répondre "de mémoire", on va chercher dans le document les passages pertinents, puis on les lui donne au moment de la question, avec une consigne stricte de ne répondre qu'à partir de ces passages. C'est exactement ce que fait ce projet.

Dans un contexte bancaire, la fiabilité et la traçabilité des réponses (pouvoir dire "voici d'où vient ce chiffre") sont des exigences de conformité, pas un détail technique. Ce projet démontre explicitement cette rigueur : citation systématique de la source, refus honnête plutôt qu'invention, et une mesure chiffrée de la qualité plutôt qu'un simple "ça marche".

## Fonctionnement (architecture RAG)

```
Document PDF
    │
    ▼
① INGESTION      extraction du texte, page par page
    │
    ▼
② CHUNKING       découpage en passages de taille gérable
    │
    ▼
③ INDEXATION     chaque passage → vecteur d'embedding (Voyage AI)
    │                                            (une seule fois, à l'avance)
    ▼
  [ index stocké ]
                                 ┌──────────────────────┐
  Question posée ──────────────▶│ ④ RETRIEVAL           │
                                 │ la question devient   │
                                 │ aussi un vecteur,      │
                                 │ comparée à l'index     │
                                 └──────────┬────────────┘
                                            ▼
                                 passages les plus proches
                                 en sens (pas juste en mots)
                                            │
                                            ▼
                                 ⑤ GÉNÉRATION ENCADRÉE
                                 Claude répond UNIQUEMENT à partir
                                 de ces passages, cite la page,
                                 ou dit "je ne trouve pas"
                                            │
                                            ▼
                                       Réponse finale
```

Les étapes ① à ③ ne se font qu'une seule fois (à l'indexation du document). Les étapes ④ et ⑤ se font à chaque question posée.

## Structure du projet

```
Assist_analyse_doc_financiers/
├── README.md                  ce fichier
├── requirements.txt            dépendances Python
├── .env.example                 variables d'environnement attendues (sans valeurs)
├── .env                         vos vraies clés API (jamais commité, exclu par .gitignore)
├── src/
│   ├── ingestion.py             étape ① : extraction du texte du PDF
│   ├── chunking.py              étape ② : découpage en passages
│   ├── indexing.py              étape ③ : vecteurs d'embedding (Voyage AI)
│   ├── retrieval.py              étape ④ : recherche par similarité
│   ├── generation.py             étape ⑤ : réponse encadrée par Claude
│   ├── evaluate.py               fait tourner les 20 questions et mesure le score
│   └── ask.py                    outil interactif pour poser des questions en direct
└── data/
    ├── raw/
    │   └── bnp-paribas-amendement-s1-2026.pdf   le document source (160 pages)
    ├── processed/                               fichiers générés par les scripts
    │   ├── pages.json            (non versionné, régénérable gratuitement et instantanément)
    │   ├── chunks.json            (non versionné, régénérable gratuitement et instantanément)
    │   └── embeddings.npy          (versionné : coûteux à régénérer, appels API payants)
    └── eval/
        ├── questions.json          le jeu de 20 questions (versionné, écrit à la main)
        └── results.json            détail du dernier run d'évaluation (versionné, preuve du score)
```

## Rôle de chaque fichier

Dans l'ordre où ils interviennent dans le pipeline :

| Fichier | Rôle | Entrée | Sortie |
|---|---|---|---|
| `src/ingestion.py` | Extrait le texte de chaque page du PDF avec `pdfplumber`, en gardant le numéro de page | `data/raw/*.pdf` | `data/processed/pages.json` |
| `src/chunking.py` | Découpe le texte de chaque page en passages de 400 mots avec 60 mots de chevauchement (pour ne jamais couper une idée en deux) | `pages.json` | `data/processed/chunks.json` |
| `src/indexing.py` | Transforme chaque passage en vecteur numérique (embedding) via l'API Voyage AI | `chunks.json` | `data/processed/embeddings.npy` |
| `src/retrieval.py` | Reçoit une question, la transforme aussi en vecteur, et retrouve les passages les plus proches en sens (similarité cosinus) | question + index | liste de passages classés par pertinence |
| `src/generation.py` | Combine `retrieval.py` avec un appel à Claude Haiku : construit le prompt avec les passages retrouvés et une consigne stricte, renvoie la réponse finale | question + index | réponse texte, avec citation de page |
| `src/evaluate.py` | Fait tourner `generation.py` sur les 20 questions de `data/eval/questions.json`, compare automatiquement chaque réponse à ce qui est attendu, calcule le score | `questions.json` + index | `data/eval/results.json` + score affiché |
| `src/ask.py` | Petit outil en ligne de commande pour poser ses propres questions en direct, utile pour une démonstration | question tapée au clavier | réponse affichée |

Aucun fichier ne fait plus d'une chose : c'est volontaire, pour que chaque étape du RAG soit isolée, testable et explicable séparément.

## Installation

Prérequis : Python 3.10+, une clé API [Anthropic](https://console.anthropic.com/) et une clé API [Voyage AI](https://dashboard.voyageai.com/).

```bash
# 1. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les clés API
cp .env.example .env
# puis éditer .env et renseigner ANTHROPIC_API_KEY et VOYAGE_API_KEY
```

## Comment tout tester, étape par étape

Le pipeline doit être exécuté **dans l'ordre** la première fois (chaque étape dépend du résultat de la précédente). Toutes les commandes se lancent depuis la racine du projet.

```bash
# Étape 1 : extraire le texte du PDF
python src/ingestion.py
# -> "160 pages extraites (160 avec du texte) -> data/processed/pages.json"

# Étape 2 : découper en passages
python src/chunking.py
# -> "289 passages -> data/processed/chunks.json (moyenne 302 mots/passage)"

# Étape 3 : indexer (appelle l'API Voyage AI, nécessite une clé valide)
python src/indexing.py
# -> "289 passages indexés -> data/processed/embeddings.npy (dimension 1024)"
# Note : si votre compte Voyage AI n'a pas encore de moyen de paiement enregistré,
# le débit est limité à 3 requêtes/minute ; le script le gère déjà (petits lots, pauses),
# mais ça prend alors ~10 minutes au lieu de quelques secondes.

# Étape 4 : tester la recherche seule (sans appel à Claude)
python src/retrieval.py
# -> affiche les passages les plus proches pour une question de démonstration

# Étape 5 : tester la génération complète (retrieval + Claude)
python src/generation.py
# -> affiche une réponse complète avec citation de page, sur 2 questions de démonstration

# Étape 6 : lancer l'évaluation chiffrée complète (20 questions)
python src/evaluate.py
# -> affiche le détail question par question, puis le score global

# Bonus : poser ses propres questions en direct (idéal pour une démo)
python src/ask.py
```

Pour poser une question précise sans passer par `ask.py` (par exemple pour vérifier un chiffre pendant une préparation) :

```bash
python -c "
from src.retrieval import load_index
from src.generation import answer_question

chunks, embeddings = load_index()
print(answer_question('Votre question ici ?', chunks, embeddings))
"
```

## Résultats de l'évaluation

20 questions construites à partir de faits réels vérifiés dans le document : **15 questions répondables** (dont la réponse est bien présente) et **5 questions pièges** (volontairement hors périmètre, pour vérifier que le système ne hallucine jamais).

| | Score |
|---|---|
| **Global** | **17/20 (85%)** |
| Questions répondables | 12/15 (80%) |
| Questions pièges (refus honnête attendu) | **5/5 (100%)** |

Le résultat le plus important n'est pas le 85% global, mais le **100% sur les questions pièges** : face à une question hors du périmètre du document (effectif du Groupe, cours de bourse en temps réel, dividende d'un exercice non couvert, question hors sujet type culture générale), le système n'a jamais inventé de réponse. C'est précisément le comportement qu'un système de production doit garantir avant d'être déployé dans un contexte bancaire.

Le détail complet (chaque question, la réponse obtenue, correcte ou non) est dans `data/eval/results.json`.

## Limites connues

Deux limites réelles ont été identifiées en testant, et documentées honnêtement plutôt que cachées :

**1. Les tableaux financiers à en-têtes multi-niveaux sont mal extraits.** La majorité des tableaux simples (compte de résultat, bilan) s'extraient parfaitement avec `pdfplumber` (libellé et valeurs sur la même ligne). Un type de tableau précis (ex. le tableau de variation des capitaux propres) a ses libellés de ligne et ses chiffres physiquement séparés dans la structure du PDF, et aucune des deux méthodes testées (`pypdf`, `pdfplumber`) ne les recolle correctement. Une question posée précisément sur ce tableau recevrait une réponse peu fiable.

**2. Une information factuelle courte noyée dans un texte qualitatif long peut être mal retrouvée.** Exemple concret rencontré pendant l'évaluation : une question sur le nom de l'Administrateur Directeur Général a échoué, alors que l'information est bien présente dans le document. Diagnostic fait : le passage contenant son nom mélange cette courte mention factuelle avec une longue citation qualitative du dirigeant (plusieurs phrases sur la stratégie du Groupe). Ce mélange dilue le sens du passage dans son vecteur d'embedding, qui devient alors peu détectable par une question factuelle courte et précise (ce passage était classé 30e sur l'ensemble du document, loin derrière le seuil de recherche). Augmenter le nombre de passages récupérés (`top_k`) n'aurait pas suffi à corriger ce cas, contrairement à un autre échec rencontré (passage classé 7e, corrigé en relevant `top_k` de 5 à 8).

## Pistes d'amélioration

Non implémentées ici, volontairement, pour tenir le scope initial du projet :

- **Chunking plus fin ou sémantique** : découper par idée/paragraphe plutôt que par nombre de mots fixe, pour éviter qu'un passage mélange plusieurs sujets (corrigerait la limite n°2)
- **Extraction de tableaux dédiée** (ex. détecter les tableaux et les reformater en paires libellé/valeur explicites avant indexation) pour la limite n°1
- **Recherche hybride** : combiner la recherche par embeddings avec une recherche par mot-clé classique (TF-IDF/BM25), pour rattraper les cas où un terme exact et rare compte plus que le sens général
- **Base vectorielle dédiée** (FAISS, Chroma, Pinecone) si le projet devait passer à l'échelle (plusieurs documents, mises à jour fréquentes) : pas nécessaire ici vu le volume (un seul document, 289 passages)

## Stack technique et justification des choix

| Outil | Rôle | Pourquoi ce choix |
|---|---|---|
| **Claude (API Anthropic)**, modèle `claude-haiku-4-5` | Génère la réponse finale à partir des passages récupérés | Tâche fermée (répondre à partir d'un contexte donné, pas de raisonnement complexe) : le modèle le moins cher qui remplit la tâche, plutôt que le plus gros par réflexe |
| **Voyage AI**, modèle `voyage-3.5` | Transforme chaque passage et chaque question en vecteur d'embedding | Claude n'a pas d'API d'embeddings propre ; Voyage AI est le fournisseur recommandé par Anthropic pour ce rôle. Tier gratuit de 200 millions de tokens, largement suffisant ici |
| **pdfplumber** | Extraction du texte des PDF | Remplace un premier essai avec `pypdf`, qui désorganisait les tableaux de chiffres (voir [Limites connues](#limites-connues)) |
| **numpy** | Calcul de similarité entre vecteurs | Pas besoin d'une vraie base de données vectorielle vu le volume (un seul document, quelques centaines de passages) |
| **python-dotenv** | Charge les clés API depuis `.env`, jamais commité | Bonne pratique de sécurité de base |

## Glossaire

- **RAG (Retrieval-Augmented Generation)** : récupérer des passages pertinents dans une base documentaire avant de les donner au LLM pour générer sa réponse, plutôt que de le laisser répondre uniquement à partir de ce qu'il a appris pendant son entraînement
- **Chunking** : découpage d'un document en passages ("chunks") de taille gérable
- **Embedding** : représentation numérique (vecteur) du sens d'un texte, permettant de comparer deux textes par similarité de sens plutôt que par correspondance exacte de mots
- **Retrieval** : étape de récupération des passages les plus pertinents pour une question donnée
- **Hallucination** : réponse inventée par le LLM, présentée avec la même assurance qu'une réponse correcte
- **Top-k** : nombre de passages les plus proches qu'on retient et qu'on transmet au LLM (ici, 8)

## Comment en parler en entretien

Quelques points à avoir en tête, pour pouvoir expliquer ce projet en profondeur et pas seulement le montrer :

- **Pourquoi un RAG et pas juste donner le PDF entier à Claude ?** Un document long dépasse souvent ce qu'on peut envoyer en une fois, et même quand c'est possible, noyer le modèle dans tout le texte dilue sa capacité à repérer l'info précise. Des passages ciblés, retrouvés par pertinence, sont plus fiables et moins coûteux en tokens.
- **Pourquoi des embeddings plutôt qu'une recherche par mot-clé (TF-IDF/BM25) ?** La recherche par mot-clé ne comprend que les mots exacts : "bénéfice net" ne matche pas "résultat net". Les embeddings capturent le sens, pas juste les mots. En pratique, les systèmes sérieux combinent souvent les deux (recherche hybride), un point à mentionner si on te demande d'aller plus loin.
- **Pourquoi Haiku et pas un modèle plus gros ?** Choisir le modèle le moins cher qui remplit la tâche est un vrai réflexe d'ingénierie, pas un raccourci. Le bon réflexe pour un recruteur technique : savoir justifier un choix de modèle par la nature de la tâche, pas par défaut.
- **Comment tu as mesuré la qualité, pas juste "ça marche" ?** 20 questions, dont 5 pièges volontairement sans réponse dans le document, pour vérifier l'honnêteté du système autant que son exactitude. 85% global, mais surtout 100% sur les pièges : zéro hallucination, le point le plus important dans un contexte bancaire.
- **Comment tu as diagnostiqué les échecs, plutôt que de deviner ?** Pour chaque question ratée, vérification du rang réel de la bonne page dans le classement complet de similarité (pas juste dans le top-k retourné). Ça a distingué deux causes différentes : un simple réglage insuffisant (`top_k` trop bas, corrigé) et un vrai problème de fond (dilution sémantique d'un passage, documenté comme limite plutôt que masqué).
- **Qu'est-ce que tu ferais différemment avec plus de temps ?** Un chunking plus intelligent (par idée plutôt que par nombre de mots fixe), une extraction dédiée des tableaux complexes, une recherche hybride. Savoir nommer les limites et leurs solutions, même non implémentées, montre une vraie compréhension du sujet, pas juste l'exécution d'un tutoriel.

## Licence

Projet pédagogique, à but de démonstration de compétences.
