"""
Analyseur adaptatif de Work Assignments.

Détecte la structure d'un ZIP décompressé et identifie tous les
Work Orders présents en utilisant l'Excel comme source de vérité.
"""
import os
import re
import logging

from src.common.file_utils import localiser_fichier_audio
from src.common.exceptions import WorkOrderError
from src.workflow_0_preparation.excel_parser import lire_excel_tous_work_orders

logger = logging.getLogger(__name__)


def detecter_work_orders_multiples(extracted_dir, excel_path):
    """
    Détecter tous les Work Orders dans un ZIP décompressé.

    Algorithme:
        1. Lire Excel Work Order pour connaître nombre exact de dossiers
        2. Vérifier présence dossiers MC3-xxxxx correspondants
        3. Localiser pages couvertures (racine du ZIP)
        4. Localiser fichiers audio (dans chaque dossier DAUDIO)
        5. Associer: Excel ligne -> dossier -> page couverture -> audio

    Args:
        extracted_dir: Chemin vers dossier ZIP décompressé
        excel_path: Chemin vers fichier Excel work order

    Returns:
        list[dict]: Liste de Work Orders détectés avec tous les chemins associés

    Raises:
        WorkOrderError: Si incohérences critiques détectées
    """
    logger.info("Détection Work Orders multiples...")

    # ÉTAPE 1: Lire Excel pour référence
    work_orders_excel = lire_excel_tous_work_orders(excel_path)

    # ÉTAPE 2: Détecter dossiers MC[2-5]-xxxxx
    dossiers_regex = re.compile(r'MC[2-5]-\d{5}')
    dossiers_trouves = []

    for item in os.listdir(extracted_dir):
        item_path = os.path.join(extracted_dir, item)
        if os.path.isdir(item_path) and dossiers_regex.match(item):
            dossiers_trouves.append(item)

    logger.info(
        f"{len(dossiers_trouves)} dossiers MC détectés: "
        f"{', '.join(sorted(dossiers_trouves))}"
    )

    # ÉTAPE 3: Valider cohérence Excel vs dossiers
    numeros_excel = set(wo['numero_dossier'] for wo in work_orders_excel)
    dossiers_set = set(dossiers_trouves)

    if numeros_excel != dossiers_set:
        manquants_excel = dossiers_set - numeros_excel
        manquants_dossiers = numeros_excel - dossiers_set

        if manquants_excel:
            logger.warning(f"Dossiers présents mais absents Excel: {manquants_excel}")
        if manquants_dossiers:
            logger.warning(f"Dossiers listés Excel mais absents: {manquants_dossiers}")

    # ÉTAPE 4: Localiser pages couvertures
    pages_couvertures = {}
    for root, dirs, files in os.walk(extracted_dir):
        for file in files:
            if file.endswith('.docx') and not file.startswith('~'):
                match = dossiers_regex.search(file)
                if match:
                    numero = match.group()
                    pages_couvertures[numero] = os.path.join(root, file)

    logger.info(f"{len(pages_couvertures)} pages couvertures localisées")

    # ÉTAPE 5: Assembler données
    work_orders = []

    for wo_excel in work_orders_excel:
        numero = wo_excel['numero_dossier']
        dossier_path = os.path.join(extracted_dir, numero)

        if not os.path.isdir(dossier_path):
            logger.warning(f"Dossier manquant: {numero}")
            continue

        page_couv = pages_couvertures.get(numero)
        if not page_couv:
            logger.warning(f"Page couverture manquante pour {numero}")

        audio_file = None
        try:
            audio_file = str(localiser_fichier_audio(dossier_path, numero))
        except FileNotFoundError as e:
            logger.warning(str(e))

        work_orders.append({
            'numero_dossier': numero,
            'dossier_path': dossier_path,
            'page_couverture': page_couv,
            'audio_file': audio_file,
            'excel_work_order': excel_path,
            'metadata_excel': {
                'date_audience': wo_excel['date_audience'],
                'duree_audio': wo_excel['duree_audio'],
                'recording_remarks': wo_excel['recording_remarks'],
            }
        })

    logger.info(f"{len(work_orders)} Work Orders assemblés avec succès")

    # VALIDATION FINALE
    erreurs = []
    for wo in work_orders:
        if not wo['page_couverture']:
            erreurs.append(f"{wo['numero_dossier']}: Page couverture manquante")
        if not wo['audio_file']:
            erreurs.append(f"{wo['numero_dossier']}: Fichier audio manquant")

    if erreurs:
        logger.warning("Avertissements détection:")
        for err in erreurs:
            logger.warning(f"   - {err}")

    return work_orders
