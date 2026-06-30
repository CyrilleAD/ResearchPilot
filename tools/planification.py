import json
import re
from config import TEMPERATURE_GENERATION, TEMPERATURE_MERMAID
from tools.base import appel_llm, parser_json


def _nettoyer_mermaid(texte: str) -> str:
    """
    Retire les blocs de code markdown autour du Mermaid.
    
    Le LLM entoure souvent sa reponse de ```mermaid ... ```
    meme si on lui demande de ne pas le faire.
    On nettoie en Python — plus fiable que d'esperer que le LLM obeisse.
    """
    texte = texte.strip()
    if texte.startswith("```mermaid"):
        texte = texte[10:]  # Enlever ```mermaid (10 caracteres)
    elif texte.startswith("```"):
        texte = texte[3:]   # Enlever ``` (3 caracteres)
    
    if texte.endswith("```"):
        texte = texte[:-3]  # Enlever les ``` de fin
    
    return texte.strip()





def definir_vision_projet(
    description_projet: str,
    public_cible: str,
    probleme_resolu: str,
    secteur: str = "technologie"
) -> dict:
    """
    Definit la vision strategique, la mission et les objectifs SMART.
    
    Vision = ou on veut aller dans 5 ans
    Mission = ce qu'on fait concretement chaque jour
    SMART = Specifique, Mesurable, Atteignable, Realiste, Temporel
    """
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Definis la vision strategique complete de ce projet.

Description : {description_projet}
Public cible : {public_cible}
Probleme resolu : {probleme_resolu}
Secteur : {secteur}
Marche : Quebec, Canada

