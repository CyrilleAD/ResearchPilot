import json
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from config import MODELE_PRINCIPAL, TEMPERATURE_AGENT, MAX_ITERATIONS
from prompts import SYSTEM_PROMPT_AGENT
from state import sauvegarder_etat, enregistrer_analyse, enregistrer_document
from ui import (
    afficher_iteration,
    afficher_pensee_agent,
    afficher_appel_outil,
    afficher_resultat_outil,
    afficher_separateur,
    afficher_erreur,
    afficher_succes,
    console
)

# Importer tous les outils
from tools.recherche import (
    rechercher_informations,
    analyser_besoins_utilisateurs,
    etudier_solutions_existantes,
    identifier_technologies,
    rechercher_donnees_marche
)
from tools.planification import (
    definir_vision_projet,
    creer_personas,
    planifier_fonctionnalites,
    concevoir_architecture,
    planifier_roadmap,
    decomposer_en_taches,
    generer_diagrammes_mermaid
)
from tools.fichiers import (
    ecrire_fichier_markdown,
    lire_fichier,
    lister_fichiers_projet
)
from tools.marche import (
    analyser_marche_quebec,
    analyser_concurrents_quebec,
    identifier_tendances_secteur,
    evaluer_positionnement,
    generer_rapport_marche
)
from tools.finance import (
    estimer_couts_developpement,
    modeliser_revenus,
    calculer_point_equilibre,
    projeter_scenarios_financiers,
    generer_rapport_financier
)
from tools.strategie import (
    generer_swot,
    concevoir_gtm_quebec,
    analyser_risques_reglementaires_quebec,
    calculer_score_viabilite,
    generer_rapport_swot,
    generer_rapport_gtm,
    generer_rapport_viabilite
)

load_dotenv()

# Documents Markdown que l'agent DOIT avoir ecrits avant de pouvoir terminer.
# Liste alignee sur le README (section "Documents generes").
DOCUMENTS_OBLIGATOIRES = [
    "VISION.md",
    "ANALYSE_MARCHE.md",
    "ANALYSE_FINANCIERE.md",
    "ANALYSE_SWOT.md",
    "STRATEGIE_LANCEMENT.md",
    "SCORE_VIABILITE.md",
]






# Ce dictionnaire est le "dispatcher" : il mappe les noms (strings) vers les fonctions.
# Quand le LLM dit "appelle analyser_marche_quebec", on cherche ce nom ici
# et on appelle la vraie fonction Python.
FONCTIONS_DISPONIBLES = {
    # Recherche
    "rechercher_informations": rechercher_informations,
    "analyser_besoins_utilisateurs": analyser_besoins_utilisateurs,
    "etudier_solutions_existantes": etudier_solutions_existantes,
    "identifier_technologies": identifier_technologies,
    "rechercher_donnees_marche": rechercher_donnees_marche,
    
    # Planification
    "definir_vision_projet": definir_vision_projet,
    "creer_personas": creer_personas,
    "planifier_fonctionnalites": planifier_fonctionnalites,
    "concevoir_architecture": concevoir_architecture,
    "planifier_roadmap": planifier_roadmap,
    "decomposer_en_taches": decomposer_en_taches,
    "generer_diagrammes_mermaid": generer_diagrammes_mermaid,
    
    # Fichiers
    "ecrire_fichier_markdown": ecrire_fichier_markdown,
    "lire_fichier": lire_fichier,
    "lister_fichiers_projet": lister_fichiers_projet,
    
    # Marche Quebec
    "analyser_marche_quebec": analyser_marche_quebec,
    "analyser_concurrents_quebec": analyser_concurrents_quebec,
    "identifier_tendances_secteur": identifier_tendances_secteur,
    "evaluer_positionnement": evaluer_positionnement,
    "generer_rapport_marche": generer_rapport_marche,
    
    # Finance
    "estimer_couts_developpement": estimer_couts_developpement,
    "modeliser_revenus": modeliser_revenus,
    "calculer_point_equilibre": calculer_point_equilibre,
    "projeter_scenarios_financiers": projeter_scenarios_financiers,
    "generer_rapport_financier": generer_rapport_financier,
    
    # Strategie
    "generer_swot": generer_swot,
    "concevoir_gtm_quebec": concevoir_gtm_quebec,
    "analyser_risques_reglementaires_quebec": analyser_risques_reglementaires_quebec,
    "calculer_score_viabilite": calculer_score_viabilite,
    "generer_rapport_swot": generer_rapport_swot,
    "generer_rapport_gtm": generer_rapport_gtm,
    "generer_rapport_viabilite": generer_rapport_viabilite,
}




