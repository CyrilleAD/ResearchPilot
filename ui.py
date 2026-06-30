from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box
from datetime import datetime


console = Console()

def afficher_bienvenue():
    """Affiche l'ecran de bienvenue au demarrage de ResearchPilot."""
    console.print()
    console.print(Panel(
        Text.assemble(
            ("ResearchPilot", "bold cyan"),
            (" v1.0\n\n", "dim"),
            ("Agent IA de creation de projets technologiques\n", "white"),
            ("Marche cible : Quebec, Canada\n\n", "dim"),
            ("Analyse de marche  |  Finance  |  Strategie  |  Documentation", "dim cyan")
        ),
        title="[bold blue]Bienvenue[/bold blue]",
        border_style="blue",
        padding=(1, 4)
    ))
    console.print()


def afficher_iteration(iteration: int, max_iterations: int, message: str = ""):
    """
    Affiche une ligne de statut pour chaque iteration de la boucle agentique.

    Les : int et : str apres les parametres sont des "type hints".
    Ils n'ont aucun effet sur l'execution mais documentent ce qu'on attend.
    iteration : int = on attend un nombre entier
    message : str = "" = on attend une chaine, vide par defaut
    """
    # Calculer le pourcentage d'avancement
    pourcentage = int((iteration / max_iterations) * 100)

    # Construire la barre de progression manuellement
    # 20 caracteres au total
    # "#" pour les cases "faites", "." pour les cases "restantes"
    barre = "[" + "#" * (pourcentage // 5) + "." * (20 - pourcentage // 5) + "]"

    if message:
        console.print(
            f"  [dim]Iteration {iteration:02d}/{max_iterations}[/dim] "
            f"[cyan]{barre}[/cyan] "
            f"[white]{message}[/white]"
        )
    else:
        console.print(
            f"  [dim]Iteration {iteration:02d}/{max_iterations}[/dim] "
            f"[cyan]{barre}[/cyan]"
        )



def afficher_pensee_agent(pensee: str):
    """
    Affiche le raisonnement de l'agent avant qu'il agisse.
    C'est le "R" de ReAct (Reasoning).
    """
    # On verifie qu'il y a vraiment quelque chose a afficher
    if pensee and len(pensee) > 10:
        # Tronquer si trop long (evite d'inonder le terminal)
        texte_court = pensee[:200] + ("..." if len(pensee) > 200 else "")
        console.print(
            Panel(
                f"[italic dim]{texte_court}[/italic dim]",
                title="[dim]Raisonnement de l'agent[/dim]",
                border_style="dim",
                padding=(0, 2)
            )
        )



def afficher_appel_outil(nom_outil: str, arguments: dict):
    """
    Affiche quel outil l'agent va utiliser et avec quels arguments.
    """
    # Icones textuelles par categorie (pour eviter les emojis)
    icones = {
        "recherche": "[blue]recherche[/blue]",
        "analyser": "[magenta]analyse[/magenta]",
        "calculer": "[yellow]calcul[/yellow]",
        "projeter": "[yellow]projection[/yellow]",
        "modeliser": "[yellow]modelisation[/yellow]",
        "generer": "[green]generation[/green]",
        "concevoir": "[cyan]conception[/cyan]",
        "identifier": "[blue]identification[/blue]",
        "evaluer": "[magenta]evaluation[/magenta]",
        "ecrire": "[red]ecriture fichier[/red]",
        "lire": "[dim]lecture[/dim]",
        "lister": "[dim]listing[/dim]",
        "estimer": "[yellow]estimation[/yellow]",
    }

    # Trouver la categorie de l'outil en regardant son debut
    # ex: "analyser_marche_quebec" commence par "analyser" -> categorie "analyse"
    categorie = next(
        (icones[k] for k in icones if nom_outil.startswith(k)),
        "[white]outil[/white]"
    )
    # next() retourne le premier element qui satisfait la condition
    # le deuxieme argument est la valeur par defaut si rien ne satisfait

    # Construire les lignes a afficher
    lignes = [f"[bold cyan]{nom_outil}[/bold cyan]"]
    for cle, valeur in arguments.items():
        # Formater la valeur selon son type
        if isinstance(valeur, (dict, list)):
            valeur_str = f"({type(valeur).__name__} avec {len(valeur)} elements)"
        elif isinstance(valeur, str) and len(valeur) > 60:
            valeur_str = valeur[:60] + "..."
        else:
            valeur_str = str(valeur)
        lignes.append(f"  [dim]{cle}[/dim] : [white]{valeur_str}[/white]")

    console.print(Panel(
        "\n".join(lignes),
        title=f"[dim]Appel outil — {categorie}[/dim]",
        border_style="cyan",
        padding=(0, 2)
    ))




def afficher_resultat_outil(nom_outil: str, resultat, succes: bool = True):
    """
    Affiche un resume du resultat retourne par un outil.
    On n'affiche pas tout (ca peut etre enorme), juste un apercu.
    """
    if not succes:
        console.print(f"  [red]Erreur dans {nom_outil}[/red]")
        return

    if isinstance(resultat, dict):
        nb_cles = len(resultat)
        resume = f"dict avec {nb_cles} cles"
        # Montrer les 3 premieres cles
        cles = list(resultat.keys())[:3]
        resume += f" : {', '.join(cles)}"
        if nb_cles > 3:
            resume += f" + {nb_cles - 3} autres"
    elif isinstance(resultat, list):
        resume = f"liste de {len(resultat)} elements"
    elif isinstance(resultat, str):
        resume = resultat[:100] + ("..." if len(resultat) > 100 else "")
    else:
        resume = str(resultat)[:80]

    console.print(f"  [green]Resultat[/green] [dim]({nom_outil})[/dim] : {resume}")





def afficher_apercu_fichier(chemin: str, contenu: str, nb_lignes: int = 20):
    """
    Affiche un apercu des premieres lignes d'un fichier avec coloration.
    Appele avant de demander la confirmation d'ecriture.
    """
    lignes = contenu.split("\n")
    apercu = "\n".join(lignes[:nb_lignes])
    if len(lignes) > nb_lignes:
        apercu += f"\n\n... ({len(lignes) - nb_lignes} lignes supplementaires)"

    console.print(Panel(
        Syntax(apercu, "markdown", theme="monokai", word_wrap=True),
        title=f"[green]Apercu : {chemin}[/green]",
        border_style="green",
        padding=(0, 1)
    ))




def afficher_confirmation_fichier(chemin: str, taille_lignes: int) -> bool:
    """
    Demande confirmation avant d'ecrire un fichier.
    C'est le Human-in-the-Loop pattern : on ne fait pas d'action
    irreversible sans l'approbation de l'utilisateur.

    Retourne True si confirme, False si refuse.
    """
    console.print()
    console.print(Panel(
        f"[yellow]L'agent souhaite ecrire le fichier suivant :[/yellow]\n\n"
        f"  [bold]{chemin}[/bold]\n"
        f"  [dim]Taille approximative : {taille_lignes} lignes[/dim]",
        title="[yellow]Confirmation requise[/yellow]",
        border_style="yellow",
        padding=(0, 2)
    ))

    reponse = console.input(
        "  [yellow]Confirmer l'ecriture ? ([bold]o[/bold]/n) : [/yellow]"
    ).strip().lower()

    # On accepte plusieurs formes de "oui"
    # La chaine vide = l'utilisateur a appuye Entree sans rien taper = oui par defaut
    return reponse in ("", "o", "oui", "y", "yes")




def afficher_separateur(titre: str = ""):
    """Ligne horizontale avec titre optionnel."""
    if titre:
        console.print(Rule(f"[dim]{titre}[/dim]", style="dim"))
    else:
        console.print(Rule(style="dim"))


def afficher_erreur(message: str, detail: str = ""):
    """Message d'erreur mis en forme."""
    contenu = f"[red]{message}[/red]"
    if detail:
        contenu += f"\n\n[dim]{detail}[/dim]"
    console.print(Panel(contenu, title="[red]Erreur[/red]", border_style="red"))


def afficher_succes(message: str):
    """Message de succes."""
    console.print(f"  [green]{message}[/green]")


def afficher_info(message: str):
    """Information neutre."""
    console.print(f"  [cyan]{message}[/cyan]")


def afficher_avertissement(message: str):
    """Avertissement."""
    console.print(f"  [yellow]Attention : {message}[/yellow]")





def afficher_liste_projets(projets: list):
    """Affiche la liste des projets existants en tableau."""
    if not projets:
        console.print("  [dim]Aucun projet existant.[/dim]")
        return

    table = Table(
        title="Projets Existants",
        box=box.ROUNDED,
        header_style="bold cyan"
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Nom du Projet", style="white", width=30)
    table.add_column("Date Creation", style="dim", width=20)
    table.add_column("Statut", style="yellow", width=15)
    table.add_column("Documents", justify="right", style="cyan", width=10)

    for i, projet in enumerate(projets, 1):
        table.add_row(
            str(i),
            projet.get("nom_projet", "Sans nom")[:28],
            projet.get("date_creation", "Inconnue")[:18],
            projet.get("statut", "inconnu"),
            str(projet.get("nb_documents_generes", 0))
        )

    console.print(table)


def afficher_score_viabilite(score_data: dict):
    """Affiche le score de viabilite avec une visualisation."""
    score = score_data.get("score_global", 0)
    verdict = score_data.get("verdict", "INCONNU")
    action = score_data.get("action_recommandee", "")

    # Choisir la couleur selon le score
    if score >= 75:
        style_score = "bold green"
        barre_car = "#"
    elif score >= 60:
        style_score = "bold yellow"
        barre_car = "#"
    elif score >= 45:
        style_score = "bold orange3"
        barre_car = "="
    else:
        style_score = "bold red"
        barre_car = "-"

    nb_barres = score // 5
    barre = barre_car * nb_barres + "." * (20 - nb_barres)

    console.print()
    console.print(Panel(
        Text.assemble(
            (f"Score de Viabilite : {score}/100\n", style_score),
            (f"[{barre}]\n\n", "cyan"),
            (f"Verdict : {verdict}\n\n", style_score),
            (f"{action}", "white")
        ),
        title="[bold]Evaluation Finale du Projet[/bold]",
        border_style="blue",
        padding=(1, 4)
    ))

    # Tableau des 6 dimensions
    detail = score_data.get("detail_calcul_score", {})
    if detail:
        table = Table(
            title="Detail par Dimension",
            box=box.SIMPLE,
            header_style="bold"
        )
        table.add_column("Dimension", style="white", width=30)
        table.add_column("Score", justify="right", width=10)
        table.add_column("Poids", justify="right", width=10)
        table.add_column("Contribution", justify="right", width=15)

        for dim, val in detail.items():
            score_dim = val.get("score", 0)
            # Colorer le score selon sa valeur
            if score_dim >= 70:
                style_dim = "green"
            elif score_dim >= 50:
                style_dim = "yellow"
            else:
                style_dim = "red"

            table.add_row(
                dim.replace("_", " ").title(),
                f"[{style_dim}]{score_dim}/100[/{style_dim}]",
                f"{val.get('poids_pct', 0)}%",
                f"{val.get('contribution', 0):.1f} pts"
            )

        console.print(table)


def afficher_tableau_financier(scenarios: dict):
    """Affiche les 3 scenarios financiers en tableau comparatif."""
    table = Table(
        title="Scenarios Financiers (24 mois)",
        box=box.DOUBLE_EDGE,
        header_style="bold cyan"
    )
    table.add_column("Metrique", style="white", width=35)
    table.add_column("Optimiste", justify="right", style="green", width=18)
    table.add_column("Realiste", justify="right", style="yellow", width=18)
    table.add_column("Pessimiste", justify="right", style="red", width=18)

    def fmt_cad(v):
        """Formater un nombre en dollars canadiens."""
        if isinstance(v, (int, float)):
            return f"{v:,.0f} $"
        return str(v)

    metriques = [
        ("MRR Final", "mrr_final_cad"),
        ("ARR Projete", "arr_projete_cad"),
        ("Clients Finaux", "clients_finaux"),
        ("Break-even (mois)", "mois_break_even"),
        ("Profit Net 24 mois", "profit_net_fin_periode_cad"),
        ("Revenu Total 24 mois", "revenu_total_periode_cad"),
    ]

    for label, cle in metriques:
        opt = scenarios.get("scenario_optimiste", {}).get(cle, "N/A")
        real = scenarios.get("scenario_realiste", {}).get(cle, "N/A")
        pess = scenarios.get("scenario_pessimiste", {}).get(cle, "N/A")

        # Ne pas formater en CAD les colonnes qui sont des mois ou des clients
        if cle not in ("mois_break_even", "clients_finaux"):
            opt = fmt_cad(opt)
            real = fmt_cad(real)
            pess = fmt_cad(pess)

        table.add_row(label, str(opt), str(real), str(pess))

    console.print(table)


def afficher_resume_projet(etat: dict):
    """Affiche un resume de l'etat d'un projet."""
    nom = etat.get("nom_projet", "Sans nom")
    statut = etat.get("statut", "inconnu")
    docs = etat.get("documents_generes", [])
    analyses = [v for v in etat.get("analyses", {}).values() if v is not None]

    table = Table(
        title=f"Projet : {nom}",
        box=box.SIMPLE,
        show_header=False
    )
    table.add_column("Cle", style="dim", width=25)
    table.add_column("Valeur", style="white", width=40)

    table.add_row("Statut", statut)
    table.add_row("Documents generes", str(len(docs)))
    table.add_row("Analyses completees", str(len(analyses)))

    if docs:
        table.add_row(
            "Fichiers crees",
            "\n".join([d.get("fichier", "") for d in docs[:5]])
        )

    console.print(table)


def afficher_tableau_recherche(resultats: list, titre: str = "Resultats de recherche"):
    """Affiche les resultats Tavily en tableau."""
    if not resultats:
        console.print("  [dim]Aucun resultat de recherche web disponible[/dim]")
        return

    table = Table(
        title=titre,
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan"
    )
    table.add_column("Source", style="dim", width=30)
    table.add_column("Titre", style="white", width=40)
    table.add_column("Apercu", style="dim", width=50)

    for r in resultats[:5]:
        url = r.get("url", "")
        if len(url) > 28:
            url = url[:25] + "..."
        titre_res = r.get("title", "Sans titre")[:38]
        contenu = r.get("content", "")[:48] + "..."
        table.add_row(url, titre_res, contenu)

    console.print(table)