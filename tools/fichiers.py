import os
from pathlib import Path
from config import DOSSIER_PROJETS
from ui import (
    afficher_apercu_fichier,
    afficher_confirmation_fichier,
    afficher_succes,
    afficher_erreur,
    afficher_info
)

def ecrire_fichier_markdown(
    nom_fichier: str,
    contenu: str,
    slug_projet: str,
    demander_confirmation: bool = False
) -> dict:
    """
    Ecrit un fichier Markdown dans le dossier du projet.
    Affiche un apercu et, si demande_confirmation=True, attend une confirmation
    interactive (uniquement pertinent en usage manuel — l'agent autonome
    n'attend jamais de confirmation, il n'y a personne pour y repondre).

    Les fichiers sont structures ainsi :
        projets_generes/
        └── <slug_projet>/
            ├── VISION.md
            ├── ANALYSE_MARCHE.md
            └── ...
    
    Retourne un dict avec le statut : "succes", "annule", ou "erreur"
    """
    # Construire le chemin complet
    dossier_projet = DOSSIER_PROJETS / slug_projet
    dossier_projet.mkdir(parents=True, exist_ok=True)
    # parents=True : cree tous les dossiers intermediaires si necessaire
    # exist_ok=True : ne plante pas si le dossier existe deja
    
    # Path(nom_fichier).name extrait juste le nom de fichier
    # Ex: "sous/dossier/VISION.md" -> "VISION.md"
    # Securite : empeche d'ecrire dans des dossiers non prevus (path traversal)
    nom_propre = Path(nom_fichier).name
    chemin = dossier_projet / nom_propre
    
    # Chemin lisible pour l'affichage
    try:
        chemin_affiche = str(chemin.relative_to(Path.cwd()))
    except ValueError:
        chemin_affiche = str(chemin)
    
    # Si le LLM a double-echappe les sauts de ligne (\n litteraux au lieu de vrais \n)
    if '\n' not in contenu and r'\n' in contenu:
        contenu = contenu.replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\"', '"')

    lignes = contenu.split("\n")
    nb_lignes = len(lignes)
    
    # Afficher l'apercu (les 25 premieres lignes)
    afficher_apercu_fichier(chemin_affiche, contenu, nb_lignes=25)
    
    # Demander confirmation si demande
    if demander_confirmation:
        confirme = afficher_confirmation_fichier(chemin_affiche, nb_lignes)
        if not confirme:
            afficher_info(f"Ecriture annulee : {nom_propre}")
            return {
                "statut": "annule",
                "fichier": str(chemin),
                "nom_fichier": nom_propre,
                "raison": "Annule par l'utilisateur"
            }
    
    # Ecriture du fichier
    try:
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        
        afficher_succes(f"Fichier ecrit : {chemin_affiche} ({nb_lignes} lignes)")
        
        return {
            "statut": "succes",
            "fichier": str(chemin),
            "nom_fichier": nom_propre,
            "chemin_relatif": chemin_affiche,
            "nb_lignes": nb_lignes,
            "taille_octets": len(contenu.encode("utf-8"))
        }
    
    except OSError as e:
        # OSError couvre les erreurs de systeme de fichiers :
        # permissions insuffisantes, disque plein, chemin invalide...
        afficher_erreur(f"Impossible d'ecrire {nom_propre}", str(e))
        return {
            "statut": "erreur",
            "fichier": str(chemin),
            "nom_fichier": nom_propre,
            "erreur": str(e)
        }



def lire_fichier(
    nom_fichier: str,
    slug_projet: str
) -> dict:
    """
    Lit le contenu d'un fichier deja genere.
    
    Utile pour :
    - Verifier ce qui a ete ecrit
    - Reprendre un contenu pour l'enrichir
    - Assembler le rapport final depuis les fichiers individuels
    """
    dossier_projet = DOSSIER_PROJETS / slug_projet
    chemin = dossier_projet / Path(nom_fichier).name
    
    if not chemin.exists():
        return {
            "statut": "non_trouve",
            "fichier": str(chemin),
            "contenu": None,
            "message": f"Le fichier {nom_fichier} n'existe pas pour {slug_projet}"
        }
    
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        lignes = contenu.split("\n")
        return {
            "statut": "succes",
            "fichier": str(chemin),
            "nom_fichier": Path(nom_fichier).name,
            "contenu": contenu,
            "nb_lignes": len(lignes),
            "taille_octets": chemin.stat().st_size,
            "premiere_ligne": lignes[0] if lignes else ""
        }
    
    except OSError as e:
        return {
            "statut": "erreur",
            "fichier": str(chemin),
            "contenu": None,
            "erreur": str(e)
        }
    


def lister_fichiers_projet(slug_projet: str) -> dict:
    """
    Liste tous les fichiers Markdown generes pour un projet.
    
    Appele en fin de session pour montrer le bilan a l'utilisateur.
    """
    dossier_projet = DOSSIER_PROJETS / slug_projet
    
    if not dossier_projet.exists():
        return {
            "statut": "vide",
            "dossier": str(dossier_projet),
            "fichiers": [],
            "message": f"Aucun fichier genere pour {slug_projet}"
        }
    
    fichiers = []
    taille_totale = 0
    
    # glob("*.md") = tous les fichiers .md dans le dossier
    # sorted() pour avoir un ordre alphabetique coherent
    for chemin in sorted(dossier_projet.glob("*.md")):
        taille = chemin.stat().st_size
        taille_totale += taille
        
        # Lire le titre depuis la premiere ligne (titre H1)
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                premiere_ligne = f.readline().strip()
        except OSError:
            premiere_ligne = ""
        
        fichiers.append({
            "nom": chemin.name,
            "chemin": str(chemin),
            "taille_octets": taille,
            # lstrip("#") enleve les # du debut, strip() les espaces
            "titre": premiere_ligne.lstrip("#").strip() if premiere_ligne.startswith("#") else chemin.stem
        })
    
    return {
        "statut": "succes",
        "dossier": str(dossier_projet),
        "nb_fichiers": len(fichiers),
        "taille_totale_octets": taille_totale,
        "fichiers": fichiers
    }