def construire_liste_outils() -> list:
    """
    Retourne la liste de tous les outils au format JSON Schema OpenAI.
    
    Cette liste est envoyee avec CHAQUE appel LLM.
    Attention : plus la liste est longue, plus chaque appel coute cher.
    25 outils represente environ 2000 tokens supplementaires par appel.
    """
    return [
        # ---- RECHERCHE ----
        {
            "type": "function",
            "function": {
                "name": "rechercher_informations",
                "description": "Recherche des informations sur un sujet. Appele en PREMIER pour tout nouveau projet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requete": {"type": "string", "description": "La question a rechercher"},
                        "domaine": {"type": "string", "description": "Domaine specifique (optionnel)"},
                        "profondeur": {"type": "string", "enum": ["basique", "avancee"]}
                    },
                    "required": ["requete"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyser_besoins_utilisateurs",
                "description": "Cree des personas et identifie les pain points. Apres la recherche initiale.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "public_cible": {"type": "string"},
                        "probleme_principal": {"type": "string"}
                    },
                    "required": ["description_projet", "public_cible", "probleme_principal"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "etudier_solutions_existantes",
                "description": "Analyse les alternatives sur le marche. Avant la planification.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "probleme_a_resoudre": {"type": "string"},
                        "secteur": {"type": "string"},
                        "public_cible": {"type": "string"}
                    },
                    "required": ["probleme_a_resoudre", "secteur", "public_cible"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identifier_technologies",
                "description": "Recommande le stack technologique adapte.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_projet": {"type": "string"},
                        "contraintes": {"type": "array", "items": {"type": "string"}},
                        "competences_equipe": {"type": "array", "items": {"type": "string"}},
                        "budget_infra_mensuel_cad": {"type": "number"}
                    },
                    "required": ["type_projet", "contraintes", "competences_equipe"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rechercher_donnees_marche",
                "description": "Fetche via Tavily des donnees marche actuelles : salaires devs Quebec, couts hebergement cloud, programmes aide startup, prix logiciels similaires, taux freelance. OBLIGATOIRE avant estimer_couts_developpement.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_donnee": {
                            "type": "string",
                            "enum": ["salaires_developpeurs", "couts_hebergement", "programmes_aide_startup", "prix_logiciels_similaires", "taux_freelance"],
                            "description": "Type de donnee a rechercher"
                        },
                        "region": {"type": "string", "description": "Region geographique (defaut: Quebec, Canada)"},
                        "contexte": {"type": "string", "description": "Contexte supplementaire pour affiner la recherche"}
                    },
                    "required": ["type_donnee"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "definir_vision_projet",
                "description": "Definit vision, mission, objectifs SMART.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "public_cible": {"type": "string"},
                        "probleme_resolu": {"type": "string"},
                        "secteur": {"type": "string"}
                    },
                    "required": ["description_projet", "public_cible", "probleme_resolu"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "creer_personas",
                "description": "Cree les profils utilisateurs detailles avec parcours d'achat.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "analyse_besoins": {"type": "object"}
                    },
                    "required": ["description_projet", "analyse_besoins"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "planifier_fonctionnalites",
                "description": "Classe les fonctionnalites MoSCoW et definit le MVP.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "analyse_besoins": {"type": "object"},
                        "solutions_existantes": {"type": "object"}
                    },
                    "required": ["description_projet", "analyse_besoins", "solutions_existantes"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "concevoir_architecture",
                "description": "Architecture technique : composants, flux, securite.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "fonctionnalites": {"type": "object"},
                        "technologies": {"type": "object"}
                    },
                    "required": ["description_projet", "fonctionnalites", "technologies"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "planifier_roadmap",
                "description": "Planning de developpement en phases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "fonctionnalites": {"type": "object"},
                        "couts_dev": {"type": "object"}
                    },
                    "required": ["description_projet", "fonctionnalites", "couts_dev"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "decomposer_en_taches",
                "description": "Taches de developpement en sprints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fonctionnalites_mvp": {"type": "array", "items": {"type": "object"}},
                        "architecture": {"type": "object"}
                    },
                    "required": ["fonctionnalites_mvp", "architecture"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_diagrammes_mermaid",
                "description": "Genere les diagrammes Mermaid (architecture, sequence, gantt). Passer les 3 arguments : architecture = resultat concevoir_architecture, flux_donnees = architecture['flux_donnees_principal'], roadmap = resultat planifier_roadmap.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "architecture": {"type": "object", "description": "Resultat de concevoir_architecture"},
                        "flux_donnees": {"type": "array", "items": {"type": "object"}, "description": "architecture['flux_donnees_principal'] ou []"},
                        "roadmap": {"type": "object", "description": "Resultat de planifier_roadmap"}
                    },
                    "required": ["architecture", "flux_donnees", "roadmap"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ecrire_fichier_markdown",
                "description": "Ecrit directement un fichier Markdown sur le disque, sans demander de confirmation a personne (l'agent est autonome). A appeler immediatement pour chaque document, jamais apres avoir demande la permission a l'utilisateur.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nom_fichier": {"type": "string", "description": "Ex: VISION.md"},
                        "contenu": {"type": "string"},
                        "slug_projet": {"type": "string"},
                        "demander_confirmation": {"type": "boolean", "default": False, "description": "Laisser False — l'agent est autonome, personne ne repondra a une demande de confirmation"}
                    },
                    "required": ["nom_fichier", "contenu", "slug_projet"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lire_fichier",
                "description": "Lit un fichier deja genere.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nom_fichier": {"type": "string"},
                        "slug_projet": {"type": "string"}
                    },
                    "required": ["nom_fichier", "slug_projet"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lister_fichiers_projet",
                "description": "Liste tous les fichiers generes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slug_projet": {"type": "string"}
                    },
                    "required": ["slug_projet"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyser_marche_quebec",
                "description": "Analyse TAM/SAM/SOM Quebec. Avant les analyses financieres.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "secteur": {"type": "string"},
                        "public_cible": {"type": "string"},
                        "modele_revenu": {"type": "string"}
                    },
                    "required": ["description_projet", "secteur", "public_cible"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyser_concurrents_quebec",
                "description": "Analyse des concurrents Quebec.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "secteur": {"type": "string"},
                        "public_cible": {"type": "string"}
                    },
                    "required": ["description_projet", "secteur", "public_cible"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "identifier_tendances_secteur",
                "description": "Tendances technologiques et marche du secteur.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "secteur": {"type": "string"},
                        "horizon_annees": {"type": "integer", "default": 3}
                    },
                    "required": ["secteur"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "evaluer_positionnement",
                "description": "Positionnement concurrentiel et proposition de valeur.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "analyse_marche": {"type": "object"},
                        "analyse_concurrents": {"type": "object"},
                        "prix_mensuel_cad": {"type": "number"}
                    },
                    "required": ["description_projet", "analyse_marche", "analyse_concurrents"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_rapport_marche",
                "description": "Genere ANALYSE_MARCHE.md. Args exacts uniquement : nom_projet, analyse_marche, analyse_concurrents, tendances, positionnement — pas d'autres champs comme potentiel_general (deja inclus dans analyse_marche).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nom_projet": {"type": "string"},
                        "analyse_marche": {"type": "object", "description": "Resultat de analyser_marche_quebec"},
                        "analyse_concurrents": {"type": "object", "description": "Resultat de analyser_concurrents_quebec"},
                        "tendances": {"type": "object", "description": "Resultat de identifier_tendances_secteur"},
                        "positionnement": {"type": "object", "description": "Resultat de evaluer_positionnement"}
                    },
                    "required": ["nom_projet", "analyse_marche", "analyse_concurrents"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "estimer_couts_developpement",
                "description": "Estime les couts de developpement avec des taux horaires reels fetches via rechercher_donnees_marche. Appeler rechercher_donnees_marche('salaires_developpeurs') AVANT cet outil pour obtenir les taux.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nb_semaines_estimees": {"type": "integer", "description": "Duree totale du projet en semaines"},
                        "profil_developpeur": {"type": "string", "description": "Ex: 'dev senior Python IA'"},
                        "taux_horaire_min_cad": {"type": "number", "description": "Taux plancher en CAD, fetch via rechercher_donnees_marche"},
                        "taux_horaire_moyen_cad": {"type": "number", "description": "Taux moyen en CAD, fetch via rechercher_donnees_marche"},
                        "taux_horaire_max_cad": {"type": "number", "description": "Taux plafond en CAD, fetch via rechercher_donnees_marche"},
                        "infra_mensuel_cad": {"type": "number", "description": "Couts infra cloud mensuels en CAD (defaut 55)"},
                        "heures_par_semaine": {"type": "integer", "description": "Heures de travail par semaine (defaut 30)"},
                        "couts_outils_mensuels_cad": {"type": "number", "description": "Licences et outils mensuels en CAD (defaut 100)"}
                    },
                    "required": ["nb_semaines_estimees", "profil_developpeur", "taux_horaire_min_cad", "taux_horaire_moyen_cad", "taux_horaire_max_cad"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "modeliser_revenus",
                "description": "Metriques SaaS : MRR, ARR, CAC, LTV.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prix_mensuel_cad": {"type": "number"},
                        "clients_initiaux": {"type": "integer"},
                        "taux_croissance_mensuel_pct": {"type": "number"},
                        "taux_churn_mensuel_pct": {"type": "number"},
                        "couts_acquisition_cad": {"type": "number"},
                        "nb_mois": {"type": "integer", "default": 24}
                    },
                    "required": ["prix_mensuel_cad", "clients_initiaux", "taux_croissance_mensuel_pct", "taux_churn_mensuel_pct", "couts_acquisition_cad"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculer_point_equilibre",
                "description": "Break-even calcule en Python.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "couts_fixes_mensuels_cad": {"type": "number"},
                        "prix_unitaire_cad": {"type": "number"},
                        "cout_variable_par_client_cad": {"type": "number", "default": 0}
                    },
                    "required": ["couts_fixes_mensuels_cad", "prix_unitaire_cad"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "projeter_scenarios_financiers",
                "description": "3 scenarios (optimiste/realiste/pessimiste) sur 24 mois.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prix_mensuel_cad": {"type": "number"},
                        "clients_initiaux": {"type": "integer"},
                        "couts_fixes_mensuels_cad": {"type": "number"},
                        "cout_variable_par_client_cad": {"type": "number", "default": 0},
                        "nb_mois": {"type": "integer", "default": 24}
                    },
                    "required": ["prix_mensuel_cad", "clients_initiaux", "couts_fixes_mensuels_cad"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_rapport_financier",
                "description": "Genere ANALYSE_FINANCIERE.md. OBLIGATOIRE : passer scenarios = resultat complet de projeter_scenarios_financiers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nom_projet": {"type": "string"},
                        "couts_dev": {"type": "object", "description": "Resultat de estimer_couts_developpement"},
                        "revenus": {"type": "object", "description": "Resultat de modeliser_revenus"},
                        "break_even": {"type": "object", "description": "Resultat de calculer_point_equilibre"},
                        "scenarios": {"type": "object", "description": "Resultat de projeter_scenarios_financiers — OBLIGATOIRE"}
                    },
                    "required": ["nom_projet", "couts_dev", "revenus", "break_even", "scenarios"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_swot",
                "description": "Calcule l'ANALYSE SWOT (dict de donnees, pas le document Markdown — pour le document, utiliser ensuite generer_rapport_swot avec ce resultat). Apres toutes les analyses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "analyse_marche": {"type": "object"},
                        "analyse_concurrents": {"type": "object"},
                        "couts_dev": {"type": "object"}
                    },
                    "required": ["description_projet", "analyse_marche", "analyse_concurrents", "couts_dev"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "concevoir_gtm_quebec",
                "description": "Go-to-Market Quebec avec plan 90 jours.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description_projet": {"type": "string"},
                        "public_cible": {"type": "string"},
                        "prix_mensuel_cad": {"type": "number"},
                        "positionnement": {"type": "object"},
                        "budget_marketing_mensuel_cad": {"type": "number", "default": 500}
                    },
                    "required": ["description_projet", "public_cible", "prix_mensuel_cad", "positionnement"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyser_risques_reglementaires_quebec",
                "description": "Conformite Loi 25, LPRPDE, regulations sectorielles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_projet": {"type": "string"},
                        "donnees_collectees": {"type": "array", "items": {"type": "string"}},
                        "secteur": {"type": "string"}
                    },
                    "required": ["type_projet", "donnees_collectees", "secteur"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculer_score_viabilite",
                "description": "Score viabilite 0-100. Appele EN DERNIER apres toutes les analyses (generer_swot et analyser_risques_reglementaires_quebec doivent avoir ete appeles avant pour fournir swot et risques_reglementaires).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "analyse_marche": {"type": "object"},
                        "analyse_concurrents": {"type": "object"},
                        "couts_dev": {"type": "object"},
                        "scenarios": {"type": "object", "description": "Resultat de projeter_scenarios_financiers"},
                        "swot": {"type": "object", "description": "Resultat de generer_swot"},
                        "risques_reglementaires": {"type": "object", "description": "Resultat de analyser_risques_reglementaires_quebec"}
                    },
                    "required": ["description", "analyse_marche", "analyse_concurrents", "couts_dev", "scenarios", "swot", "risques_reglementaires"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_rapport_swot",
                "description": "Genere ANALYSE_SWOT.md (document Markdown) a partir du dict swot deja produit par generer_swot. SEULEMENT 2 args : swot (le dict retourne par generer_swot, PAS description_projet/analyse_marche/analyse_concurrents/couts_dev) et nom_projet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "swot": {"type": "object", "description": "Le dict complet retourne par generer_swot (forces, faiblesses, opportunites, menaces)"},
                        "nom_projet": {"type": "string"}
                    },
                    "required": ["swot", "nom_projet"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_rapport_gtm",
                "description": "Genere STRATEGIE_LANCEMENT.md.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gtm": {"type": "object"},
                        "nom_projet": {"type": "string"},
                        "budget_mensuel_cad": {"type": "number", "default": 500}
                    },
                    "required": ["gtm", "nom_projet"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generer_rapport_viabilite",
                "description": "Genere SCORE_VIABILITE.md avec le verdict final. score_data = resultat de calculer_score_viabilite, nom_projet = nom du projet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "score_data": {"type": "object", "description": "Resultat de calculer_score_viabilite"},
                        "nom_projet": {"type": "string", "description": "Nom du projet (ex: ImmoVision AI Quebec)"}
                    },
                    "required": ["score_data", "nom_projet"]
                }
            }
        }
    ]