Reponds en JSON :
{{
    "nom_produit_suggere": "Nom court et memorisable",
    "tagline": "Phrase d'accroche en francais (max 10 mots)",
    "vision": "Ou voulons-nous aller dans 5 ans ? (1-2 phrases)",
    "mission": "Ce qu'on fait concretement (1-2 phrases)",
    "proposition_de_valeur": "En quoi sommes-nous differents ? (1 phrase)",
    "objectifs_smart": [
        {{
            "objectif": "Description",
            "specifique": "Qu'est-ce qu'on veut exactement ?",
            "mesurable": "Comment mesurer le succes ?",
            "atteignable": "Pourquoi c'est atteignable ?",
            "realiste": "Est-ce realiste avec nos ressources ?",
            "temporel": "D'ici quand ?",
            "kpi": "Indicateur cle (ex: 100 clients payants)"
        }}
    ],
    "valeurs_fondamentales": [
        {{
            "valeur": "Nom de la valeur",
            "comment_on_la_vit": "Comment elle se manifeste dans le produit"
        }}
    ],
    "anti_vision": "Ce qu'on NE veut PAS devenir",
    "indicateur_succes_18_mois": "Un seul chiffre qui prouvera le succes"
}}"""

    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "nom_produit_suggere": "Projet",
        "vision": description_projet,
        "objectifs_smart": []
    })




def creer_personas(
    description_projet: str,
    analyse_besoins: dict
) -> dict:
    """
    Affine les personas avec parcours d'achat et objections.
    
    La difference avec analyser_besoins_utilisateurs du chapitre 05 :
    - analyser_besoins_utilisateurs -> recherche initiale, pain points
    - creer_personas -> profils detailles avec psychologie d'achat
    """
    personas_bruts = analyse_besoins.get("personas", [])
    segment = analyse_besoins.get("segment_le_plus_prometteur", {})
    
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Affine et complete ces personas pour le projet.

Projet : {description_projet}
Personas identifies : {json.dumps(personas_bruts, ensure_ascii=False)[:1500]}
Segment prioritaire : {json.dumps(segment, ensure_ascii=False)}

Ajoute pour chaque persona :
- Le parcours d'achat (comment il va decouvrir et acheter)
- Les objections (pourquoi il NE voudrait PAS acheter)
- Les canaux de contact (LinkedIn, groupes Facebook Quebec, evenements)

Reponds en JSON :
{{
    "persona_principal": {{
        "nom": "Prenom + titre",
        "description": "2-3 phrases",
        "quote_typique": "Ce qu'il dirait apres utilisation",
        "parcours_achat": [
            {{
                "etape": "Prise de conscience",
                "description": "Comment il decouvre le probleme",
                "notre_role": "Comment etre present a cette etape"
            }}
        ],
        "objections": [
            {{
                "objection": "Raison de ne pas acheter",
                "reponse": "Notre contre-argument"
            }}
        ],
        "canaux": ["LinkedIn", "Groupe Facebook PME Quebec", "etc."]
    }},
    "personas_secondaires": [
        {{
            "nom": "Prenom + titre",
            "relation_persona_principal": "Son role dans la decision d'achat",
            "priorite": "influenceur / decideur / utilisateur final"
        }}
    ],
    "anti_persona": {{
        "profil": "Qui on NE cible PAS",
        "pourquoi": "Pourquoi ce n'est pas notre client ideal",
        "risque_si_on_les_cible": "Ce qui arrive si on essaie de les satisfaire"
    }}
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "persona_principal": {},
        "personas_secondaires": []
    })



def planifier_fonctionnalites(
    description_projet: str,
    analyse_besoins: dict,
    solutions_existantes: dict
) -> dict:
    """
    Classe les fonctionnalites avec la methode MoSCoW et definit le MVP.
    
    Must Have  = Sans ca, le produit ne fonctionne pas
    Should Have = Important mais lancement possible sans
    Could Have  = Nice-to-have pour V2+
    Won't Have  = Hors scope maintenant
    
    MVP = Minimum Viable Product : la version la PLUS SIMPLE qui prouve
    que l'idee fonctionne. Un MVP peut etre livre en 2-4 semaines.
    """
    lacunes = solutions_existantes.get("lacunes_identifiees", [])
    jobs = analyse_besoins.get("jobs_to_be_done", [])
    
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Classe les fonctionnalites avec la methode MoSCoW.

Projet : {description_projet}
Lacunes du marche a adresser : {json.dumps(lacunes, ensure_ascii=False)}
Jobs-to-be-done principaux : {json.dumps(jobs[:3], ensure_ascii=False)}

REGLE MVP : La version la PLUS SIMPLE qui prouve que l'idee fonctionne.
Un MVP peut etre livre en 2-4 semaines par un dev solo.
Pense "enlever" pas "ajouter".

Reponds en JSON :
{{
    "mvp_description": "Ce que fait le MVP en 1 phrase simple",
    "must_have": [
        {{
            "fonctionnalite": "Nom court",
            "description": "Ce que ca fait concretement",
            "user_story": "En tant que [persona], je veux [action] pour [benefice]",
            "critere_acceptance": "Comment savoir que c'est fait ?",
            "effort_dev_jours": 0,
            "pourquoi_indispensable": "Raison"
        }}
    ],
    "should_have": [
        {{
            "fonctionnalite": "Nom",
            "description": "Ce que ca fait",
            "user_story": "En tant que...",
            "effort_dev_jours": 0,
            "version_cible": "V1.1 / V2"
        }}
    ],
    "could_have": [
        {{
            "fonctionnalite": "Nom",
            "description": "Ce que ca fait",
            "version_cible": "V2 / V3"
        }}
    ],
    "wont_have": [
        {{
            "fonctionnalite": "Nom",
            "pourquoi_exclus": "Raison concrete"
        }}
    ],
    "effort_total_mvp_jours": 0,
    "temps_estimatif_mvp": "X semaines avec 1 dev"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "mvp_description": "MVP non defini",
        "must_have": [],
        "should_have": []
    })




def concevoir_architecture(
    description_projet: str,
    fonctionnalites: dict,
    technologies: dict
) -> dict:
    """
    Conçoit l'architecture technique du projet.
    
    L'architecture definit comment les composants s'organisent.
    Principe : chaque composant a une seule responsabilite.
    """
    must_have = fonctionnalites.get("must_have", [])
    stack = technologies.get("stack_recommande", {})
    
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Conçois l'architecture technique pour ce projet.

Projet : {description_projet}
Fonctionnalites MVP : {json.dumps([f.get("fonctionnalite","") for f in must_have], ensure_ascii=False)}
Stack technique : {json.dumps(stack, ensure_ascii=False)[:800]}

Reponds en JSON :
{{
    "type_architecture": "Monolithique / Microservices / Serverless / Hybride",
    "justification_choix": "Pourquoi cette architecture pour ce contexte",
    "composants_principaux": [
        {{
            "nom": "Nom du composant",
            "responsabilite": "Ce qu'il fait (une seule chose)",
            "technologie": "Technologie utilisee",
            "interactions": ["Avec quels autres composants"]
        }}
    ],
    "flux_donnees_principal": [
        {{
            "etape": 1,
            "de": "Composant source",
            "vers": "Composant destination",
            "donnee": "Quelle donnee circule",
            "protocol": "HTTP / WebSocket / Queue"
        }}
    ],
    "schema_base_donnees_principal": [
        {{
            "table": "Nom de la table",
            "champs_cles": ["champ1 (type)", "champ2 (type)"],
            "relations": ["table_liee via cle etrangere"]
        }}
    ],
    "securite": {{
        "authentification": "Methode et pourquoi",
        "autorisation": "Gestion des permissions",
        "donnees_sensibles": "Comment elles sont protegees",
        "conformite_loi25": "Mesures de conformite technique"
    }},
    "scalabilite": "Comment l'architecture peut grossir sans refonte"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {
        "type_architecture": "Non defini",
        "composants_principaux": []
    })




def planifier_roadmap(
    description_projet: str,
    fonctionnalites: dict,
    couts_dev: dict
) -> dict:
    """Cree le planning de developpement en phases incrementales."""
    duree_mvp = fonctionnalites.get("temps_estimatif_mvp", "4 semaines")
    budget = couts_dev.get("budget_total_cad", {}).get("scenario_realiste", 0)
    
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Cree la roadmap de developpement pour ce projet.

Projet : {description_projet}
Duree estimee MVP : {duree_mvp}
Budget total realiste : {budget}$ CAD

CONTRAINTES : Equipe 1-2 personnes, livrer vite, valider avec vrais utilisateurs.
Pas de big-bang — phases incrementales uniquement.

Reponds en JSON :
{{
    "phases": [
        {{
            "numero": 1,
            "nom": "Phase 1 — MVP",
            "objectif": "Ce qu'on veut valider",
            "duree_semaines": 0,
            "delivrables": ["Ce qu'on livre a la fin"],
            "criteres_succes": ["Ce qui prouve que la phase est reussie"],
            "fonctionnalites_incluses": ["Fonctionnalite 1"],
            "risques_principaux": ["Risque 1"],
            "milestone": "Evenement qui marque la fin"
        }}
    ],
    "jalons_cles": [
        {{
            "jalon": "Nom du jalon",
            "description": "Ce qui se passe",
            "semaine_estimee": 0,
            "critere_validation": "Comment valider"
        }}
    ],
    "hypotheses_a_valider_phase1": ["Hypothese critique a valider avant d'investir"],
    "budget_par_phase": [
        {{
            "phase": 1,
            "budget_cad": 0,
            "repartition": "Dev: X$ / Infra: Y$ / Marketing: Z$"
        }}
    ]
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {"phases": [], "jalons_cles": []})





def decomposer_en_taches(
    fonctionnalites_mvp: list,
    architecture: dict
) -> dict:
    """
    Decompose les fonctionnalites en taches de developpement concretes.
    
    Regle : une tache = 0.5 a 2 jours de travail max.
    Si une tache est plus longue, la decomposer.
    """
    fonc_str = json.dumps(fonctionnalites_mvp[:5], ensure_ascii=False)
    composants = [c.get("nom", "") for c in architecture.get("composants_principaux", [])]
    
    from prompts import SYSTEM_PROMPT_GENERATION
    prompt = f"""Decompose ces fonctionnalites en taches de developpement.

