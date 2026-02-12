#!/usr/bin/env python3
"""
Workflow : Exemple - Récupération de Citation
Description : Récupère une citation aléatoire depuis l'API Quotable et l'affiche
"""

import os
import sys
import io
import logging
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Fix encodage UTF-8 Windows (CLAUDE.md — tous les scripts Python console)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
API_URL = "https://api.quotable.io/random"
TIMEOUT = 10  # secondes
CITATIONS_FILE = "citations.txt"


def recuperer_citation():
    """
    Récupère une citation aléatoire depuis l'API Quotable.

    Returns:
        dict: Données de la citation ou None en cas d'erreur
    """
    try:
        logger.info(f"Appel de l'API : {API_URL}")
        response = requests.get(API_URL, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()
        logger.info("✅ Citation récupérée avec succès")
        return data

    except requests.Timeout:
        logger.error("❌ Timeout : L'API n'a pas répondu dans le délai imparti")
        return None
    except requests.RequestException as e:
        logger.error(f"❌ Erreur lors de l'appel API : {e}")
        return None
    except ValueError as e:
        logger.error(f"❌ Erreur de parsing JSON : {e}")
        return None


def valider_citation(data):
    """
    Valide que les données de la citation sont complètes.

    Args:
        data (dict): Données de la citation

    Returns:
        bool: True si valide, False sinon
    """
    if not data:
        return False

    champs_requis = ['content', 'author']
    for champ in champs_requis:
        if champ not in data or not data[champ]:
            logger.error(f"❌ Champ manquant ou vide : {champ}")
            return False

    return True


def afficher_citation(data):
    """
    Affiche la citation de manière formatée.

    Args:
        data (dict): Données de la citation
    """
    print("\n" + "="*60)
    print(f"\"{data['content']}\"")
    print(f"\n— {data['author']}")

    if 'tags' in data and data['tags']:
        print(f"\nTags: {', '.join(data['tags'])}")

    print("="*60 + "\n")


def sauvegarder_citation(data):
    """
    Sauvegarde la citation dans un fichier.

    Args:
        data (dict): Données de la citation
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CITATIONS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}]\n")
            f.write(f"\"{data['content']}\"\n")
            f.write(f"— {data['author']}\n")
            f.write("-" * 60 + "\n")

        logger.info(f"✅ Citation sauvegardée dans {CITATIONS_FILE}")

    except IOError as e:
        logger.error(f"❌ Erreur lors de la sauvegarde : {e}")


def main():
    """Point d'entrée principal du workflow."""
    # Parser les arguments
    parser = argparse.ArgumentParser(
        description="Récupère et affiche une citation aléatoire"
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Sauvegarder la citation dans un fichier'
    )
    args = parser.parse_args()

    try:
        logger.info("Démarrage du workflow de récupération de citation...")

        # Étape 1 & 2 : Récupérer la citation
        data = recuperer_citation()

        # Étape 3 : Valider les données
        if not valider_citation(data):
            logger.error("❌ Données de citation invalides")
            return 1

        # Étape 4 : Afficher la citation
        afficher_citation(data)

        # Étape 5 (optionnelle) : Sauvegarder
        if args.save:
            sauvegarder_citation(data)

        logger.info("✅ Workflow terminé avec succès")
        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Workflow interrompu par l'utilisateur")
        return 130
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
