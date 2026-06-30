import math
from datetime import datetime
from config import REGION
from tools.base import appel_llm, parser_json
from prompts import SYSTEM_PROMPT_FINANCE, SYSTEM_PROMPT_GENERATION




def estimer_couts_developpement(
    nb_semaines_estimees: int,
    profil_developpeur: str,
    taux_horaire_min_cad: float,
    taux_horaire_moyen_cad: float,
    taux_horaire_max_cad: float,
    infra_mensuel_cad: float = 55.0,
    heures_par_semaine: int = 30,
    couts_outils_mensuels_cad: float = 100.0
) -> dict:
    """
    Estime les couts de developpement avec les taux horaires reels fetches par Tavily.

    DOIT etre appele APRES rechercher_donnees_marche("salaires_developpeurs").
    Les taux horaires (min/moyen/max) viennent de cet appel prealable.

    Parametres :
        nb_semaines_estimees      : Duree totale du projet en semaines
        profil_developpeur        : Description ex: "dev senior Python IA"
        taux_horaire_min_cad      : Taux horaire plancher (fetch via Tavily)
        taux_horaire_moyen_cad    : Taux horaire moyen (fetch via Tavily)
        taux_horaire_max_cad      : Taux horaire plafond (fetch via Tavily)
        infra_mensuel_cad         : Cout infra mensuel (fetch ou defaut 55$)
        heures_par_semaine        : Heures de travail par semaine (defaut 30)
        couts_outils_mensuels_cad : Licences, outils, etc. (defaut 100$)
    """
    if taux_horaire_min_cad <= 0:
        raise ValueError(
            "taux_horaire_min_cad doit etre > 0. "
            "Appelle rechercher_donnees_marche('salaires_developpeurs') d'abord "
            "pour obtenir les vrais taux horaires."
        )

    # CALCUL PYTHON — jamais le LLM pour les maths
    total_heures = nb_semaines_estimees * heures_par_semaine
    nb_mois = nb_semaines_estimees / 4.33  # 4.33 semaines par mois en moyenne

    # Les 3 scenarios de cout salaire
    cout_salaire_min  = total_heures * taux_horaire_min_cad
    cout_salaire_moy  = total_heures * taux_horaire_moyen_cad
    cout_salaire_max  = total_heures * taux_horaire_max_cad

    # Couts infrastructure
    cout_infra = infra_mensuel_cad * nb_mois

    # Couts outils
    cout_outils = couts_outils_mensuels_cad * nb_mois

    # Totaux par scenario
    total_min = cout_salaire_min + cout_infra + cout_outils
    total_moy = cout_salaire_moy + cout_infra + cout_outils
    total_max = cout_salaire_max + cout_infra + cout_outils

    # Marges de securite
    budget_optimiste  = round(total_moy * 0.85)   # -15%
    budget_realiste   = round(total_moy)
    budget_pessimiste = round(total_max * 1.15)   # taux max + 15%

    # LLM interprete seulement — Python a deja calcule
    prompt = f"""Interprete ces couts de developpement pour {REGION}.

Profil recherche : {profil_developpeur}
Duree : {nb_semaines_estimees} semaines ({nb_mois:.1f} mois)
Heures travaillees : {total_heures:.0f}h
Taux horaire utilise : {taux_horaire_min_cad}-{taux_horaire_max_cad}$ CAD/h (fetch Tavily)

COUTS CALCULES EN PYTHON :
- Salaires scenario bas  : {cout_salaire_min:,.0f}$ CAD
- Salaires scenario moyen : {cout_salaire_moy:,.0f}$ CAD
- Salaires scenario haut : {cout_salaire_max:,.0f}$ CAD
- Infrastructure ({nb_mois:.1f} mois x {infra_mensuel_cad}$/mois) : {cout_infra:,.0f}$ CAD
- Outils/licences : {cout_outils:,.0f}$ CAD
- Budget realiste total : {budget_realiste:,}$ CAD

Reponds en JSON :
{{
    "analyse_budget": "1-2 phrases : ce budget est-il realiste pour {REGION} ?",
    "risques_sous_estimation": ["Cout souvent oublie 1", "Cout oublie 2"],
    "conseils_reduction_couts": ["Conseil 1 pour reduire sans compromettre la qualite"],
    "comparaison_marche": "Comment ce budget se compare aux projets similaires",
    "programmes_aide_applicables": ["RS&DE", "PARI-CNRC", "etc."],
    "economies_potentielles_avec_aide_cad": 0
}}"""

    interpretation = parser_json(
        appel_llm(SYSTEM_PROMPT_FINANCE, prompt, temperature=0.2),
        {"analyse_budget": ""},
        "estimer_couts_developpement"
    )

    return {
        "profil_developpeur": profil_developpeur,
        "region": REGION,
        "nb_semaines_estimees": nb_semaines_estimees,
        "nb_mois": round(nb_mois, 1),
        "total_heures": round(total_heures),
        "taux_horaire_cad": {
            "min": taux_horaire_min_cad,
            "moyen": taux_horaire_moyen_cad,
            "max": taux_horaire_max_cad
        },
        "detail_couts_cad": {
            "salaires_scenario_bas": round(cout_salaire_min),
            "salaires_scenario_moyen": round(cout_salaire_moy),
            "salaires_scenario_haut": round(cout_salaire_max),
            "infrastructure": round(cout_infra),
            "outils_licences": round(cout_outils)
        },
        "budget_total_cad": {
            "scenario_optimiste": budget_optimiste,
            "scenario_realiste": budget_realiste,
            "scenario_pessimiste": budget_pessimiste
        },
        "interpretation": interpretation
    }




