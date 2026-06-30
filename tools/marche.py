import json
from datetime import datetime
from tools.base import appel_llm, parser_json, recherche_tavily
from prompts import SYSTEM_PROMPT_MARCHE, SYSTEM_PROMPT_GENERATION
    




def analyser_marche_quebec(
    description_projet: str,
    secteur: str,
    public_cible: str,
    modele_revenu: str = "SaaS"
) -> dict:
    """
    Analyse le marche quebecois avec TAM/SAM/SOM.
    
    Specifique au Quebec :
    - Population ~8.8M habitants (2024)
    - ~80% francophone
    - Programmes gouvernementaux genereux pour les startups tech
    - Fort sentiment d'identite locale (preference pour produits locaux)
    """
    resultats_web = recherche_tavily(
        f"marche {secteur} Quebec taille chiffres statistiques"
    )
    
    contexte_web = ""
    if resultats_web:
        contexte_web = "\nDONNEES WEB RECENTES :\n"
        for r in resultats_web[:4]:
            contexte_web += f"- {r.get('title','')} : {r.get('content','')[:200]}\n"
    
    prompt = f"""Analyse le marche quebecois pour ce projet.

Projet : {description_projet}
Secteur : {secteur}
Public cible : {public_cible}
Modele de revenu : {modele_revenu}
{contexte_web}

IMPORTANT : Donner des fourchettes (min-max) pour les tailles de marche.
Ne jamais presenter une estimation comme un fait verifie.

Reponds en JSON :
{{
    "secteur": "{secteur}",
    "date_analyse": "{datetime.now().strftime('%Y-%m')}",
    "tam": {{
        "description": "Marche mondial ou nord-americain total",
        "valeur_min_cad": 0,
        "valeur_max_cad": 0,
        "source": "Estimation LLM / source web",
        "methode_calcul": "Comment ce chiffre a ete derive"
    }},
    "sam": {{
        "description": "Marche atteignable avec notre modele au Quebec/Canada",
        "valeur_min_cad": 0,
        "valeur_max_cad": 0,
        "criteres_inclusion": ["Critere 1 pour etre dans le SAM"]
    }},
    "som": {{
        "description": "Part realiste en 3-5 ans",
        "valeur_min_cad": 0,
        "valeur_max_cad": 0,
        "hypotheses": ["Hypothese 1 pour atteindre ce SOM"],
        "part_du_sam_pct": 0
    }},
    "croissance_marche": {{
        "taux_annuel_pct": 0,
        "tendance": "croissance / stable / declin",
        "facteurs_croissance": ["Facteur 1"]
    }},
    "specifiques_quebec": {{
        "population_cible": "Taille du public cible au Quebec",
        "avantages_marche_local": ["Avantage 1"],
        "defis_marche_local": ["Defi 1"],
        "programmes_aide_applicables": ["Investissement Quebec", "PARI-CNRC", "RS&DE"],
        "sensibilite_langue_francaise": "eleve / moyen / faible"
    }},
    "potentiel_general": "eleve / moyen / faible / inconnu",
    "score_marche_sur_10": 0,
    "justification_score": "Pourquoi ce score"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_MARCHE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "secteur": secteur,
        "tam": {},
        "sam": {},
        "som": {},
        "potentiel_general": "inconnu",
        "score_marche_sur_10": 5
    })





def analyser_concurrents_quebec(
    description_projet: str,
    secteur: str,
    public_cible: str
) -> dict:
    """
    Identifie et analyse les concurrents sur le marche quebecois.
    
    Distingue :
    - Concurrents directs : meme solution, meme public
    - Concurrents indirects : different moyen pour le meme but
    - Solutions de substitution : Excel, papier, agence, etc.
    """
    resultats_web = recherche_tavily(
        f"concurrents {secteur} logiciels {public_cible} comparatif"
    )
    
    contexte = ""
    if resultats_web:
        contexte = "\nCONCURRENTS TROUVES EN LIGNE :\n"
        for r in resultats_web[:4]:
            contexte += f"- {r.get('title','')} ({r.get('url','')})\n"
    
    prompt = f"""Analyse les concurrents sur le marche quebecois.

Projet : {description_projet}
Secteur : {secteur}
Public cible : {public_cible}
{contexte}

