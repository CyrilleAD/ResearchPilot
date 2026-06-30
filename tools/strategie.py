import json
from datetime import datetime
from tools.base import appel_llm, parser_json
from prompts import SYSTEM_PROMPT_STRATEGIE, SYSTEM_PROMPT_GENERATION
    



def generer_swot(
    description_projet: str,
    analyse_marche: dict,
    analyse_concurrents: dict,
    couts_dev: dict
) -> dict:
    """
    Genere l'analyse SWOT complete et honnete.
    
    Param : les resultats des agents precedents.
    L'agent strategie lit les resultats de tous les autres agents
    pour avoir une vue d'ensemble.
    """
    potentiel = analyse_marche.get("potentiel_general", "inconnu")
    nb_concurrents = len(analyse_concurrents.get("concurrents_directs", []))
    budget_realiste = couts_dev.get("budget_total_cad", {}).get("scenario_realiste", "?")
    barriere = analyse_concurrents.get("barriere_entree_marche", "inconnue")
    
    prompt = f"""Genere une analyse SWOT HONNETE pour ce projet.

Description : {description_projet}
Potentiel marche Quebec : {potentiel}
Nb concurrents directs : {nb_concurrents}
Barriere a l'entree : {barriere}
Budget dev (realiste) : {budget_realiste}$ CAD

REGLE ABSOLUE : Les faiblesses et menaces doivent etre aussi nombreuses et
detaillees que les forces et opportunites. Un rapport trop positif est inutile.

Reponds en JSON :
{{
    "forces": [
        {{
            "element": "Description courte",
            "detail": "Pourquoi c'est une vraie force",
            "impact": "eleve / moyen / faible"
        }}
    ],
    "faiblesses": [
        {{
            "element": "Description courte",
            "detail": "Pourquoi c'est une faiblesse concrete",
            "impact": "eleve / moyen / faible",
            "mitigation_possible": "Comment attenuer cette faiblesse",
            "urgence": "maintenant / moyen terme / long terme"
        }}
    ],
    "opportunites": [
        {{
            "element": "Description courte",
            "detail": "Comment exploiter concretement",
            "impact_potentiel": "eleve / moyen / faible",
            "horizon": "court terme / moyen terme / long terme",
            "action_requise": "Ce qu'il faut faire pour saisir l'opportunite"
        }}
    ],
    "menaces": [
        {{
            "element": "Description courte",
            "detail": "Pourquoi c'est une menace reelle",
            "probabilite": "faible / moyenne / elevee",
            "impact_si_materialise": "faible / moyen / fort / critique",
            "strategie_defensive": "Comment se proteger"
        }}
    ],
    "synthese_strategique": "2-3 phrases sur la position strategique globale"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_STRATEGIE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "forces": [], "faiblesses": [], "opportunites": [], "menaces": [],
        "synthese_strategique": "Analyse non disponible"
    })




def concevoir_gtm_quebec(
    description_projet: str,
    public_cible: str,
    prix_mensuel_cad: float,
    positionnement: dict = None,
    budget_marketing_mensuel_cad: float = 500.0
) -> dict:
    """
    Conçoit la strategie de lancement specifique au Quebec.

    Budget par defaut = 500$/mois. C'est un budget de fondateur solo realiste.
    Les conseils sont adaptes a ce budget — pas de conseils pour agences.
    """
    positionnement = positionnement or {}
    pvt = positionnement.get("proposition_valeur_unique", "non definie")
    segment = positionnement.get("segment_cible_prioritaire", {})
    
    prompt = f"""Conçois la strategie Go-to-Market pour le Quebec.

Projet : {description_projet}
Public cible : {public_cible}
Prix : {prix_mensuel_cad}$ CAD/mois
Proposition de valeur : {pvt}
Segment prioritaire : {json.dumps(segment, ensure_ascii=False)}
Budget marketing mensuel : {budget_marketing_mensuel_cad}$ CAD

IMPORTANT : Conseils adaptes au budget de {budget_marketing_mensuel_cad}$/mois.
Pas de conseils pour gros budgets. Entrepreneur solo au Quebec.

