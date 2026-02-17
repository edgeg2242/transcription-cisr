"""
Workflow 0 : Préparation Work Order CISR

Point d'entrée CLI et orchestration du pipeline de préparation.
Décompresse le ZIP, identifie le type, extrait les métadonnées,
et prépare la structure projet pour les workflows suivants.
"""
import os
import re
import sys
import shutil
import argparse
import logging

from src.common.logging_setup import fix_utf8_windows, setup_logging
from src.common.file_utils import decompresser_zip, detecter_type_transcription
from src.common.constants import TypeTranscription
from src.common.exceptions import WorkOrderError

from src.workflow_0_preparation.excel_parser import (
    parser_excel_work_order,
    lire_excel_tous_work_orders,
)
from src.workflow_0_preparation.cover_page_extractor import (
    extraire_metadonnees_spr,
    extraire_metadonnees_sar,
)
from src.workflow_0_preparation.audio_locator import trouver_fichier_audio
from src.workflow_0_preparation.metadata_generator import (
    generer_metadata_json,
    generer_metadata_json_sar,
    creer_structure_projet_spr,
    creer_structure_projet_sar,
)
from src.workflow_0_preparation.validators import valider_metadonnees_spr
from src.workflow_0_preparation.work_assignment_analyzer import (
    detecter_work_orders_multiples,
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal du workflow 0."""
    fix_utf8_windows()

    parser = argparse.ArgumentParser(
        description='Workflow 0: Préparation Work Order CISR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python -m src.workflow_0_preparation.main \\
    --zip-path "work_assignment.zip" \\
    --output-dir "Test_Demandes"
        """
    )
    parser.add_argument('--zip-path', required=True,
                        help='Chemin vers le fichier ZIP work order')
    parser.add_argument('--output-dir', default='Test_Demandes',
                        help='Dossier de sortie (défaut: Test_Demandes)')
    parser.add_argument('--project-name',
                        help='Nom du projet (auto-généré si omis)')

    args = parser.parse_args()
    setup_logging(__name__)

    try:
        logger.info("=" * 60)
        logger.info("Démarrage Workflow 0: Préparation Work Order CISR")
        logger.info("=" * 60)

        if not os.path.exists(args.zip_path):
            raise WorkOrderError(f"Fichier ZIP non trouvé: {args.zip_path}")

        temp_dir = os.path.join(os.getcwd(), 'extracted_temp')

        # ÉTAPE 1: Décompression
        logger.info("\n[ÉTAPE 1] Décompression du ZIP...")
        extract_dir = decompresser_zip(args.zip_path, temp_dir)

        # ÉTAPE 2: Identification Type
        logger.info("\n[ÉTAPE 2] Identification du type de transcription...")
        type_transcription = detecter_type_transcription(str(extract_dir))

        # ÉTAPE 3: Extraction Métadonnées
        logger.info("\n[ÉTAPE 3] Extraction des métadonnées...")

        # Chercher fichier Excel
        excel_files = []
        for root, dirs, files in os.walk(str(extract_dir)):
            for file in files:
                if file.endswith('.xlsx') and not file.startswith('~'):
                    excel_files.append(os.path.join(root, file))

        if type_transcription == TypeTranscription.SPR:
            project_dir, metadata_path = _traiter_spr(
                extract_dir, excel_files, args
            )

        elif type_transcription == TypeTranscription.SAR:
            project_dir, metadata_path = _traiter_sar(
                extract_dir, args
            )

        else:
            raise WorkOrderError(
                f"Type {type_transcription} pas encore supporté (MVP SPR et SAR seulement)"
            )

        # NETTOYAGE
        logger.info("\n[NETTOYAGE] Suppression dossier temporaire...")
        shutil.rmtree(temp_dir, ignore_errors=True)

        # SUCCÈS
        logger.info("\n" + "=" * 60)
        logger.info("Work order préparé avec succès!")
        logger.info(f"Dossier projet: {project_dir}")
        logger.info(f"Métadonnées: {metadata_path}")
        logger.info("Prêt pour workflow 1 (réception)")
        logger.info("=" * 60)

        return 0

    except WorkOrderError as e:
        logger.error(f"\nErreur workflow 0: {e}")
        return 1
    except Exception as e:
        logger.error(f"\nErreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _traiter_spr(extract_dir, excel_files, args):
    """Traiter un Work Assignment SPR (simple ou multi-WO)."""
    extract_dir_str = str(extract_dir)

    # Détection multi-Work Orders
    work_orders_multiples = None
    if excel_files:
        try:
            logger.info("\n[ÉTAPE 3.5] Détection Work Orders multiples...")
            work_orders_multiples = detecter_work_orders_multiples(
                extract_dir_str, excel_files[0]
            )
            if len(work_orders_multiples) <= 1:
                work_orders_multiples = None
            else:
                logger.info(
                    f"Mode MULTI-WORK ORDERS: {len(work_orders_multiples)} dossiers"
                )
        except Exception as e:
            logger.warning(f"Détection multi-WO échouée: {e}")
            work_orders_multiples = None

    # BRANCHE MULTI
    if work_orders_multiples and len(work_orders_multiples) > 1:
        return _traiter_spr_multi(work_orders_multiples, args)

    # BRANCHE SIMPLE
    return _traiter_spr_simple(extract_dir_str, excel_files, args)


def _traiter_spr_multi(work_orders, args):
    """Traiter plusieurs Work Orders SPR."""
    logger.info(f"\nTraitement de {len(work_orders)} Work Orders...")
    project_dir = None
    metadata_path = None

    for i, wo in enumerate(work_orders, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Work Order {i}/{len(work_orders)}: {wo['numero_dossier']}")
        logger.info(f"{'='*60}")

        metadonnees = extraire_metadonnees_spr(wo['page_couverture'])
        metadata_excel = parser_excel_work_order(
            wo['excel_work_order'], numero_dossier=wo['numero_dossier']
        )

        fichiers = {
            'audio': wo['audio_file'],
            'page_couverture': wo['page_couverture'],
            'excel': wo['excel_work_order'],
            'zip_original': args.zip_path,
        }

        project_dir = creer_structure_projet_spr(
            args.output_dir, None, fichiers, metadonnees
        )
        metadata_path = os.path.join(project_dir, 'metadata_work_order.json')
        generer_metadata_json(metadonnees, fichiers, metadata_path, metadata_excel)
        valider_metadonnees_spr(metadonnees)

        logger.info(f"{wo['numero_dossier']}: Traité avec succès")

    logger.info(f"\n{len(work_orders)} Work Orders traités avec succès")
    return project_dir, metadata_path


def _traiter_spr_simple(extract_dir, excel_files, args):
    """Traiter un seul Work Order SPR."""
    logger.info("\nMode Work Order Simple (1 dossier)")

    # Page couverture
    page_couverture_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.docx') and not file.startswith('~'):
                page_couverture_files.append(os.path.join(root, file))

    if not page_couverture_files:
        raise WorkOrderError("Aucune page couverture (.docx) trouvée")

    page_couverture_path = page_couverture_files[0]
    metadonnees = extraire_metadonnees_spr(page_couverture_path)

    # Audio
    logger.info("\n[ÉTAPE 4] Localisation du fichier audio...")
    fichiers_audio = trouver_fichier_audio(extract_dir)

    # Excel
    metadata_excel = None
    if excel_files:
        try:
            metadata_excel = parser_excel_work_order(
                excel_files[0], numero_dossier=metadonnees['numero_dossier']
            )
        except WorkOrderError as e:
            logger.warning(f"Parsing Excel échoué: {e}")

    # Structure projet
    fichiers = {
        'audio': fichiers_audio[0] if fichiers_audio else None,
        'page_couverture': page_couverture_path,
        'excel': excel_files[0] if excel_files else None,
        'zip_original': args.zip_path,
    }

    project_dir = creer_structure_projet_spr(
        args.output_dir, args.project_name, fichiers, metadonnees
    )

    metadata_path = os.path.join(project_dir, 'metadata_work_order.json')
    generer_metadata_json(metadonnees, fichiers, metadata_path, metadata_excel)
    valider_metadonnees_spr(metadonnees)

    return project_dir, metadata_path


def _traiter_sar(extract_dir, args):
    """Traiter un Work Assignment SAR (multi-cases)."""
    metadata_sar = extraire_metadonnees_sar(str(extract_dir))

    logger.info("\n[ÉTAPE 5] Création de la structure de projet SAR...")
    zip_basename = os.path.basename(args.zip_path)
    match_bon = re.search(r'([A-Z]+-\d+-[A-Z]+)', zip_basename)
    bon_commande = match_bon.group(1) if match_bon else "SAR-UNKNOWN"

    if args.project_name:
        bon_commande = args.project_name.replace('-SAR', '')

    project_dir = creer_structure_projet_sar(
        args.output_dir, bon_commande, metadata_sar, str(extract_dir)
    )

    metadata_path = os.path.join(project_dir, 'metadata_work_order.json')
    generer_metadata_json_sar(metadata_sar, bon_commande, metadata_path)

    if not metadata_sar.get('cases') or len(metadata_sar['cases']) == 0:
        raise WorkOrderError("SAR: Aucun case valide trouvé")

    logger.info(f"Validation SAR réussie ({len(metadata_sar['cases'])} cases)")
    return project_dir, metadata_path


if __name__ == '__main__':
    sys.exit(main())