def executer_outil(nom_outil: str, arguments: dict) -> str:
    """
    Selectionne et execute la bonne fonction Python.
    
    1. Cherche le nom dans FONCTIONS_DISPONIBLES
    2. Appelle la fonction avec les arguments
    3. Serialise le resultat en JSON string
    4. Retourne le JSON string au LLM
    
    Retourne TOUJOURS une string (jamais None, jamais un dict).
    Le LLM ne comprend que du texte.
    """
    afficher_appel_outil(nom_outil, arguments)
    
    fonction = FONCTIONS_DISPONIBLES.get(nom_outil)
    if not fonction:
        erreur = {"erreur": f"Outil inconnu : {nom_outil}"}
        afficher_erreur(f"Outil inconnu : {nom_outil}")
        return json.dumps(erreur, ensure_ascii=False)
    
    try:
        resultat = fonction(**arguments)
        # **arguments "depaquette" le dictionnaire en arguments nommes
        # Ex: {"nom": "test", "age": 25} devient fonction(nom="test", age=25)
        
        afficher_resultat_outil(nom_outil, resultat, succes=True)
        # Les fonctions generer_rapport_* retournent des strings Markdown.
        # Si on fait json.dumps(string), le LLM recoit "\"# Titre\\nSection\""
        # (avec guillemets et \n escapes visibles comme texte), puis quand il
        # copie ce contenu dans ecrire_fichier_markdown il re-echappe les \n
        # -> fichiers avec \n litteraux au lieu de vrais sauts de ligne.
        # Solution : retourner la string directement, sans double-encodage.
        if isinstance(resultat, str):
            return resultat
        return json.dumps(resultat, ensure_ascii=False, default=str)
    
    except TypeError as e:
        # TypeError = mauvais arguments (nom ou type incorrect)
        erreur = {"erreur": f"Mauvais arguments pour {nom_outil}", "detail": str(e)}
        afficher_erreur(f"Erreur arguments {nom_outil}", str(e))
        return json.dumps(erreur, ensure_ascii=False)
    
    except Exception as e:
        erreur = {"erreur": f"Erreur dans {nom_outil}", "detail": str(e)}
        afficher_erreur(f"Erreur execution {nom_outil}", str(e))
        return json.dumps(erreur, ensure_ascii=False)
    




