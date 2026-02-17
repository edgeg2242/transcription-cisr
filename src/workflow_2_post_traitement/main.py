"""
Workflow 2 : Post-traitement des transcriptions CISR.

Orchestrateur principal : charge la transcription brute, applique les
corrections, mappe les locuteurs, g\u00e9n\u00e8re le document Word CISR conforme.
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

from src.common.logging_setup import fix_utf8_windows, setup_logging
from src.common.exceptions import WorkflowError
from src.workflow_2_post_traitement.text_cleaner import (
    extraire_texte_integral,
    extraire_interventions_par_locuteur,
    nettoyer_texte,
)
from src.workflow_2_post_traitement.corrections import (
    pipeline_corrections_intelligentes,
    charger_dictionnaire,
)
from src.workflow_2_post_traitement.speaker_mapper import (
    mapper_locuteurs,
    structurer_dialogue,
    creer_paragraphes,
)
from src.workflow_2_post_traitement.word_formatter import generer_document_word
from src.workflow_2_post_traitement.qa_validator import valider_qa, generer_rapport

fix_utf8_windows()
logger = logging.getLogger(__name__)


class TranscriptionData:
    """Conteneur pour les donn\u00e9es de transcription tout au long du pipeline."""
    def __init__(self):
        self.texte_brut = ""
        self.metadata = {}
        self.dictionnaire = {}
        self.texte_nettoye = ""
        self.texte_corrige = ""
        self.interventions = []
        self.paragraphes = []
        self.stats_corrections = []
        self.score_qa = {}


def charger_transcription_brute(chemin_txt: str) -> str:
    """Charge la transcription brute depuis le fichier TXT."""
    chemin = Path(chemin_txt)
    if not chemin.exists():
        raise WorkflowError(f"Fichier introuvable : {chemin_txt}")

    with open(chemin, 'r', encoding='utf-8') as f:
        contenu = f.read()

    logger.info(f"Transcription charg\u00e9e ({len(contenu)} caract\u00e8res)")
    return contenu


def charger_metadata(chemin_json: str) -> dict:
    """Charge les m\u00e9tadonn\u00e9es depuis le fichier JSON."""
    import json

    chemin = Path(chemin_json)
    if not chemin.exists():
        raise WorkflowError(f"Fichier metadata introuvable : {chemin_json}")

    with open(chemin, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    logger.info(f"M\u00e9tadonn\u00e9es charg\u00e9es (dossier: {metadata.get('dossier', 'N/A')})")
    return metadata


def main():
    """Point d'entr\u00e9e principal du workflow 2."""
    parser = argparse.ArgumentParser(
        description="Workflow 2 : Transcription Post-Traitement CISR"
    )

    # Arguments obligatoires
    parser.add_argument('--input', required=True, help='Chemin transcription TXT brute')
    parser.add_argument('--metadata', required=True, help='Chemin m\u00e9tadonn\u00e9es JSON')
    parser.add_argument('--dossier', required=True, help='Num\u00e9ro dossier (ex: MC3-16722)')
    parser.add_argument('--section', required=True, choices=['SPR', 'SAR', 'SI', 'SAI'], help='Section CISR')
    parser.add_argument('--transcripteur', required=True, help='Nom du transcripteur')
    parser.add_argument('--agence', required=True, help='Nom agence transcription')

    # Arguments optionnels
    parser.add_argument('--iuc', help='Num\u00e9ro IUC/UCI (10 chiffres)')
    parser.add_argument('--commissaire', help='Nom de la commissaire')
    parser.add_argument('--huis-clos', action='store_true', help='Marquer comme huis clos')
    parser.add_argument('--metadata-json', help='metadata_work_order.json pour tableaux CISR')
    parser.add_argument('--page-couverture', help='Page couverture client (.docx)')
    parser.add_argument('--output-dir', help='Dossier de sortie (d\u00e9faut: m\u00eame que input)')
    parser.add_argument('--skip-qa', action='store_true', help='Sauter validation QA')
    parser.add_argument('--dry-run', action='store_true', help='Mode test')

    args = parser.parse_args()

    try:
        setup_logging()

        logger.info("=" * 70)
        logger.info("Workflow 2 : Transcription Post-Traitement CISR")
        logger.info("=" * 70)

        data = TranscriptionData()

        # \u00c9tape 1 : Chargement
        contenu_brut = charger_transcription_brute(args.input)
        data.metadata = charger_metadata(args.metadata)

        # Charger dictionnaire corrections
        dict_path = Path(__file__).parent.parent.parent / "data" / "dictionaries" / "corrections_v2.1.json"
        data.dictionnaire = charger_dictionnaire(str(dict_path))

        # Extraire texte int\u00e9gral et interventions
        data.texte_brut = extraire_texte_integral(contenu_brut)
        interventions_brutes = extraire_interventions_par_locuteur(contenu_brut)

        # \u00c9tape 2 : Nettoyage
        data.texte_nettoye = nettoyer_texte(data.texte_brut, data.dictionnaire)

        # \u00c9tape 3 : Corrections intelligentes (6 passes)
        data.texte_corrige, rapport_corrections = pipeline_corrections_intelligentes(
            data.texte_nettoye, data.metadata, data.dictionnaire
        )
        data.stats_corrections = rapport_corrections.get('details_corrections', [])

        # \u00c9tape 4 : Mapping locuteurs
        mapping = mapper_locuteurs(interventions_brutes, args)

        # \u00c9tape 5 : Structuration dialogue
        texte_dialogue = structurer_dialogue(data.texte_corrige, mapping)

        # \u00c9tape 6 : Cr\u00e9ation paragraphes
        data.paragraphes = creer_paragraphes(texte_dialogue)

        # Dossier de sortie
        output_dir = Path(args.output_dir) if args.output_dir else Path(args.input).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        nom_fichier = f"{args.transcripteur.upper()}-{args.dossier}-{date_str}-{args.section}.docx"
        output_path = output_dir / nom_fichier

        if args.dry_run:
            logger.info(f"Mode DRY-RUN : Fichier serait g\u00e9n\u00e9r\u00e9 \u00e0 {output_path}")
        else:
            # \u00c9tape 7 : G\u00e9n\u00e9ration document Word
            doc_path = generer_document_word(data, args, output_path)

            # \u00c9tape 8 : Validation QA
            if not args.skip_qa:
                data.score_qa = valider_qa(doc_path, data)
            else:
                logger.info("Validation QA saut\u00e9e (--skip-qa)")
                data.score_qa = {'score': 0, 'total': 20, 'statut': 'SKIPPED'}

            # \u00c9tape 9 : Rapport
            rapport_path = generer_rapport(data, output_dir)

        logger.info("=" * 70)
        logger.info("Workflow termin\u00e9 avec succ\u00e8s")
        if not args.dry_run:
            logger.info(f"Document final : {output_path}")
            logger.info(f"Rapport : {rapport_path}")
            if not args.skip_qa:
                logger.info(f"Score QA : {data.score_qa['score']}/{data.score_qa['total']}")
        logger.info("=" * 70)

        return 0

    except WorkflowError as e:
        logger.error(f"Erreur de workflow : {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Workflow interrompu par l'utilisateur")
        return 130

    except Exception as e:
        logger.error(f"Erreur inattendue : {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
