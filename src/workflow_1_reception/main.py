"""
Workflow 1 : Réception et transcription des demandes CISR.

Orchestrateur principal : reçoit un dossier de demande,
prépare l'audio, transcrit via AssemblyAI, sauvegarde le résultat brut.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

from src.common.logging_setup import fix_utf8_windows, setup_logging
from src.common.exceptions import WorkflowError
from src.workflow_1_reception.audio_preparer import preparer_audio, log_recording_remarks
from src.workflow_1_reception.transcriber import (
    upload_audio,
    transcrire,
    sauvegarder_transcription_brute,
)

fix_utf8_windows()
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal du workflow 1."""
    parser = argparse.ArgumentParser(
        description="Workflow 1 : Réception et Transcription CISR"
    )

    parser.add_argument('--demande-folder', required=True, help='Dossier contenant audio + metadata')
    parser.add_argument('--metadata-json', help='metadata_work_order.json (workflow 0)')
    parser.add_argument('--section', choices=['SPR', 'SAR', 'SI', 'SAI'], help='Section CISR')
    parser.add_argument('--output-dir', help='Dossier de sortie (défaut: demande-folder)')
    parser.add_argument('--language', default='fr', help='Code langue (défaut: fr)')
    parser.add_argument('--no-diarization', action='store_true', help='Désactiver la diarization')
    parser.add_argument('--speakers', type=int, help='Nombre de locuteurs attendus')

    args = parser.parse_args()

    try:
        setup_logging()

        logger.info("=" * 70)
        logger.info("Workflow 1 : Réception et Transcription CISR")
        logger.info("=" * 70)

        demande_folder = Path(args.demande_folder)
        output_dir = Path(args.output_dir) if args.output_dir else demande_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        # Charger metadata si disponible
        metadata_wo = {}
        if args.metadata_json and Path(args.metadata_json).exists():
            with open(args.metadata_json, 'r', encoding='utf-8') as f:
                metadata_wo = json.load(f)
            logger.info(f"Métadonnées chargées: {args.metadata_json}")

        # Trouver fichiers audio
        audio_extensions = ['.a00', '.mp3', '.wav', '.m4a']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(demande_folder.rglob(f'*{ext}'))

        if not audio_files:
            raise WorkflowError(f"Aucun fichier audio trouvé dans {demande_folder}")

        logger.info(f"Fichiers audio trouvés: {len(audio_files)}")

        # Traiter chaque fichier audio
        for audio_file in audio_files:
            logger.info(f"\nTraitement: {audio_file.name}")

            # Log Recording Remarks (informatif)
            log_recording_remarks(audio_file, metadata_wo)

            # Préparer audio (.a00 → .mp3 si nécessaire)
            audio_pret = preparer_audio(audio_file)
            logger.info(f"Audio prêt: {audio_pret.name}")

            # Upload vers AssemblyAI
            audio_url = upload_audio(audio_pret)

            # Déterminer nombre de locuteurs
            speakers = args.speakers
            if not speakers and args.section:
                speakers = 1 if args.section == 'SPR' else None

            # Transcrire
            result = transcrire(
                audio_url=audio_url,
                language_code=args.language,
                speaker_labels=not args.no_diarization,
                speakers_expected=speakers,
            )

            # Sauvegarder transcription brute
            output_name = f"{audio_file.stem}_transcription_brute.txt"
            output_path = output_dir / output_name
            sauvegarder_transcription_brute(result, output_path)

            # Sauvegarder résultat JSON complet
            json_path = output_dir / f"{audio_file.stem}_assemblyai_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Résultat JSON: {json_path}")

        logger.info("=" * 70)
        logger.info("Workflow 1 terminé avec succès")
        logger.info("=" * 70)
        return 0

    except WorkflowError as e:
        logger.error(f"Erreur workflow : {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Workflow interrompu")
        return 130

    except Exception as e:
        logger.error(f"Erreur inattendue : {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