def executer_agent(description_projet: str, etat: dict) -> dict:
    """
    Lance et gere la boucle agentique.
    
    C'est ici que tout se passe. Lis chaque commentaire.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    outils = construire_liste_outils()
    slug = etat.get("slug", "projet")
    
    # Message initial : la mission de l'agent
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_AGENT
        },
        {
            "role": "user",
            "content": f"""Analyse et planifie ce projet de maniere complete.

DESCRIPTION DU PROJET :
{description_projet}

SLUG DU PROJET : {slug}

INSTRUCTIONS :
1. Commence par rechercher des informations sur le domaine
2. Analyse les besoins utilisateurs et les solutions existantes
3. Fais l'analyse de marche Quebec (TAM/SAM/SOM)
4. Estime les couts et projete les scenarios financiers
5. Fais l'analyse SWOT et strategique
6. Genere les diagrammes Mermaid
7. Ecris tous les fichiers Markdown (en demandant confirmation)
8. Calcule le score de viabilite final en dernier

Commence par la recherche d'informations sur ce domaine."""
        }
    ]
    
    afficher_separateur("Demarrage de l'agent ResearchPilot")
    console.print(f"  [cyan]Projet[/cyan] : {description_projet[:80]}")
    console.print(f"  [cyan]Slug[/cyan]   : {slug}")
    afficher_separateur()

    relances_documents = 0
    MAX_RELANCES_DOCUMENTS = 3

    # ============================================================
    # LA BOUCLE PRINCIPALE
    # ============================================================
    for iteration in range(1, MAX_ITERATIONS + 1):
        afficher_iteration(iteration, MAX_ITERATIONS)
        
        # APPEL LLM
        reponse = client.chat.completions.create(
            model=MODELE_PRINCIPAL,
            messages=messages,
            tools=outils,
            tool_choice="auto",  # Le LLM decide quand utiliser un outil
            temperature=TEMPERATURE_AGENT,
            max_tokens=4096
        )
        
        message_agent = reponse.choices[0].message
        raison_arret = reponse.choices[0].finish_reason
        
        # Afficher le raisonnement si present
        if message_agent.content:
            afficher_pensee_agent(message_agent.content)
        
        # =======================================================
        # CAS 1 : finish_reason == "stop" -> L'agent a fini
        # =======================================================
        if raison_arret == "stop":
            documents_ecrits = {
                Path(d.get("fichier", "")).name for d in etat.get("documents_generes", [])
            }
            manquants = [doc for doc in DOCUMENTS_OBLIGATOIRES if doc not in documents_ecrits]

            if manquants and relances_documents < MAX_RELANCES_DOCUMENTS:
                relances_documents += 1
                if message_agent.content:
                    messages.append({"role": "assistant", "content": message_agent.content})
                messages.append({
                    "role": "user",
                    "content": (
                        "Tu n'as pas encore ecrit tous les documents obligatoires. "
                        f"Documents manquants : {', '.join(manquants)}. "
                        "Appelle ecrire_fichier_markdown pour chacun maintenant, sans poser de question — "
                        "personne ne repondra. N'attends pas de confirmation."
                    )
                })
                continue

            afficher_separateur("Agent termine")
            afficher_succes(f"Mission complete en {iteration} iterations")

            if message_agent.content:
                console.print(f"\n[bold green]Conclusion :[/bold green]\n{message_agent.content}\n")

            etat["statut"] = "complete"
            sauvegarder_etat(etat)
            break
        
        # =======================================================
        # CAS 2 : finish_reason == "tool_calls" -> L'agent veut utiliser un outil
        # =======================================================
        elif raison_arret == "tool_calls":
            # IMPORTANT : ajouter le message de l'agent AU CONTEXTE
            # Ce message contient les tool_calls — il est necessaire pour la coherence
            messages.append(message_agent)
            
            # Executer chaque outil demande (peut en demander plusieurs)
            for appel_outil in message_agent.tool_calls:
                nom = appel_outil.function.name
                arguments_str = appel_outil.function.arguments
                tool_call_id = appel_outil.id  # ID unique de cet appel
                
                # Parser les arguments (le LLM retourne du JSON en string)
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                # Si le LLM oublie slug_projet pour ecrire_fichier_markdown, l'injecter
                if nom == "ecrire_fichier_markdown" and "slug_projet" not in arguments:
                    arguments["slug_projet"] = slug

                # Executer l'outil
                resultat = executer_outil(nom, arguments)
                
                # AJOUTER LE RESULTAT AU CONTEXTE
                # CRITIQUE : tool_call_id doit matcher l'id de l'appel
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": resultat
                })
                
                # Mettre a jour l'etat avec les resultats
                _mettre_a_jour_etat(etat, nom, arguments, resultat)
            
            # Sauvegarder apres chaque serie d'outils
            sauvegarder_etat(etat)
        
        # =======================================================
        # CAS 3 : finish_reason == "length" -> reponse tronquee
        # =======================================================
        elif raison_arret == "length":
            messages.append(message_agent)
            if message_agent.tool_calls:
                # Le LLM a ete coupe en plein milieu de tool_calls.
                # On doit repondre a chaque tool_call_id sinon l'API retourne 400.
                for appel_outil in message_agent.tool_calls:
                    nom = appel_outil.function.name
                    try:
                        arguments = json.loads(appel_outil.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    if nom == "ecrire_fichier_markdown" and "slug_projet" not in arguments:
                        arguments["slug_projet"] = slug
                    resultat = executer_outil(nom, arguments)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": appel_outil.id,
                        "content": resultat
                    })
                    _mettre_a_jour_etat(etat, nom, arguments, resultat)
                sauvegarder_etat(etat)
            else:
                messages.append({
                    "role": "user",
                    "content": "Ta reponse a ete coupee. Continue exactement ou tu t'es arrete."
                })

        # =======================================================
        # CAS 4 : raison inconnue -> Securite
        # =======================================================
        else:
            afficher_erreur(f"Raison d'arret inconnue : {raison_arret}")
            break
    
    else:
        # La boucle for s'est terminee sans break = MAX_ITERATIONS atteint
        afficher_erreur(
            f"Limite de {MAX_ITERATIONS} iterations atteinte",
            "Le projet partiel est sauvegarde. Relance pour continuer."
        )
        etat["statut"] = "incomplet"
        sauvegarder_etat(etat)
    
    return etat


