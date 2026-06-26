# ResearchPilot

Agent IA de planification et d'analyse de projets technologiques, specialise pour le marche quebecois.

**Auteur** : Akrou Cyrille Dady  
**Formation** : Argentic AI Formation — Niveau 3 : Fondations Agentiques  
**Version** : 1.0.0

---

## Presentation

ResearchPilot transforme une idee de projet en documentation complete et professionnelle en quelques minutes. Il combine deux capacites : la planification de projet (vision, architecture, roadmap) et la recherche strategique (marche, finance, conformite reglementaire).

L'agent travaille de maniere autonome en utilisant 25 outils specialises, organises en 6 agents thematiques. Il produit jusqu'a 12 documents Markdown prets pour GitHub.

## Ce que ResearchPilot produit

A partir d'une simple description de projet, l'agent genere :

| Document | Contenu |
|---|---|
| `VISION.md` | Vision, mission, objectifs SMART, valeurs fondamentales |
| `PERSONAS.md` | Profils utilisateurs avec parcours d'achat et objections |
| `SPECIFICATIONS.md` | Fonctionnalites MoSCoW, definition du MVP |
| `ARCHITECTURE.md` | Stack technique, composants, securite, diagrammes Mermaid |
| `ROADMAP.md` | Phases de developpement, jalons, budget par phase |
| `TACHES.md` | Sprints, user stories, criteres de done |
| `ANALYSE_MARCHE.md` | TAM/SAM/SOM Quebec, concurrents, tendances secteur |
| `ANALYSE_FINANCIERE.md` | Couts dev (salaires Quebec), revenus SaaS, 3 scenarios financiers |
| `ANALYSE_SWOT.md` | Forces, faiblesses, opportunites, menaces, interactions TOWS |
| `STRATEGIE_LANCEMENT.md` | Go-to-Market Quebec, canaux, plan 90 jours, KPIs |
| `SCORE_VIABILITE.md` | Score 0-100 sur 6 dimensions, verdict final, recommandations |
| `RAPPORT_COMPLET.md` | Synthese de tous les documents precedents |

## Architecture de l'agent

ResearchPilot utilise le **pattern ReAct** (Reasoning + Acting) : avant chaque action, l'agent ecrit son raisonnement, puis execute l'outil approprie. La boucle continue jusqu'a ce que toutes les analyses soient completes.

```
main.py
  └── agent.py  (boucle agentique principale — ReAct pattern)
        ├── tools/recherche.py     (4 outils — recherche web et besoins)
        ├── tools/planification.py (7 outils — vision, architecture, Mermaid)
        ├── tools/fichiers.py      (3 outils — lecture/ecriture fichiers)
        ├── tools/marche.py        (5 outils — TAM/SAM/SOM Quebec)
        ├── tools/finance.py       (5 outils — couts, revenus, scenarios)
        └── tools/strategie.py     (7 outils — SWOT, GTM, Loi 25, viabilite)
```

Fichiers de support :

```
config.py   — Constantes (modeles, salaires Quebec, couts cloud)
prompts.py  — System prompts des 7 agents specialises
state.py    — Persistance JSON (reprise de session)
ui.py       — Interface terminal avec Rich (tableaux, panneaux, couleurs)
```

## Concepts implementes

Ce projet est un exemple de reference pour les concepts suivants :

**Boucle agentique** : Le LLM appelle des outils en boucle jusqu'a completion. Le code inspecte `finish_reason` : `"tool_calls"` pour executer un outil, `"stop"` pour terminer.

**Function Calling** : Chaque outil est defini en JSON Schema (format OpenAI). Le LLM choisit quel outil appeler et avec quels arguments — il ne genere pas du code Python.

**ReAct Pattern** : Le contenu textuel du message de l'agent (avant les tool calls) est son raisonnement. Cela rend le processus transparent et debuggable.

**Human-in-the-Loop** : Avant d'ecrire un fichier, l'agent affiche un apercu et demande confirmation. L'utilisateur reste en controle des actions irreversibles.

**Calcul Python vs LLM** : Les formules financieres (break-even, scenarios, LTV/CAC) sont calculees en Python, pas par le LLM. Cela garantit la precision mathematique.

