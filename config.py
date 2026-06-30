import os
from pathlib import Path

REGION = os.getenv("REGION", "Quebec, Canada")

BASE_DIR = Path(__file__).parent

DOSSIER_PROJETS = BASE_DIR / "projets_generes"

DOSSIER_ETAT = BASE_DIR / "etat_projets"

DOSSIER_PROJETS.mkdir(exist_ok=True)
DOSSIER_ETAT.mkdir(exist_ok=True)

MODELE_PRINCIPAL = "gpt-4o-mini"
MODELE_SECONDAIRE = "gpt-4o-mini"
MODELE_MERMAID = "gpt-4o-mini"

TEMPERATURE_AGENT = 0.3
TEMPERATURE_GENERATION = 0.6
TEMPERATURE_ANALYSE = 0.3
TEMPERATURE_MERMAID = 0.2

MAX_ITERATIONS = 60

MAX_TOKENS_GENERATION = 4000
MAX_TOKENS_COURT = 1000