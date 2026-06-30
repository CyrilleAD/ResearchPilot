import os
import sys
from dotenv import load_dotenv

# Charger le .env en tout premier, avant les autres imports
# Ainsi, quand les modules s'importent et lisent os.getenv(...),
# les variables sont deja disponibles.
load_dotenv()

from config import DOSSIER_PROJETS
from state import (
    creer_etat_projet,
    charger_etat,
    lister_projets_existants,
    sauvegarder_etat
)
from ui import (
    afficher_bienvenue,
    afficher_succes,
    afficher_erreur,
    afficher_info,
    afficher_avertissement,
    afficher_separateur,
    afficher_liste_projets,
    afficher_resume_projet,
    afficher_score_viabilite,
    afficher_tableau_financier,
    console
)
from agent import executer_agent




def verifier_configuration() -> bool:
    """
    Verifie que tout est en place avant de lancer l'agent.
    
    Retourne True si OK, False si un probleme bloquant est detecte.
    Un avertissement (Tavily absent) n'est pas bloquant.
    """
    problemes_bloquants = []
    
    # 1. Cle OpenAI — sans ca, rien ne fonctionne
    if not os.getenv("OPENAI_API_KEY"):
        problemes_bloquants.append(
            "OPENAI_API_KEY manquante — ajoute ta cle dans le fichier .env"
        )
    
    # 2. Dossier de sortie — doit pouvoir etre cree
    try:
        DOSSIER_PROJETS.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        problemes_bloquants.append(
            f"Impossible de creer le dossier de sortie : {e}"
        )
    
    # Verifier chaque probleme bloquant
    if problemes_bloquants:
        afficher_separateur("Problemes de configuration detectes")
        for probleme in problemes_bloquants:
            afficher_erreur("Configuration", probleme)
        console.print(
            "\n  Corrige les problemes ci-dessus puis relance :\n"
            "  [bold]python main.py[/bold]\n"
        )
        return False
    
    # Avertissements non bloquants
    if not os.getenv("TAVILY_API_KEY"):
        afficher_avertissement(
            "TAVILY_API_KEY absente — la recherche web sera desactivee\n"
            "  Le programme fonctionnera avec les connaissances du LLM uniquement."
        )
    
    return True




def choisir_ou_creer_projet() -> tuple[str, dict]:
    """
    Affiche un menu pour choisir entre un nouveau projet ou reprendre un existant.
    
    Retourne :
        (description_projet, etat)
    """
    projets = lister_projets_existants()
    
    # Afficher la liste des projets existants si il y en a
    if projets:
        afficher_liste_projets(projets)
        console.print()
        console.print("  [dim]Tape un numero pour reprendre, ou[/dim] [bold]0[/bold] [dim]pour un nouveau projet[/dim]")
        
        choix = input("\n  Ton choix : ").strip()
        
        # Reprise d'un projet existant
        if choix.isdigit() and 1 <= int(choix) <= len(projets):
            projet_choisi = projets[int(choix) - 1]
            slug = projet_choisi["slug"]
            nom = projet_choisi["nom_projet"]

            etat = charger_etat(slug)
            if etat:
                description = etat.get("description_projet", nom)
                afficher_info(f"Reprise du projet : {nom}")
                return description, etat
            else:
                afficher_erreur("Chargement impossible", f"Fichier d'etat corrompu pour {slug}")
    
    # Nouveau projet
    afficher_separateur("Nouveau projet")
    console.print(
        "  Decris ton idee de projet. Sois precis : le public cible,\n"
        "  le probleme resolu, le modele de revenu si tu en as un.\n"
    )
    console.print("  [dim]Exemples :[/dim]")
    console.print("  [dim]- SaaS de gestion de rendez-vous pour salons de coiffure au Quebec[/dim]")
    console.print("  [dim]- Application mobile de suivi nutritionnel pour athletes amateur[/dim]")
    console.print("  [dim]- Plateforme B2B de facturation pour consultants independants[/dim]\n")
    
    description = ""
    while not description.strip():
        description = input("  Ton projet : ").strip()
        if not description:
            afficher_avertissement("La description ne peut pas etre vide.")
    
    # Nom court pour le slug
    console.print()
    console.print("  [dim]Donne un nom court a ce projet (2-4 mots) :[/dim]")
    nom = input("  Nom : ").strip()
    if not nom:
        nom = description[:40]
    
    etat = creer_etat_projet(description, nom)
    sauvegarder_etat(etat)
    
    afficher_succes(f"Projet cree : {etat['nom_projet']} (slug : {etat['slug']})")
    return description, etat





def afficher_bilan_final(etat: dict):
    """
    Affiche le resume complet du projet apres l'execution de l'agent.
    """
    afficher_separateur("Bilan de l'analyse")
    afficher_resume_projet(etat)
    
    # Score de viabilite si calcule
    score_data = etat.get("analyses", {}).get("score_viabilite")
    if score_data:
        afficher_score_viabilite(score_data)
    
    # Projections financieres si disponibles
    scenarios = etat.get("analyses", {}).get("scenarios_financiers")
    if scenarios:
        afficher_tableau_financier(scenarios)
    
    # Liste des fichiers generes
    fichiers = etat.get("documents_generes", [])
    if fichiers:
        afficher_separateur("Fichiers generes")
        for doc in fichiers:
            console.print(f"  [green]✓[/green] {doc.get('fichier', '')}")
        
        # Dossier de sortie
        slug = etat.get("slug", "")
        if slug:
            dossier = DOSSIER_PROJETS / slug
            console.print(f"\n  [cyan]Dossier complet :[/cyan] {dossier}")
    else:
        afficher_info("Aucun fichier genere dans cette session.")
    
    afficher_separateur()





def main():
    """
    Point d'entree de ResearchPilot.
    
    Ordre d'execution :
    1. Afficher le titre
    2. Verifier la configuration
    3. Choisir le projet
    4. Lancer l'agent
    5. Afficher le bilan
    """
    afficher_bienvenue()
    
    # Etape 1 : Configuration
    if not verifier_configuration():
        sys.exit(1)
    # sys.exit(1) : code de sortie 1 = erreur (convention Unix)
    # Les scripts qui appelleraient main.py sauront qu'il y a eu un probleme
    
    # Etape 2 : Choisir le projet
    description_projet, etat = choisir_ou_creer_projet()
    
    # Etape 3 : Lancer l'agent
    afficher_separateur("Lancement de l'analyse")
    
    try:
        etat = executer_agent(description_projet, etat)
    
    except KeyboardInterrupt:
        # L'utilisateur a appuye sur Ctrl+C
        console.print("\n\n  [yellow]Analyse interrompue par l'utilisateur[/yellow]")
        etat["statut"] = "interrompu"
        sauvegarder_etat(etat)
        afficher_info("L'etat du projet est sauvegarde. Relance pour continuer.")
        sys.exit(0)
    
    except Exception as e:
        afficher_erreur("Erreur inattendue", str(e))
        sauvegarder_etat(etat)
        sys.exit(1)
    
    # Etape 4 : Bilan final
    afficher_bilan_final(etat)


# Ce bloc s'execute SEULEMENT si on lance ce fichier directement :
#   python main.py    -> s'execute
#   import main       -> ne s'execute PAS
#
# C'est une convention Python fondamentale. Sans ce bloc, un simple
# "import main" dans un test ou un autre fichier lancerait le programme entier.
if __name__ == "__main__":
    main()