Fonctionnalites MVP : {fonc_str}
Composants architecture : {json.dumps(composants, ensure_ascii=False)}

REGLE : Une tache = 0.5 a 2 jours de travail max.

Reponds en JSON :
{{
    "sprints": [
        {{
            "numero": 1,
            "nom": "Sprint 1 — Infrastructure",
            "duree_jours": 0,
            "taches": [
                {{
                    "id": "T001",
                    "titre": "Titre court",
                    "description": "Ce qu'il faut faire exactement",
                    "composant": "Composant concerne",
                    "effort_demi_journees": 1,
                    "dependances": ["T000"],
                    "critere_done": "Tests passes + revue + deploye en staging",
                    "type": "backend / frontend / devops / test / doc"
                }}
            ]
        }}
    ],
    "taches_techniques_transversales": [
        {{
            "id": "TT001",
            "titre": "Configuration CI/CD",
            "description": "Pipeline de deploiement automatique",
            "effort_demi_journees": 2,
            "quand": "Debut du projet"
        }}
    ],
    "definition_of_done_globale": "Criteres qui s'appliquent a TOUTES les taches"
}}"""
    
    reponse = appel_llm(SYSTEM_PROMPT_GENERATION, prompt, max_tokens=3000)
    return parser_json(reponse, {"sprints": [], "taches_techniques_transversales": []})





def generer_diagrammes_mermaid(
    architecture: dict,
    flux_donnees: list = None,
    roadmap: dict = None,
    **_kwargs
) -> dict:
    """
    Genere 3 diagrammes Mermaid : architecture, sequence, gantt.
    
    Points importants :
    - temperature=TEMPERATURE_MERMAID (0.2) pour la syntaxe stricte
    - _nettoyer_mermaid() pour retirer les backticks que le LLM ajoute
    - system prompt tres strict avec exemples et regles
    """
    from prompts import SYSTEM_PROMPT_MERMAID
    
    flux_donnees = flux_donnees or []
    roadmap = roadmap or {}
    composants = architecture.get("composants_principaux", [])
    phases = roadmap.get("phases", [])
    
    # --- Diagramme 1 : Architecture (graph TD) ---
    composants_str = json.dumps(
        [{"nom": c.get("nom",""), "interactions": c.get("interactions",[])}
         for c in composants],
        ensure_ascii=False
    )
    
    prompt_archi = f"""Genere un diagramme Mermaid "graph TD" pour cette architecture.