Reponds en JSON :
{{
    "strategie_generale": "Approche globale en 3-4 phrases",
    "canaux_acquisition_par_priorite": [
        {{
            "rang": 1,
            "canal": "Nom du canal",
            "description": "Comment l'utiliser concretement",
            "cout_mensuel_cad": 0,
            "effort_hebdo_heures": 0,
            "resultats_attendus_mois_3": "Nb de leads attendus",
            "pourquoi_ce_canal_fonctionne_quebec": "Specificite quebecoise"
        }}
    ],
    "partenariats_strategiques_quebec": [
        {{
            "type_partenaire": "Incubateur / Chambre de commerce / Media / etc.",
            "exemples_concrets": ["Nom reel au Quebec"],
            "valeur_pour_eux": "Ce qu'ils gagnent",
            "valeur_pour_nous": "Ce qu'on gagne",
            "comment_approcher": "Email / evenement / LinkedIn"
        }}
    ],
    "strategie_contenu_francophone": {{
        "plateformes_prioritaires": ["LinkedIn", "YouTube", "etc."],
        "types_contenu": ["article", "video", "etc."],
        "frequence_publication": "X fois / semaine"
    }},
    "plan_action_90_jours": [
        {{
            "periode": "Semaines 1-2",
            "actions": ["Action 1 concrete"],
            "objectif_mesurable": "KPI a atteindre",
            "budget_utilise_cad": 0
        }},
        {{
            "periode": "Semaines 3-6",
            "actions": ["Action 1"],
            "objectif_mesurable": "KPI",
            "budget_utilise_cad": 0
        }},
        {{
            "periode": "Semaines 7-12",
            "actions": ["Action 1"],
            "objectif_mesurable": "KPI",
            "budget_utilise_cad": 0
        }}
    ],
    "kpis_succes_mois_3": {{
        "clients_payants_cibles": 0,
        "mrr_cible_cad": 0,
        "cout_acquisition_client_cible_cad": 0
    }},
    "erreurs_communes_eviter": ["Erreur que font les startups au Quebec"]
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_STRATEGIE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "strategie_generale": "Non disponible",
        "canaux_acquisition_par_priorite": [],
        "plan_action_90_jours": []
    })




