import json
from config import REGION
from tools.base import appel_llm, parser_json, recherche_tavily, formater_resultats_tavily
from prompts import SYSTEM_PROMPT_RECHERCHE


def _valider_salaires_developpeurs(resultat: dict) -> dict:
    """Evite de propager des taux salariaux impossibles comme valeurs valides."""
    profils = resultat.get("profils", {})
    if not isinstance(profils, dict):
        return resultat

    avertissements = list(resultat.get("_validation_avertissements", []))
    champs_taux = ("min", "moyen", "max")

    for profil, valeurs in profils.items():
        if not isinstance(valeurs, dict):
            continue

        for champ in champs_taux:
            valeur = valeurs.get(champ)
            if valeur == 0:
                valeurs[champ] = None
                avertissements.append(
                    f"{profil}.{champ}: taux 0 invalide remplace par None"
                )

    if avertissements:
        resultat["_validation_avertissements"] = avertissements
        resultat["fiabilite"] = "a verifier"
        resultat.setdefault(
            "note",
            "Certains taux salariaux etaient absents ou invalides dans la reponse LLM."
        )

    return resultat


def rechercher_informations(
        requete: str,
        domaine: str = "",
        profondeur: str = "basique"
) -> dict:
    """
    Effectue une recherche d'information sur un sujet.
    
    C'est le premier outil que l'agent appelle pour toute nouvelle analyse.
    Tavily est requis (voir tools/base.py — leve ValueError si absent).
    """

    # Faire la recherche web via base.py
    resultats_web = recherche_tavily(
        f"{requete} {domaine}",
        nb_resultats=6 if profondeur == "avancee" else 4,
        region=REGION
    )

     # Formater les resultats pour le prompt
    contexte_web = formater_resultats_tavily(resultats_web, max_chars=300)

    prompt = f"""Recherche et synthetise les informations sur ce sujet :

    Sujet : {requete}
    Domaine : {domaine if domaine else "general"}
    Contexte : Projet technologique vise le marche {REGION}
    {contexte_web}

    Reponds en JSON :
    {{
        "sujet": "{requete}",
        "source_donnees": "tavily_web",
        "resume_principal": "3-4 phrases qui resument les informations cles",
        "faits_cles": [
            {{
                "fait": "Fait ou statistique important",
                "source": "URL ou nom de la source",
                "fiabilite": "haute / moyenne / estimation"
            }}
        ],
        "tendances_identifiees": ["Tendance 1", "Tendance 2"],
        "questions_sans_reponse": ["Ce qu'on ne sait pas encore"],
        "sources_consultees": [],
        "pertinence_region": "Pourquoi ces infos s'appliquent a {REGION}"
    }}"""

    reponse = appel_llm(SYSTEM_PROMPT_RECHERCHE, prompt)
    resultat = parser_json(reponse, {
        "sujet": requete,
        "resume_principal": "Recherche non disponible",
        "faits_cles": []
    }, "rechercher_informations")

    # Ajouter les resultats web bruts pour l'affichage UI
    resultat["_resultats_web_bruts"] = resultats_web
    return resultat