def modeliser_revenus(
    prix_mensuel_cad: float,
    clients_initiaux: int,
    taux_croissance_mensuel_pct: float,
    taux_churn_mensuel_pct: float,
    couts_acquisition_cad: float = 100.0,
    nb_mois: int = 24
) -> dict:
    """
    Calcule les metriques SaaS cles : MRR, ARR, CAC, LTV, LTV/CAC.
    TOUT est calcule en Python ici.
    """
    # Conversions
    taux_croissance = taux_croissance_mensuel_pct / 100
    taux_churn = taux_churn_mensuel_pct / 100
    
    # MRR initial
    mrr_initial = clients_initiaux * prix_mensuel_cad
    
    # CAC
    clients_par_mois = clients_initiaux * taux_croissance
    cac = couts_acquisition_cad / clients_par_mois if clients_par_mois > 0 else 0
    
    # LTV
    duree_vie_mois = 1 / taux_churn if taux_churn > 0 else 999
    ltv = prix_mensuel_cad * duree_vie_mois
    
    # Ratio LTV/CAC
    ratio_ltv_cac = ltv / cac if cac > 0 else 0
    
    # ARR projete
    arr_projete = mrr_initial * 12
    
    # Interpretation LLM
    prompt = f"""Interprete ces metriques SaaS.

Prix mensuel : {prix_mensuel_cad}$ CAD
Clients initiaux : {clients_initiaux}
Taux croissance mensuel : {taux_croissance_mensuel_pct}%
Churn mensuel : {taux_churn_mensuel_pct}%
CAC calcule : {cac:.2f}$ CAD
LTV calculee : {ltv:.2f}$ CAD
Ratio LTV/CAC : {ratio_ltv_cac:.1f}

Reponds en JSON :
{{
    "evaluation_metriques": "eleve / bon / acceptable / preoccupant",
    "analyse_cac": "Le CAC de {cac:.0f}$ est-il raisonnable pour ce secteur ?",
    "analyse_churn": "Un churn de {taux_churn_mensuel_pct}% est-il acceptable ?",
    "analyse_ltv_cac": "Que signifie un ratio de {ratio_ltv_cac:.1f} ? (>3 = bon)",
    "actions_pour_ameliorer": ["Action 1 pour ameliorer les metriques"],
    "risque_principal": "Le plus grand risque financier identifie"
}}"""
    
    interpretation = parser_json(
        appel_llm(SYSTEM_PROMPT_FINANCE, prompt, temperature=0.2),
        {"evaluation_metriques": "inconnu"},
        "modeliser_revenus"
    )
    
    return {
        "prix_mensuel_cad": prix_mensuel_cad,
        "clients_initiaux": clients_initiaux,
        "taux_croissance_mensuel_pct": taux_croissance_mensuel_pct,
        "taux_churn_mensuel_pct": taux_churn_mensuel_pct,
        "mrr_initial_cad": round(mrr_initial, 2),
        "arr_projete_cad": round(arr_projete, 2),
        "cac_cad": round(cac, 2),
        "ltv_cad": round(ltv, 2),
        "ratio_ltv_cac": round(ratio_ltv_cac, 2),
        "duree_vie_client_mois": round(duree_vie_mois, 1),
        "interpretation": interpretation
    }




