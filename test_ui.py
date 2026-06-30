# test_ui.py — A supprimer apres le test
from ui import (
    console,
    afficher_bienvenue,
    afficher_iteration,
    afficher_appel_outil,
    afficher_resultat_outil,
    afficher_succes,
    afficher_info,
    afficher_erreur,
    afficher_avertissement,
    afficher_separateur
)

# Test 1 : Bienvenue
afficher_bienvenue()

# Test 2 : Iterations
afficher_separateur("Test des iterations")
for i in range(1, 6):
    afficher_iteration(i, 60, f"Simulation iteration {i}")

# Test 3 : Appel d'outil
afficher_separateur("Test appel outil")
afficher_appel_outil(
    "analyser_marche_quebec",
    {
        "description_projet": "SaaS pour restaurateurs",
        "secteur": "restauration",
        "public_cible": "restaurants independants"
    }
)

# Test 4 : Resultat
afficher_resultat_outil(
    "analyser_marche_quebec",
    {"tam": 500000000, "sam": 50000000, "som": 5000000, "potentiel": "eleve"}
)

# Test 5 : Messages
afficher_separateur("Messages")
afficher_succes("Fichier VISION.md ecrit avec succes (45 lignes)")
afficher_info("Tavily non configure, mode LLM seul active")
afficher_avertissement("Budget marketing non specifie, 500$/mois utilise par defaut")
afficher_erreur("Cle API invalide", "La cle doit commencer par 'sk-'")