def analyser_besoins_utilisateurs(
        description_projet: str,
        public_cible: str,
        probleme_principal: str
) -> dict:
    """
    Cree des personas et identifie les pain points.
    
    Un persona = un profil fictif mais realiste d'un utilisateur typique.
    Les pain points = les vraies frustrations de cet utilisateur.
    """
    resultats_web = recherche_tavily(
        f"besoins {public_cible} probleme {probleme_principal}",
        nb_resultats=4,
        region=REGION
    )
    contexte = formater_resultats_tavily(resultats_web, max_chars=200)

    prompt = f"""Cree une analyse complete des besoins utilisateurs.

Projet : {description_projet}
Public cible : {public_cible}
Probleme a resoudre : {probleme_principal}
Marche : {REGION}
{contexte}

Reponds en JSON :
{{
    "personas": [
        {{
            "nom": "Prenom fictif et titre",
            "age": 0,
            "poste": "Titre du poste",
            "taille_entreprise": "Solo / 1-10 / 11-50 / 51-200 / 200+",
            "localisation_quebec": "Montreal / Quebec City / region",
            "objectifs_principaux": ["Ce qu'il veut accomplir"],
            "frustrations_actuelles": ["Ce qui le frustre aujourd'hui"],
            "comment_il_resout_maintenant": "Sa solution actuelle",
            "budget_mensuel_acceptable_cad": 0,
            "criteres_achat": ["Ce qui va le convaincre d'acheter"],
            "citations_typiques": ["Une phrase qu'il dirait"]
        }}
    ],
    "jobs_to_be_done": [
        {{
            "job": "Quand... je veux... pour...",
            "importance": "critique / important / nice-to-have",
            "satisfaction_actuelle": "faible / moyenne / bonne"
        }}
    ],
    "douleurs_non_evidentes": ["Pain point pas mentionne spontanement"],
    "questions_a_valider": ["Hypothese a valider avec des vraies interviews"],
    "segment_le_plus_prometteur": {{
        "profil": "Description du segment",
        "pourquoi": "Pourquoi commencer par eux",
        "taille_estimee_quebec": "Nombre d'organisations ou personnes"
    }}
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_RECHERCHE, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "personas": [],
        "jobs_to_be_done": [],
        "segment_le_plus_prometteur": {}
    }, "analyser_besoins_utilisateurs")



def etudier_solutions_existantes(
        probleme_a_resoudre: str,
        secteur: str,
        public_cible: str
) -> dict:
    """
    Analyse les alternatives deja sur le marche.
    Essentiel pour trouver ce qui differentie notre projet.
    """
    resultats_web = recherche_tavily(
        f"solutions logiciels {probleme_a_resoudre} {secteur} alternatives comparaison",
        nb_resultats=6,
        region=REGION
    )
    contexte = formater_resultats_tavily(resultats_web, max_chars=250)

    prompt = f"""Analyse les solutions existantes pour ce probleme.

Probleme : {probleme_a_resoudre}
Secteur : {secteur}
Public cible : {public_cible}
{contexte}