def calculer_point_equilibre(
    couts_fixes_mensuels_cad: float,
    prix_unitaire_cad: float,
    cout_variable_par_client_cad: float = 0.0
) -> dict:
    """
    Calcule le point mort (break-even) : combien de clients pour etre rentable.
    
    Formule :
    break_even = ceil(couts_fixes / (prix - cout_variable))
    
    Exemple :
    couts_fixes = 5000$ (loyer serveur + salaire fondateur)
    prix = 79$ (abonnement mensuel)
    cout_variable = 5$ (cout du LLM par client)
    break_even = ceil(5000 / (79-5)) = ceil(67.5) = 68 clients
    
    Pourquoi ceil() et pas round() ?
    Parce qu'a 67 clients, tu perds encore de l'argent.
    Il faut 68 clients complets, pas 67.5 clients imaginaires.
    """
    marge_par_client = prix_unitaire_cad - cout_variable_par_client_cad
    
    if marge_par_client <= 0:
        return {
            "erreur": "Le prix est inferieur ou egal au cout variable. Modele non viable.",
            "break_even_clients": None,
            "marge_par_client_cad": round(marge_par_client, 2)
        }
    
    # La formule du break-even
    break_even = math.ceil(couts_fixes_mensuels_cad / marge_par_client)
    
    mrr_break_even = break_even * prix_unitaire_cad
    
    # Interpretation
    prompt = f"""Interprete ce break-even.

Couts fixes mensuels : {couts_fixes_mensuels_cad:,.0f}$ CAD
Prix unitaire : {prix_unitaire_cad}$ CAD
Cout variable par client : {cout_variable_par_client_cad}$ CAD
Break-even calcule : {break_even} clients

Reponds en JSON :
{{
    "evaluation": "facile / atteignable / ambitieux / tres difficile",
    "contexte": "En combien de temps peut-on realiste attendre {break_even} clients ?",
    "strategies_atteindre_plus_vite": ["Strategie 1"],
    "sensibilite_prix": "Que se passe-t-il si on augmente le prix de 20% ?",
    "alerte_si_applicable": "Risque specifique a signaler ou null"
}}"""
    
    interpretation = parser_json(
        appel_llm(SYSTEM_PROMPT_FINANCE, prompt, temperature=0.2),
        {"evaluation": "inconnu"},
        "calculer_point_equilibre"
    )
    
    return {
        "couts_fixes_mensuels_cad": couts_fixes_mensuels_cad,
        "prix_unitaire_cad": prix_unitaire_cad,
        "cout_variable_par_client_cad": cout_variable_par_client_cad,
        "marge_par_client_cad": round(marge_par_client, 2),
        "break_even_clients": break_even,
        "mrr_au_break_even_cad": round(mrr_break_even, 2),
        "interpretation": interpretation
    }





def projeter_scenarios_financiers(
    prix_mensuel_cad: float,
    clients_initiaux: int,
    couts_fixes_mensuels_cad: float,
    cout_variable_par_client_cad: float = 0.0,
    nb_mois: int = 24
) -> dict:
    """
    Projete 3 scenarios sur 24 mois.
    TOUT le calcul est fait en Python.
    
    Scenarios :
    - Optimiste  : croissance +20%/mois, churn 2%
    - Realiste   : croissance +8%/mois, churn 5%
    - Pessimiste : croissance +3%/mois, churn 10%
    """
    scenarios = {
        "scenario_optimiste":  {"croissance": 0.20, "churn": 0.02},
        "scenario_realiste":   {"croissance": 0.08, "churn": 0.05},
        "scenario_pessimiste": {"croissance": 0.03, "churn": 0.10},
    }
    
    resultats = {}
    
    for nom_scenario, params in scenarios.items():
        croissance = params["croissance"]
        churn = params["churn"]
        
        clients = float(clients_initiaux)
        mrr_evolution = []
        revenu_total = 0.0
        profit_total = 0.0
        mois_break_even = None
        
        # Simulation mois par mois
        for mois in range(1, nb_mois + 1):
            # Calcul du MRR de ce mois
            mrr = clients * prix_mensuel_cad
            
            # Couts ce mois
            couts_variables = clients * cout_variable_par_client_cad
            couts_totaux = couts_fixes_mensuels_cad + couts_variables
            
            # Profit ce mois
            profit_mois = mrr - couts_totaux
            profit_total += profit_mois
            revenu_total += mrr
            
            # Detecter le break-even (premier mois profitable)
            if profit_mois >= 0 and mois_break_even is None:
                mois_break_even = mois
            
            mrr_evolution.append({
                "mois": mois,
                "clients": round(clients),
                "mrr_cad": round(mrr),
                "profit_mois_cad": round(profit_mois)
            })
            
            # Mettre a jour les clients pour le prochain mois
            nouveaux = clients * croissance
            perdus = clients * churn
            clients = clients + nouveaux - perdus
        
        mrr_final = round(clients * prix_mensuel_cad)
        arr_projete = mrr_final * 12
        
        resultats[nom_scenario] = {
            "croissance_mensuelle_pct": croissance * 100,
            "churn_mensuel_pct": churn * 100,
            "clients_finaux": round(clients),
            "mrr_final_cad": mrr_final,
            "arr_projete_cad": arr_projete,
            "revenu_total_periode_cad": round(revenu_total),
            "profit_net_fin_periode_cad": round(profit_total),
            "mois_break_even": mois_break_even if mois_break_even else f">{nb_mois}",
            "mrr_evolution": mrr_evolution  # Les 24 points de donnees
        }
    
    # Interpretation LLM des 3 scenarios
    realiste = resultats["scenario_realiste"]
    prompt = f"""Interprete ces 3 scenarios financiers sur {nb_mois} mois.

SCENARIO REALISTE (le plus probable) :
- Clients apres {nb_mois} mois : {realiste['clients_finaux']}
- MRR final : {realiste['mrr_final_cad']:,}$ CAD
- Profit total : {realiste['profit_net_fin_periode_cad']:,}$ CAD
- Break-even : mois {realiste['mois_break_even']}

Reponds en JSON :
{{
    "scenario_le_plus_probable": "realiste / optimiste / pessimiste avec justification",
    "analyse_scenario_realiste": "1-2 phrases sur ce scenario",
    "risque_pessimiste": "La probabilite que le pessimiste se realise et comment l'eviter",
    "conditions_optimiste": "Qu'est-ce qu'il faudrait pour atteindre le scenario optimiste ?",
    "recommandation_principale": "1 action prioritaire basee sur ces projections"
}}"""
    
    interpretation = parser_json(
        appel_llm(SYSTEM_PROMPT_FINANCE, prompt, temperature=0.2),
        {},
        "projeter_scenarios_financiers"
    )
    resultats["interpretation_globale"] = interpretation
    
    return resultats