**Memoire externe** : L'etat du projet est persiste en JSON apres chaque serie d'outils. La session peut etre interrompue et reprise.

**Tavily fallback** : Si la cle Tavily est absente, les recherches web sont simulees par le LLM. Le programme fonctionne dans les deux cas.

## Prerequis

- Python 3.11 ou superieur
- Compte OpenAI avec credits disponibles
- Compte Tavily (optionnel, gratuit sur tavily.com)

## Installation

**1. Cloner le depot et entrer dans le dossier**

```bash
git clone <url-du-depot>
cd ResearchPilot
```

**2. Creer un environnement virtuel**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
```

**3. Installer les dependances**

```bash
pip install -r requirements.txt
```

**4. Configurer les cles API**

```bash
cp .env.example .env
```

Edite `.env` et ajoute tes cles :

```env
OPENAI_API_KEY=sk-proj-ta-cle-ici
TAVILY_API_KEY=tvly-ta-cle-ici   # optionnel
```

**5. Lancer ResearchPilot**

```bash
python main.py
```

## Utilisation

Au demarrage, ResearchPilot te demande de decrire ton projet. Plus la description est precise, meilleure est l'analyse. Exemple :

> "Une application SaaS pour les comptables independants du Quebec qui veulent automatiser leurs rapports fiscaux. Prix cible : 79$/mois. Le marche est sature de solutions en anglais — on vise les francophones qui veulent une interface en francais et une conformite aux regles CPA Quebec."

L'agent travaille ensuite de maniere autonome. Pour chaque fichier qu'il s'apprete a ecrire, il affiche un apercu et attend ta confirmation.

Les fichiers sont sauvegardes dans `projets_generes/<nom-projet>/`. L'etat de la session est sauvegarde dans `etat_projets/<nom-projet>.json` — si tu interromps avec Ctrl+C, tu peux reprendre au prochain lancement.

## Specificites Quebec

Toutes les analyses sont adaptees au contexte quebecois :

- Valeurs financieres en dollars canadiens (CAD)
- Salaires bases sur les grilles 2024-2025 du marche quebecois
- Analyse de conformite Loi 25 (equivalent RGPD Quebec, en vigueur depuis 2024)
- Programmes d'aide identifies : Investissement Quebec, PARI-CNRC, RS&DE, Futurpreneur
- Canaux marketing adaptes au marche francophone (LinkedIn FR, groupes Facebook PME Quebec)
- TAM/SAM/SOM calcules sur la population quebecoise (~8.8M habitants)

## Structure des fichiers generes

```
projets_generes/
└── mon_projet_saas/
    ├── VISION.md
    ├── PERSONAS.md
    ├── SPECIFICATIONS.md
    ├── ARCHITECTURE.md
    ├── ROADMAP.md
    ├── TACHES.md
    ├── ANALYSE_MARCHE.md
    ├── ANALYSE_FINANCIERE.md
    ├── ANALYSE_SWOT.md
    ├── STRATEGIE_LANCEMENT.md
    ├── SCORE_VIABILITE.md
    └── RAPPORT_COMPLET.md
```

## Dependances

```
openai          — Acces aux modeles GPT-4o et function calling
python-dotenv   — Chargement des variables d'environnement depuis .env
rich            — Interface terminal avec couleurs, tableaux, panneaux
tavily-python   — Recherche web optimisee pour les LLMs (optionnel)
```

## Couts estimatifs

Chaque analyse complete utilise environ 80 000 a 120 000 tokens (input + output) avec GPT-4o-mini. Au tarif de janvier 2025, cela represente environ **0.05 a 0.10 USD par projet complet**.

## Limitations connues

- Les donnees de marche sont des estimations LLM, pas des donnees de marche verifiees. Utiliser comme point de depart, pas comme source unique.
- Les projections financieres reposent sur des hypotheses de taux de croissance et de churn. Valider avec des donnees reelles.
- La conformite Loi 25 analysee est indicative. Consulter un juriste pour une analyse juridique complete.
- Le score de viabilite est un outil d'aide a la decision, pas une garantie de succes.

## Contribution

Ce projet est realise dans le cadre d'une formation. Les contributions educatives sont bienvenues via les issues GitHub.

---

**Akrou Cyrille Dady** — Formation Argentic AI — Niveau 3 Fondations Agentiques