def _mettre_a_jour_etat(etat: dict, nom: str, args: dict, resultat_json: str):
    """Met a jour l'etat apres l'execution d'un outil."""
    try:
        resultat = json.loads(resultat_json)
    except (json.JSONDecodeError, TypeError):
        return
    
    # Correspondance outil -> cle dans etat["analyses"]
    correspondances = {
        "analyser_marche_quebec": "marche",
        "analyser_concurrents_quebec": "concurrents",
        "identifier_tendances_secteur": "tendances",
        "evaluer_positionnement": "positionnement",
        "estimer_couts_developpement": "couts_dev",
        "modeliser_revenus": "revenus",
        "calculer_point_equilibre": "break_even",
        "projeter_scenarios_financiers": "scenarios_financiers",
        "generer_swot": "swot",
        "concevoir_gtm_quebec": "gtm",
        "analyser_risques_reglementaires_quebec": "risques_reglementaires",
        "calculer_score_viabilite": "score_viabilite",
    }
    
    cle = correspondances.get(nom)
    if cle and isinstance(resultat, dict) and "erreur" not in resultat:
        enregistrer_analyse(etat, cle, resultat)
    
    # Enregistrer les documents ecrits
    if nom == "ecrire_fichier_markdown" and isinstance(resultat, dict):
        if resultat.get("statut") == "succes":
            enregistrer_document(
                etat,
                resultat.get("chemin_relatif", resultat.get("nom_fichier", "")),
                resultat.get("nb_lignes", 0)
            )