def generer_rapport_financier(
    nom_projet: str,
    couts_dev: dict,
    revenus: dict,
    break_even: dict,
    scenarios: dict = None,
    **_kwargs
) -> str:
    """
    Genere le contenu complet de ANALYSE_FINANCIERE.md.
    Retourne une STRING Markdown.
    """
    scenarios = scenarios or {}
    # Extraire les donnees cles
    budget_realiste = couts_dev.get("budget_total_cad", {}).get("scenario_realiste", 0)
    ltv = revenus.get("ltv_cad", 0)
    cac = revenus.get("cac_cad", 0)
    ratio = revenus.get("ratio_ltv_cac", 0)
    be_clients = break_even.get("break_even_clients", 0)

    prompt = f"""Redige l'analyse financiere complete en Markdown pour "{nom_projet}".

DONNEES FINANCIERES CALCULEES :
- Budget dev (realiste) : {budget_realiste:,}$ CAD
- Prix mensuel : {revenus.get('prix_mensuel_cad', 0)}$ CAD
- MRR initial : {revenus.get('mrr_initial_cad', 0):,.2f}$ CAD
- LTV client : {ltv:,.2f}$ CAD
- CAC : {cac:,.2f}$ CAD
- Ratio LTV/CAC : {ratio:.1f}
- Break-even : {be_clients} clients
- Scenario realiste 24 mois :
  * Clients finaux : {scenarios.get('scenario_realiste', {}).get('clients_finaux', 0)}
  * MRR final : {scenarios.get('scenario_realiste', {}).get('mrr_final_cad', 0):,}$ CAD
  * Break-even : mois {scenarios.get('scenario_realiste', {}).get('mois_break_even', '?')}

Structure du document Markdown :
# Analyse Financiere — {nom_projet}
_Date : {datetime.now().strftime('%B %Y')} | Monnaie : CAD | TVA : TPS 5% + TVQ 9.975%_

## 1. Investissement Initial
_(detail des couts de developpement avec tableau)_

## 2. Metriques SaaS
_(tableau MRR, ARR, CAC, LTV, LTV/CAC avec interpretation)_

## 3. Point Mort (Break-even)
_(formule, resultat, interpretation)_

## 4. Scenarios sur 24 Mois
_(tableau comparatif optimiste/realiste/pessimiste)_

## 5. Projections Detaillees — Scenario Realiste
_(evolution mois par mois — tableau des 6 premiers mois)_

## 6. Programmes d'Aide et Credits d'Impot
_(RS&DE, Investissement Quebec, PARI-CNRC)_

## 7. Risques Financiers et Mitigation

## 8. Recommandations et Prochaines Etapes"""

    return appel_llm(SYSTEM_PROMPT_GENERATION, prompt, temperature=0.3, max_tokens=4000)