Reponds en JSON :
{{
    "concurrents_directs": [
        {{
            "nom": "Nom du concurrent",
            "description": "Ce qu'il fait",
            "type": "SaaS / open-source / agence",
            "prix_mensuel_cad": 0,
            "presence_quebec": "forte / moyenne / faible / absente",
            "langue_interface": "francais / anglais / bilingue",
            "part_de_marche": "leader / challenger / niche",
            "forces": ["Force 1"],
            "faiblesses": ["Faiblesse 1"],
            "url": "site.com"
        }}
    ],
    "concurrents_indirects": [
        {{
            "type": "Categorie (ex: logiciels generiques, agences)",
            "exemples": ["Nom 1"],
            "pourquoi_utilises": "Raison",
            "limite": "Pourquoi notre solution est meilleure"
        }}
    ],
    "part_de_marche_estimee_top3": {{
        "leader": "Nom + % estime",
        "challenger": "Nom + %",
        "autres": "% pour le reste du marche"
    }},
    "opportunites_differenciation": [
        "Ce que personne ne fait bien et qu'on pourrait faire"
    ],
    "barriere_entree_marche": "faible / moyenne / elevee / tres elevee",
    "justification_barriere": "Pourquoi c'est facile ou difficile d'entrer",
    "avantage_competitif_potentiel": "Notre avantage principal sur ce marche"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_MARCHE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "concurrents_directs": [],
        "opportunites_differenciation": [],
        "barriere_entree_marche": "inconnue"
    })





def identifier_tendances_secteur(
    secteur: str,
    horizon_annees: int = 3
) -> dict:
    """
    Identifie les megatendances qui vont impacter le secteur.
    
    Horizon de 3 ans : assez proche pour etre actionnable,
    assez loin pour que ca vaille la peine de se positionner.
    """
    resultats_web = recherche_tavily(
        f"tendances {secteur} technologie 2025 2026 2027 futur"
    )
    
    contexte = ""
    if resultats_web:
        contexte = "\n".join([r.get("content", "")[:200] for r in resultats_web[:3]])
    
    prompt = f"""Identifie les tendances cles pour ce secteur.

Secteur : {secteur}
Horizon : {horizon_annees} ans (2025-{2025 + horizon_annees})
{f"Contexte web : {contexte}" if contexte else ""}

Reponds en JSON :
{{
    "tendances_technologiques": [
        {{
            "tendance": "Nom de la tendance",
            "description": "Ce que ca signifie",
            "impact_sur_le_secteur": "eleve / moyen / faible",
            "horizon": "1 an / 2 ans / 3 ans / 5 ans+",
            "opportunite_ou_menace": "opportunite / menace / les deux",
            "comment_en_profiter": "Actions concretes a prendre"
        }}
    ],
    "tendances_reglementaires": [
        {{
            "tendance": "Loi ou regulation emergente",
            "description": "Ce que ca change",
            "impact": "positif / negatif / neutre pour notre projet",
            "quand": "Deja en vigueur / 2025 / 2026+"
        }}
    ],
    "tendances_comportement_clients": [
        {{
            "changement": "Ce qui change dans le comportement",
            "implication_produit": "Ce que ca signifie pour notre produit"
        }}
    ],
    "technologies_emergentes_a_surveiller": [
        "Technologie 1 qui pourrait disrupter le secteur"
    ],
    "risque_disruption": "faible / moyen / eleve",
    "fenetre_opportunite": "maintenant / 1-2 ans / 3-5 ans / incertaine"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_MARCHE, prompt, max_tokens=2500)
    return parser_json(reponse, {
        "tendances_technologiques": [],
        "tendances_reglementaires": [],
        "risque_disruption": "inconnu"
    })




def evaluer_positionnement(
    description_projet: str,
    analyse_marche: dict,
    analyse_concurrents: dict,
    prix_mensuel_cad: float = 0.0
) -> dict:
    """
    Evalue le positionnement concurrentiel et definit la proposition de valeur.
    
    Le positionnement repond a : "Pourquoi quelqu'un devrait choisir NOTRE produit
    plutot que le concurrent ?" Si on ne peut pas repondre clairement, on n'a
    pas encore de positionnement.
    """
    potentiel = analyse_marche.get("potentiel_general", "inconnu")
    barriere = analyse_concurrents.get("barriere_entree_marche", "inconnue")
    opps = analyse_concurrents.get("opportunites_differenciation", [])
    
    prompt = f"""Evalue le positionnement pour ce projet.