def analyser_risques_reglementaires_quebec(
    type_projet: str,
    donnees_collectees: list,
    secteur: str
) -> dict:
    """
    Analyse la conformite reglementaire au Quebec.
    
    Loi 25 : obligatoire si tu collectes des donnees personnelles de Quebecois.
    LPRPDE : loi federale pour les activites inter-provinciales.
    Lois sectorielles : AMF (finance), MSSS (sante), CRTC (telecom).
    """
    donnees_str = json.dumps(donnees_collectees, ensure_ascii=False)
    
    prompt = f"""Analyse les risques reglementaires pour ce projet au Quebec.

Type : {type_projet}
Secteur : {secteur}
Donnees collectees : {donnees_str}

Analyse basee sur :
- Loi 25 (Quebec) — protection renseignements personnels, en vigueur 2022-2024
- LPRPDE (federal) — si activite inter-provinciale
- Loi 101 (Quebec) — obligations francais
- Lois sectorielles selon le secteur (AMF, MSSS, CRTC)
- TPS/TVQ sur les services numeriques

Reponds en JSON :
{{
    "niveau_risque_global": "faible / moyen / eleve / critique",
    "justification_niveau_risque": "Pourquoi ce niveau",
    "loi_25_analyse": {{
        "applicable": true,
        "obligations_immediates": [
            {{
                "obligation": "Nom de l'obligation",
                "description": "Ce que ca signifie",
                "comment_se_conformer": "Etapes concretes",
                "delai": "Maintenant / Avant le lancement / Dans 6 mois",
                "penalite_non_conformite": "Amende ou pourcentage"
            }}
        ],
        "donnees_sensibles_identifiees": [
            {{
                "type": "Nom de la donnee",
                "classification_loi25": "Non sensible / Sensible / Tres sensible",
                "consentement_requis": "Implicite / Explicite / Explicite ecrit"
            }}
        ]
    }},
    "obligations_fiscales_numerique": {{
        "tps_tva_applicable": true,
        "seuil_enregistrement_cad": 30000,
        "note": "Obligatoire de percevoir TPS+TVQ des 30 000$ de revenus"
    }},
    "plan_conformite_minimal": [
        {{
            "etape": 1,
            "action": "Action concrete",
            "cout_estime_cad": 0,
            "delai": "Avant le lancement"
        }}
    ],
    "faut_il_un_avocat": {{
        "recommandation": "Oui / Ressources gratuites suffisantes / Non",
        "ressources_gratuites": ["Commission d'acces a l'information : cai.gouv.qc.ca"]
    }}
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_STRATEGIE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "niveau_risque_global": "inconnu",
        "loi_25_analyse": {"applicable": True, "obligations_immediates": []},
        "plan_conformite_minimal": []
    })





def calculer_score_viabilite(
    description: str,
    analyse_marche: dict,
    analyse_concurrents: dict,
    couts_dev: dict,
    scenarios: dict,
    swot: dict = None,
    risques_reglementaires: dict = None
) -> dict:
    """
    Calcule le score de viabilite global (0-100) avec Python.

    Methode :
    1. Le LLM note chaque dimension independamment (0-100)
    2. Python calcule la moyenne ponderee finale
    3. Le LLM ne voit pas le score global (evite le biais d'ancrage)
    """
    swot = swot or {}
    risques_reglementaires = risques_reglementaires or {}
    # Resumer les donnees pour le LLM
    potentiel = analyse_marche.get("potentiel_general", "inconnu")
    score_marche_llm = analyse_marche.get("score_marche_sur_10", 5)
    nb_concurrents = len(analyse_concurrents.get("concurrents_directs", []))
    budget_realiste = couts_dev.get("budget_total_cad", {}).get("scenario_realiste", 0)
    break_even_realiste = scenarios.get("scenario_realiste", {}).get("mois_break_even", "?")
    profit_realiste = scenarios.get("scenario_realiste", {}).get("profit_net_fin_periode_cad", 0)
    risque_legal = risques_reglementaires.get("niveau_risque_global", "inconnu")
    nb_forces = len(swot.get("forces", []))
    nb_menaces = len(swot.get("menaces", []))
    
    prompt = f"""Evalue ces 6 dimensions et donne un score entre 0 et 100 pour chacune.
Tu ne calcules PAS le score global — c'est fait en Python. Evalue independamment.

DONNEES :
Description : {description}
Potentiel marche : {potentiel} (score pre-evalue : {score_marche_llm}/10)
Nb concurrents directs : {nb_concurrents}
Budget dev realiste : {budget_realiste:,}$ CAD
Break-even realiste : mois {break_even_realiste}
Profit 24 mois (realiste) : {profit_realiste:,}$ CAD
Risque reglementaire : {risque_legal}
Forces SWOT : {nb_forces} | Menaces SWOT : {nb_menaces}

Reponds en JSON :
{{
    "potentiel_marche": {{
        "score": 0,
        "poids_pct": 25,
        "justification": "Cite les chiffres",
        "points_positifs": ["point"],
        "points_negatifs": ["point"]
    }},
    "faisabilite_technique": {{
        "score": 0,
        "poids_pct": 20,
        "justification": "Complexite technique",
        "points_positifs": [],
        "points_negatifs": []
    }},
    "viabilite_financiere": {{
        "score": 0,
        "poids_pct": 20,
        "justification": "Modele financier",
        "points_positifs": [],
        "points_negatifs": []
    }},
    "position_concurrentielle": {{
        "score": 0,
        "poids_pct": 15,
        "justification": "Position face aux concurrents",
        "points_positifs": [],
        "points_negatifs": []
    }},
    "risque_reglementaire": {{
        "score": 0,
        "poids_pct": 10,
        "justification": "Score INVERSE du risque (100=pas de risque)",
        "points_positifs": [],
        "points_negatifs": []
    }},
    "qualite_plan": {{
        "score": 0,
        "poids_pct": 10,
        "justification": "Qualite du plan et documentation",
        "points_positifs": [],
        "points_negatifs": []
    }},
    "recommandations_prioritaires": [
        "1. Action la plus urgente",
        "2. Deuxieme priorite"
    ],
    "pivot_suggere_si_score_bas": "Direction alternative si score < 50"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_STRATEGIE, prompt, max_tokens=2500)
    data = parser_json(reponse, {})
    
    # =========================================================
    # CALCUL PYTHON du score global — jamais confie au LLM
    # =========================================================
    dimensions = [
        "potentiel_marche", "faisabilite_technique", "viabilite_financiere",
        "position_concurrentielle", "risque_reglementaire", "qualite_plan"
    ]
    
    score_global = 0.0
    detail_calcul = {}
    
    for dim in dimensions:
        info = data.get(dim, {})
        if isinstance(info, dict):
            score = min(100, max(0, int(info.get("score", 50))))  # Clamp entre 0 et 100
            poids = info.get("poids_pct", 0) / 100
            contribution = score * poids
            score_global += contribution
            detail_calcul[dim] = {
                "score": score,
                "poids_pct": info.get("poids_pct", 0),
                "contribution": round(contribution, 2)
            }
    
    score_global = round(score_global)
    
    # Verdict base sur le score
    if score_global >= 75:
        verdict = "EXCELLENT"
        action = "Les conditions sont reunies. Lance le projet avec confiance."
    elif score_global >= 60:
        verdict = "BON"
        action = "Adresse les 2-3 faiblesses prioritaires, puis lance."
    elif score_global >= 45:
        verdict = "MOYEN"
        action = "Cree un MVP minimal et valide tes hypotheses avant d'investir."
    else:
        verdict = "FAIBLE"
        action = "Reconsidere le concept. Explore le pivot suggere."
    
    data["score_global"] = score_global
    data["verdict"] = verdict
    data["action_recommandee"] = action
    data["detail_calcul_score"] = detail_calcul
    
    return data






def generer_rapport_swot(swot: dict = None, nom_projet: str = "Projet", **_kwargs) -> str:
    """Genere ANALYSE_SWOT.md — retourne une STRING Markdown."""
    swot = swot or {}
    # Resumer les donnees SWOT
    forces = [f.get("element","") for f in swot.get("forces", [])]
    faiblesses = [f.get("element","") for f in swot.get("faiblesses", [])]
    
    prompt = f"""Redige l'analyse SWOT complete en Markdown pour "{nom_projet}".

Forces : {json.dumps(forces, ensure_ascii=False)}
Faiblesses : {json.dumps(faiblesses, ensure_ascii=False)}
Donnees completes : {json.dumps(swot, ensure_ascii=False)[:2000]}

Structure :
# Analyse SWOT — {nom_projet}
## Matrice SWOT (tableau 2x2)
## Forces (Strengths)
## Faiblesses (Weaknesses)
## Opportunites (Opportunities)
## Menaces (Threats)
## Interactions TOWS
## Synthese"""
    
    return appel_llm(SYSTEM_PROMPT_GENERATION, prompt, temperature=0.3, max_tokens=4000)


def generer_rapport_gtm(gtm: dict = None, nom_projet: str = "Projet", budget_mensuel_cad: float = 500.0, **_kwargs) -> str:
    """Genere STRATEGIE_LANCEMENT.md — retourne une STRING Markdown."""
    gtm = gtm or {}
    prompt = f"""Redige la strategie de lancement complete en Markdown pour "{nom_projet}".
Budget : {budget_mensuel_cad}$ CAD/mois

Donnees GTM : {json.dumps(gtm, ensure_ascii=False)[:2500]}

Structure :
# Strategie de Lancement — {nom_projet}
## 1. Strategie Generale
## 2. Canaux d'Acquisition (tableau priorite / cout / effort / resultats)
## 3. Partenariats Strategiques au Quebec
## 4. Strategie de Contenu Francophone
## 5. Plan 90 Jours (tableau avec semaines et KPIs)
## 6. KPIs de Succes
## 7. Repartition Budget Marketing
## 8. Erreurs a Eviter
## 9. Ressources Quebec pour Entrepreneurs"""
    
    return appel_llm(SYSTEM_PROMPT_GENERATION, prompt, temperature=0.3, max_tokens=4000)


def generer_rapport_viabilite(score_data: dict = None, nom_projet: str = "Projet", **_kwargs) -> str:
    """Genere SCORE_VIABILITE.md — retourne une STRING Markdown."""
    score_data = score_data or {}
    score = score_data.get("score_global", 0)
    verdict = score_data.get("verdict", "INCONNU")
    action = score_data.get("action_recommandee", "")
    
    prompt = f"""Redige le rapport de score de viabilite en Markdown pour "{nom_projet}".

SCORE FINAL : {score}/100
VERDICT : {verdict}
ACTION RECOMMANDEE : {action}

Donnees completes : {json.dumps(score_data, ensure_ascii=False)[:2000]}

Structure :
# Score de Viabilite — {nom_projet}
## Verdict Global (Score : {score}/100 — {verdict})
## Detail des 6 Dimensions (tableau avec score, poids, contribution)
## Analyse par Dimension
## Recommandations Prioritaires (les 3 actions les plus urgentes)
## Plan d'Action
## Conclusion Finale (etre direct et honnete)"""
    
    return appel_llm(SYSTEM_PROMPT_GENERATION, prompt, temperature=0.3, max_tokens=4000)