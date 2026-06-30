import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import DOSSIER_ETAT, DOSSIER_PROJETS


def _slugifier(texte: str) -> str:
    """
    Transforme un texte quelconque en identifiant de fichier safe.
    
    La convention Python : une fonction qui commence par _ est "privee".
    Elle est utilisee uniquement dans ce fichier, pas importee ailleurs.
    """

    texte = texte.lower()

    texte = re.sub(r"[^a-z0-9]+", "_", texte)
    texte = texte.strip("_")
    return texte[:50]


def creer_etat_projet(description_projet: str, nom_projet: str = "") -> dict:
    """
    Cree un nouvel etat de projet vide.
    
    Remarque le nom_projet: str = "" : le nom est optionnel.
    Si vide, on genere automatiquement un nom depuis la description.
    """
    maintenant = datetime.now().isoformat()

    if not nom_projet:
        mots = description_projet.split()[:5]
        nom_projet = " ".join(mots)

    slug = _slugifier(nom_projet)

    etat = {
        "slug": slug,
        "nom_projet": nom_projet,
        "description_projet": description_projet,

        "date_creation": maintenant,
        "date_derniere_modification": maintenant,
        "statut": "en_cours",

        "etapes_completees": [],

        "analyses": {
            "recherche": None,
            "marche": None,
            "concurrents": None,
            "tendances": None,
            "couts_dev": None,
            "revenus": None,
            "break_even": None,
            "scenarios_financiers": None,
            "swot": None,
            "gtm": None,
            "risques_reglementaires": None,
            "score_viabilite": None
        },

        "documents_generes": [],

        "historique_messages": [],

         "config": {
            "prix_mensuel_cad": None,
            "public_cible": None,
            "secteur": None,
            "budget_marketing_mensuel_cad": 500.0,
            "type_donnees_collectees": []
        },
        
        "dossier_projet": str(DOSSIER_PROJETS / slug)
    }

    Path(etat["dossier_projet"]).mkdir(parents=True, exist_ok=True)

    return etat


def sauvegarder_etat(etat: dict) -> Path:
    """
    Sauvegarde l'etat dans un fichier JSON.
    Retourne le chemin du fichier cree.
    """

    etat["date_derniere_modification"] = datetime.now().isoformat()
    
    slug = etat.get("slug", "projet_inconnu")
    chemin = DOSSIER_ETAT / f"{slug}.json"


    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(
            etat,
            f,
            ensure_ascii=False,  
            indent=2,            
            default=str          
        )

    return chemin



def charger_etat(slug: str) -> Optional[dict]:
    """
    Charge l'etat d'un projet depuis son fichier JSON.
    Retourne None si le fichier n'existe pas.
    """
    chemin = DOSSIER_ETAT / f"{slug}.json"

    if not chemin.exists():
        return None  # Le projet n'existe pas

    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)
    


def lister_projets_existants() -> list:
    """
    Retourne une liste de tous les projets sauvegardes.
    Utile pour le menu de selection au demarrage.
    """
    projets = []

    for fichier in DOSSIER_ETAT.glob("*.json"):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                etat = json.load(f)
            
            projets.append({
                "slug": etat.get("slug", fichier.stem),
                "nom_projet": etat.get("nom_projet", "Sans nom"),
                "description_courte": etat.get("description_projet", "")[:80],
                "date_creation": etat.get("date_creation", "")[:10],
                "date_modification": etat.get("date_derniere_modification", "")[:10],
                "statut": etat.get("statut", "inconnu"),
                "nb_documents_generes": len(etat.get("documents_generes", [])),
                "etapes_completees": etat.get("etapes_completees", [])
            })
        except (json.JSONDecodeError, KeyError):
            pass

    projets.sort(key=lambda p: p["date_modification"], reverse=True)
    return projets






def marquer_etape_complete(etat: dict, etape: str) -> dict:
    """
    Marque une etape comme completee dans l'etat.
    
    Etapes valides :
        "recherche_initiale", "analyse_marche", "analyse_concurrents",
        "analyse_couts", "analyse_revenus", "analyse_break_even",
        "analyse_scenarios", "analyse_swot", "analyse_gtm",
        "analyse_risques", "score_viabilite", "generation_documents"
    """
    if etape not in etat["etapes_completees"]:
        etat["etapes_completees"].append(etape)
    return etat


def enregistrer_analyse(etat: dict, cle: str, resultat) -> dict:
    """
    Sauvegarde le resultat d'une analyse dans etat["analyses"].
    
    Exemple d'utilisation :
        etat = enregistrer_analyse(etat, "marche", {"tam": 500000000})
    """
    if "analyses" not in etat:
        etat["analyses"] = {}
    etat["analyses"][cle] = resultat
    return etat


def enregistrer_document(etat: dict, chemin_fichier: str, nb_lignes: int = 0) -> dict:
    """
    Enregistre un document genere dans l'historique.
    Evite les doublons si le meme fichier est ecrit deux fois.
    """
    if "documents_generes" not in etat:
        etat["documents_generes"] = []

    chemins_existants = [d.get("fichier") for d in etat["documents_generes"]]
    if chemin_fichier not in chemins_existants:
        etat["documents_generes"].append({
            "fichier": chemin_fichier,
            "date": datetime.now().isoformat(),
            "taille_lignes": nb_lignes
        })

    return etat


def ajouter_message_historique(etat: dict, role: str, contenu: str, max_messages: int = 50) -> dict:
    """
    Ajoute un message a l'historique conversationnel.
    Limite la taille pour eviter des fichiers JSON enormes.
    """
    if "historique_messages" not in etat:
        etat["historique_messages"] = []

    etat["historique_messages"].append({
        "role": role,
        "contenu": contenu[:2000],  # Tronquer les messages trop longs
        "timestamp": datetime.now().isoformat()
    })

    # Garder seulement les N derniers messages
    if len(etat["historique_messages"]) > max_messages:
        etat["historique_messages"] = etat["historique_messages"][-max_messages:]

    return etat


def get_analyse(etat: dict, cle: str):
    """
    Raccourci pour recuperer une analyse sauvegardee.
    Retourne None si pas encore faite.
    
    Utilisation :
        marche = get_analyse(etat, "marche")
        if marche is None:
            # Pas encore analyse
        else:
            # Utiliser les donnees
    """
    return etat.get("analyses", {}).get(cle)


def etape_completee(etat: dict, etape: str) -> bool:
    """
    Verifie si une etape a deja ete faite.
    Permet d'eviter de refaire une analyse qui a deja ete sauvegardee.
    """
    return etape in etat.get("etapes_completees", [])