Reponds en JSON :
{{
    "solutions_directes": [
        {{
            "nom": "Nom du produit",
            "type": "SaaS / open-source / agence / manuel / autre",
            "prix_mensuel_cad": 0,
            "points_forts": ["Force 1"],
            "points_faibles": ["Faiblesse 1"],
            "part_de_marche": "leader / challenger / niche / inconnu",
            "disponible_en_francais": true,
            "url": "site.com"
        }}
    ],
    "solutions_indirectes": [
        {{
            "nom": "Solution de substitution",
            "pourquoi_utilisee": "Pourquoi les gens l'utilisent",
            "limite_principale": "Sa grande faiblesse"
        }}
    ],
    "lacunes_identifiees": ["Ce qu'aucune solution ne fait bien"],
    "opportunite_differenciation": "Ou est l'espace blanc sur le marche ?",
    "barriere_changer_solution": "Pourquoi les gens ne changent pas facilement",
    "conclusion": "Marche sature, sous-servi, ou vierge ?"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_RECHERCHE, prompt, max_tokens=2500)
    return parser_json(reponse, {
        "solutions_directes": [],
        "lacunes_identifiees": [],
        "conclusion": "Analyse non disponible"
    }, "etudier_solutions_existantes")


def identifier_technologies(
    type_projet: str,
    contraintes: list,
    competences_equipe: list,
    budget_infra_mensuel_cad: float = 55.0
) -> dict:
    """
    Recommande le meilleur stack technologique.
    
    L'objectif : recommander ce qui convient AU CONTEXTE (equipe, budget)
    pas juste "ce qui est populaire en 2024".
    """
    contraintes_str = json.dumps(contraintes, ensure_ascii=False)
    competences_str = json.dumps(competences_equipe, ensure_ascii=False)

    prompt = f"""Recommande le meilleur stack technologique pour ce projet.

Type de projet : {type_projet}
Contraintes : {contraintes_str}
Competences de l'equipe : {competences_str}
Budget infrastructure mensuel : {budget_infra_mensuel_cad}$ CAD
Contexte : Startup {REGION}, besoin de livrables rapides

Reponds en JSON :
{{
    "stack_recommande": {{
        "frontend": {{
            "technologie": "Nom",
            "version": "version stable",
            "justification": "Pourquoi ce choix",
            "alternative": "Si les competences ne matchent pas"
        }},
        "backend": {{
            "technologie": "Nom",
            "version": "version",
            "justification": "Pourquoi",
            "alternative": "Alternative"
        }},
        "base_de_donnees": {{
            "technologie": "Nom",
            "justification": "Pourquoi",
            "alternative": "Alternative"
        }},
        "infrastructure": {{
            "fournisseur": "AWS / GCP / Azure / Fly.io / Railway / autre",
            "services_utilises": ["Service 1"],
            "cout_mensuel_estime_cad": 0,
            "justification": "Pourquoi pour une startup Quebec"
        }},
        "ia_et_llm": {{
            "fournisseur": "OpenAI / Anthropic / Mistral / autre",
            "modele_recommande": "Nom du modele",
            "cout_par_requete_estime_cad": 0.0,
            "justification": "Pourquoi ce modele"
        }}
    }},
    "outils_developpement": {{
        "version_control": "GitHub / GitLab",
        "ci_cd": "GitHub Actions / CircleCI",
        "monitoring": "Outil recommande",
        "gestion_erreurs": "Sentry / autre"
    }},
    "risques_techniques": [
        {{
            "risque": "Description du risque",
            "probabilite": "faible / moyenne / elevee",
            "mitigation": "Comment l'eviter"
        }}
    ],
    "dette_technique_a_eviter": ["Pattern qui va causer des problemes"]
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_RECHERCHE, prompt, max_tokens=2500)
    return parser_json(reponse, {
        "stack_recommande": {},
        "risques_techniques": []
    }, "identifier_technologies")




def rechercher_donnees_marche(
    type_donnee: str,
    region: str = None,
    contexte: str = ""
) -> dict:
    """
    Recherche des donnees economiques actuelles via Tavily.

    DOIT etre appele AVANT estimer_couts_developpement.

    Parametres :
        type_donnee : Type de donnee a chercher. Valeurs acceptees :
                      "salaires_developpeurs"
                      "couts_hebergement"
                      "programmes_aide_startup"
                      "prix_logiciels_similaires"
                      "taux_freelance"
        region      : Region geographique (defaut : REGION de config.py)
        contexte    : Information supplementaire pour affiner la recherche

    Retourne : dict avec les donnees fetched et les sources citees
    """
    if region is None:
        region = REGION

    # Construire la requete selon le type de donnee
    requetes = {
        "salaires_developpeurs": f"salaire developpeur logiciel taux horaire salaire annuel junior senior {region} 2025 2026",
        "couts_hebergement":     f"cout hebergement cloud AWS Railway Fly.io startup mensuel 2025",
        "programmes_aide_startup": f"programmes aide financement startups technologie 2025",
        "prix_logiciels_similaires": f"prix abonnement SaaS logiciel {contexte} concurrent 2025",
        "taux_freelance":        f"taux horaire freelance developpeur independant 2025"
    }

    if type_donnee not in requetes:
        types_valides = list(requetes.keys())
        raise ValueError(
            f"type_donnee '{type_donnee}' invalide. "
            f"Valeurs acceptees : {types_valides}"
        )

    requete = requetes[type_donnee]
    resultats_web = recherche_tavily(requete, nb_resultats=5, region=region)
    contexte_web = formater_resultats_tavily(resultats_web, max_chars=400)

    # Prompts specialises selon le type de donnee
    if type_donnee == "salaires_developpeurs":
        prompt = f"""A partir des sources web ci-dessous, extrait les salaires et taux horaires
actuels des developpeurs en {region}.

{contexte_web}

Regles importantes :
- Les champs min, moyen et max sont des taux en CAD/heure.
- Si une source donne un salaire annuel, convertis en taux horaire avec salaire_annuel / 2080.
- Si la source ne distingue pas junior/intermediaire/senior, estime les profils a partir de la fourchette disponible et indique "estimation" dans la fiabilite.
- Ne copie jamais les valeurs d'exemple du schema.
- Ne retourne jamais 0 pour un salaire ou un taux. Utilise null si aucune donnee raisonnable n'est disponible.
- Cite les URLs utilisees dans "sources".

Reponds uniquement en JSON valide avec cette structure :
{{
    "region": "{region}",
    "source_donnees": "tavily_web",
    "profils": {{
        "dev_junior": {{
            "min": null, "moyen": null, "max": null,
            "salaire_annuel_moyen_cad": null,
            "experience": "0-2 ans",
            "source": "url ou estimation"
        }},
        "dev_intermediaire": {{
            "min": null, "moyen": null, "max": null,
            "salaire_annuel_moyen_cad": null,
            "experience": "2-5 ans",
            "source": "url ou estimation"
        }},
        "dev_senior": {{
            "min": null, "moyen": null, "max": null,
            "salaire_annuel_moyen_cad": null,
            "experience": "5+ ans",
            "source": "url ou estimation"
        }},
        "freelance_junior": {{
            "min": null, "moyen": null, "max": null,
            "note": "taux horaire freelance",
            "source": "url ou estimation"
        }},
        "freelance_senior": {{
            "min": null, "moyen": null, "max": null,
            "note": "taux horaire freelance senior",
            "source": "url ou estimation"
        }},
        "ai_engineer": {{
            "min": null, "moyen": null, "max": null,
            "salaire_annuel_moyen_cad": null,
            "note": "specialiste IA/ML",
            "source": "url ou estimation"
        }}
    }},
    "sources": ["url1", "url2"],
    "date_donnees": "2025-2026",
    "fiabilite": "haute / moyenne / estimation"
}}"""

    elif type_donnee == "couts_hebergement":
        prompt = f"""A partir des sources web ci-dessous, extrait les couts
d'hebergement cloud pour startups en {region}.

{contexte_web}

Reponds en JSON (montants en CAD/mois) :
{{
    "region": "{region}",
    "source_donnees": "tavily_web",
    "phases": {{
        "prototype": {{
            "total_mensuel_cad": 0,
            "description": "MVP 0-100 utilisateurs",
            "services_inclus": ["Serveur", "BDD", "Stockage"]
        }},
        "startup": {{
            "total_mensuel_cad": 0,
            "description": "100-1000 utilisateurs"
        }},
        "croissance": {{
            "total_mensuel_cad": 0,
            "description": "1000-10000 utilisateurs"
        }}
    }},
    "cout_llm_par_session_cad": 0.0,
    "sources": ["url1"],
    "fiabilite": "haute / moyenne / estimation"
}}"""

    elif type_donnee == "programmes_aide_startup":
        prompt = f"""A partir des sources web ci-dessous, liste les programmes
d'aide financiere pour startups tech en {region}.

{contexte_web}

Reponds en JSON :
{{
    "region": "{region}",
    "source_donnees": "tavily_web",
    "programmes": [
        {{
            "nom": "Nom du programme",
            "organisme": "Qui le gere",
            "aide_max_cad": 0,
            "type_aide": "Pret / Subvention / Credit impot / Garantie",
            "criteres": "Qui peut s'en prequalifier",
            "url": "site officiel"
        }}
    ],
    "sources": ["url1"],
    "date_verification": "2025-2026"
}}"""

    else:
        prompt = f"""A partir des sources web ci-dessous, extrait les donnees
de marche pertinentes pour : {type_donnee} en {region}.
Contexte supplementaire : {contexte}

{contexte_web}

Reponds en JSON avec les donnees trouvees, leurs sources, et leur fiabilite."""

    reponse = appel_llm(SYSTEM_PROMPT_RECHERCHE, prompt, max_tokens=2500)
    resultat = parser_json(reponse, {
        "region": region,
        "source_donnees": "tavily_web",
        "erreur": "parsing_echec"
    }, "rechercher_donnees_marche")

    if type_donnee == "salaires_developpeurs":
        resultat = _valider_salaires_developpeurs(resultat)

    # Ajouter les resultats bruts pour traçabilite
    resultat["_resultats_web_bruts"] = resultats_web
    return resultat