Projet : {description_projet}
Prix mensuel : {prix_mensuel_cad}$ CAD
Potentiel marche : {potentiel}
Barriere a l'entree : {barriere}
Opportunites de differenciation : {json.dumps(opps, ensure_ascii=False)}

Reponds en JSON :
{{
    "proposition_valeur_unique": "En quoi est-on different ET meilleur ? (1 phrase)",
    "positionnement_prix": {{
        "categorie": "economique / milieu de gamme / premium / entreprise",
        "justification": "Pourquoi ce niveau de prix est justifie",
        "comparaison_concurrents": "Plus cher / Equivalent / Moins cher que les concurrents"
    }},
    "segment_cible_prioritaire": {{
        "description": "Profil du client ideal",
        "taille_estimee_quebec": "Nombre d'organisations",
        "pourquoi_prioritaire": "Pourquoi commencer par eux"
    }},
    "axes_differenciation": [
        {{
            "axe": "Fonctionnalite / Prix / Service / Langue / etc.",
            "notre_avantage": "Ce qu'on fait mieux",
            "durabilite": "facile a copier / difficile a copier / brevet / reseau"
        }}
    ],
    "message_marketing_principal": "Le message en une phrase pour les pubs",
    "risque_erosion_avantage": "Combien de temps avant que les concurrents copient ?"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_MARCHE, prompt, max_tokens=2000)
    return parser_json(reponse, {
        "proposition_valeur_unique": "Non definie",
        "axes_differenciation": [],
        "segment_cible_prioritaire": {}
    })




def generer_rapport_marche(
    nom_projet: str,
    analyse_marche: dict,
    analyse_concurrents: dict,
    tendances: dict = None,
    positionnement: dict = None,
    **_kwargs
) -> str:
    """
    Genere le contenu complet de ANALYSE_MARCHE.md.
    
    Retourne une STRING (le contenu Markdown), pas un dict.
    C'est tools/fichiers.py qui l'ecrira sur le disque.
    """
    tendances = tendances or {}
    positionnement = positionnement or {}
    # Resumer les donnees pour le prompt (eviter de depasser le contexte)
    tam = analyse_marche.get("tam", {})
    sam = analyse_marche.get("sam", {})
    som = analyse_marche.get("som", {})
    nb_concurrents = len(analyse_concurrents.get("concurrents_directs", []))
    pvt = positionnement.get("proposition_valeur_unique", "")
    
    prompt = f"""Redige l'analyse de marche complete en Markdown pour "{nom_projet}".

DONNEES :
- TAM : {tam.get('valeur_min_cad', 0):,} a {tam.get('valeur_max_cad', 0):,} $ CAD
- SAM : {sam.get('valeur_min_cad', 0):,} a {sam.get('valeur_max_cad', 0):,} $ CAD
- SOM : {som.get('valeur_min_cad', 0):,} a {som.get('valeur_max_cad', 0):,} $ CAD
- Potentiel general : {analyse_marche.get('potentiel_general', 'inconnu')}
- Nb concurrents directs identifies : {nb_concurrents}
- Proposition de valeur unique : {pvt}

DONNEES COMPLETES : {json.dumps({
    "marche": analyse_marche,
    "concurrents": analyse_concurrents,
    "tendances": tendances,
    "positionnement": positionnement
}, ensure_ascii=False)[:3000]}

Structure du document Markdown :
# Analyse de Marche — {nom_projet}
_Date : {datetime.now().strftime('%B %Y')} | Marche : Quebec, Canada_

## 1. Taille du Marche (TAM/SAM/SOM)
_(tableau et explication de chaque niveau)_

## 2. Analyse de la Croissance

## 3. Specificites du Marche Quebecois

## 4. Concurrents Directs
_(tableau comparatif : nom, prix, forces, faiblesses)_

## 5. Concurrents Indirects et Solutions de Substitution

## 6. Tendances du Secteur

## 7. Positionnement et Proposition de Valeur

## 8. Opportunites de Differenciation

## 9. Programmes d'Aide Disponibles au Quebec

## 10. Conclusion et Recommandations"""
    
    return appel_llm(SYSTEM_PROMPT_GENERATION, prompt, temperature=0.3, max_tokens=4000)