Composants : {composants_str}

REGLES ABSOLUES — syntaxe brute uniquement, SANS backticks :
- Commence directement par "graph TD"
- Labels avec espaces entre guillemets : A["Mon Composant"]
- Pas de parentheses, < > & # @ dans les labels
- Exemple valide :
graph TD
    A["Utilisateur"] --> B["API Backend"]
    B --> C["Base de Donnees"]"""
    
    diag_archi_raw = appel_llm(SYSTEM_PROMPT_MERMAID, prompt_archi, temperature=TEMPERATURE_MERMAID, max_tokens=800)
    diag_archi = _nettoyer_mermaid(diag_archi_raw)
    
    # --- Diagramme 2 : Sequence ---
    flux_str = json.dumps(flux_donnees[:5], ensure_ascii=False) if flux_donnees else "[]"
    
    prompt_seq = f"""Genere un diagramme Mermaid "sequenceDiagram" pour ce flux.

Flux : {flux_str}

REGLES ABSOLUES — syntaxe brute, SANS backticks :
- Commence par "sequenceDiagram"
- participant A as "Nom Affiche"
- A->>B: Message
- Pas de parentheses dans les messages, max 6 acteurs

Exemple :
sequenceDiagram
    participant U as "Utilisateur"
    participant A as "Agent IA"
    U->>A: Soumet le projet
    A->>A: Analyse la demande
    A->>U: Retourne le plan"""
    
    diag_seq_raw = appel_llm(SYSTEM_PROMPT_MERMAID, prompt_seq, temperature=TEMPERATURE_MERMAID, max_tokens=700)
    diag_seq = _nettoyer_mermaid(diag_seq_raw)
    
    # --- Diagramme 3 : Gantt ---
    phases_str = json.dumps(
        [{"nom": p.get("nom",""), "semaines": p.get("duree_semaines",2)} for p in phases[:4]],
        ensure_ascii=False
    )
    
    prompt_gantt = f"""Genere un diagramme Mermaid "gantt" pour ce planning.

Phases : {phases_str}

REGLES ABSOLUES — syntaxe brute, SANS backticks :
- Commence par "gantt"
- dateFormat YYYY-MM-DD
- Pas d'accents dans les titres de section

Exemple :
gantt
    title Roadmap du Projet
    dateFormat YYYY-MM-DD
    section Phase 1 MVP
        Infrastructure : active, 2025-01-01, 14d
        Core : 2025-01-15, 21d"""
    
    diag_gantt_raw = appel_llm(SYSTEM_PROMPT_MERMAID, prompt_gantt, temperature=TEMPERATURE_MERMAID, max_tokens=700)
    diag_gantt = _nettoyer_mermaid(diag_gantt_raw)
    
    return {
        "architecture": {
            "type": "graph TD",
            "code": diag_archi,
            "description": "Architecture technique du projet"
        },
        "sequence": {
            "type": "sequenceDiagram",
            "code": diag_seq,
            "description": "Flux principal d'utilisation"
        },
        "gantt": {
            "type": "gantt",
            "code": diag_gantt,
            "description": "Planning de developpement"
        }
    }