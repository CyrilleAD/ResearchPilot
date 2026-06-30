import json
import os
import time
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
from config import MODELE_SECONDAIRE, TEMPERATURE_ANALYSE, REGION

load_dotenv()


def creer_client() -> OpenAI:
    """ Cree et retourne un client OpenAI authentifie."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def appel_llm(
        system: str,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = 2000
) -> str:
    
    """
    Effectue un appel LLM avec les parametres par defaut du projet.

    Parametres :
        system      : Le system prompt (role et instructions permanentes)
        prompt      : Le message utilisateur (la question ou tache)
        model       : Modele a utiliser (defaut : MODELE_SECONDAIRE de config)
        temperature : Creativite 0.0-1.0 (defaut : TEMPERATURE_ANALYSE de config)
        max_tokens  : Limite de tokens en sortie

    Retourne : Le texte genere par le LLM (string)
    """
    if model is None: 
        model = MODELE_SECONDAIRE
    if temperature is None:
        temperature = TEMPERATURE_ANALYSE

    client = creer_client()
    for tentative in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except RateLimitError:
            if tentative < 2:
                attente = 2 ** tentative  # 1s, 2s
                print(f"[AVERTISSEMENT] Rate limit — attente {attente}s avant retry {tentative + 2}/3")
                time.sleep(attente)
            else:
                raise


def parser_json(texte: str, fallback: dict, outil_nom: str = "inconnu") -> dict:
    """
    Parse une reponse JSON du LLM.

    Le LLM enveloppe parfois son JSON dans des backticks markdown :
        ```json
        { "cle": "valeur" }
        ```
    On nettoie ca avant de parser.

    En cas d'echec de parsing, on ne retourne PAS silencieusement un dict vide.
    On logue un avertissement visible pour que tu saches que quelque chose a cloche.

    Parametres :
        texte     : La reponse brute du LLM
        fallback  : Le dict a retourner si le JSON est invalide
        outil_nom : Nom de l'outil appelant (pour le message d'erreur)

    Retourne : dict parse ou fallback avec cle "_parsing_echec": True
    """

    nettoyee = texte.strip()

    # Supprimer les backticks markdown si presents
    if nettoyee.startswith("```"):
        parties = nettoyee.split("```")
        if len(parties) >= 2:
            nettoyee = parties[1]
            if nettoyee.startswith("json"):
                nettoyee = nettoyee[4:]
    nettoyee = nettoyee.strip()

    try:
        return json.loads(nettoyee)
    except json.JSONDecodeError as e:
        print(f"\n[AVERTISSEMENT] {outil_nom}: JSON invalide retourne par le LLM.")
        print(f"  Erreur : {e}")
        print(f"  Debut de la reponse : {texte[:150]}...")
        print(f"  Utilisation du fallback. Les donnees peuvent etre incompletes.\n")
        resultat = dict(fallback)
        resultat["_parsing_echec"] = True
        return resultat
    


def recherche_tavily(
        requete: str,
        nb_resultats: int = 5,
        profondeur: str = 'basic',
        region: str = None
) -> list:
    """
    Effectue une recherche web avec Tavily.

    Tavily est un moteur de recherche concu pour les LLMs. Il retourne
    du texte propre extrait des pages, pas du HTML brut a parser.

    POURQUOI OBLIGATOIRE :
    Ce projet fait des estimations financieres et des analyses de marche.
    Ces donnees DOIVENT etre actuelles. Un agent qui invente des salaires
    ou des prix cloud est inutile — pire, il est trompeur.
    Tavily gratuit = 1000 recherches/mois. C'est largement suffisant.

    Parametres :
        requete      : La question a rechercher (en francais ou anglais)
        nb_resultats : Nombre de resultats a retourner (1-10)
        profondeur   : "basic" (rapide) ou "advanced" (plus cher en credits)
        region       : Contexte geographique a ajouter a la requete
                       (defaut : REGION de config.py)

    Retourne : Liste de dicts avec url, title, content, score

    Leve ValueError si TAVILY_API_KEY n'est pas configuree.
    """
    if region is None:
        region = REGION

    cle = os.getenv("TAVILY_API_KEY", "")
    if not cle or not cle.startswith("tvly-"):
        raise ValueError(
            "\n" + "=" * 60 + "\n"
            "ERREUR : TAVILY_API_KEY manquante ou invalide.\n\n"
            "Tavily est obligatoire pour ResearchPilot.\n"
            "Sans lui, l'agent invente des donnees financieres — ce qui\n"
            "rendrait toute l'analyse sans valeur.\n\n"
            "Comment obtenir une cle gratuite :\n"
            "1. Va sur https://tavily.com\n"
            "2. Cree un compte (gratuit, 1000 recherches/mois)\n"
            "3. Copie ta cle API (commence par 'tvly-')\n"
            "4. Ajoute dans ton .env : TAVILY_API_KEY=tvly-ta-cle-ici\n"
            "=" * 60
        )
    
    # Enrichir la requete avec le contexte regional
    requete_complete = f"{requete} {region} 2025 2026"

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=cle)
        reponse = client.search(
            query=requete_complete,
            search_depth=profondeur,
            max_results=nb_resultats,
            include_answer=True
        )
        return reponse.get("results", [])

    except ValueError:
        raise  # Re-propager les erreurs de cle

    except Exception as e:
        print(f"[AVERTISSEMENT] Tavily: erreur reseau — {e}")
        print("  La recherche a echoue mais le programme continue.")
        return []
    


def formater_resultats_tavily(resultats: list, max_chars: int = 400) -> str:
    """
    Formate une liste de resultats Tavily en texte structure pour un prompt LLM.

    Parametres :
        resultats : Liste retournee par recherche_tavily()
        max_chars : Nombre max de caracteres par extrait de page

    Retourne : String formate pret a etre injecte dans un prompt
    """
    if not resultats:
        return ""

    lignes = ["\n\nSOURCES WEB RECENTES :"]
    for i, r in enumerate(resultats, 1):
        lignes.append(f"\n[Source {i}] {r.get('url', 'url inconnue')}")
        lignes.append(f"Titre   : {r.get('title', '')}")
        lignes.append(f"Extrait : {r.get('content', '')[:max_chars]}")

    return "\n".join(lignes)
