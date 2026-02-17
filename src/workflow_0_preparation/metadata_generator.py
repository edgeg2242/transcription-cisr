"""
Génération des fichiers metadata JSON et structures projet.
"""
import os
import re
import json
import shutil
import logging
from datetime import datetime

from src.common.exceptions import WorkOrderError

logger = logging.getLogger(__name__)


def generer_metadata_json(metadonnees, fichiers, output_path, metadata_excel=None):
    """
    Générer le fichier metadata_work_order.json pour un Work Order SPR.

    Args:
        metadonnees: Dict métadonnées extraites de la page couverture
        fichiers: Dict chemins fichiers {'audio', 'page_couverture', 'excel', 'zip_original'}
        output_path: Chemin fichier JSON de sortie
        metadata_excel: Dict métadonnées Excel (optionnel, enrichissement)
    """
    metadata_json = {
        "work_order": {
            "type": "SPR",
            "date_traitement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "dossier": {
            "numero": metadonnees['numero_dossier'],
            "section": metadonnees['section'],
            "langue": "Français",
            "huis_clos": metadonnees['huis_clos'],
            "iuc": metadonnees['iuc']
        },
        "participants": {
            "demandeur": metadonnees['demandeur'],
            "commissaire": metadonnees['commissaire'],
            "conseil_demandeur": metadonnees['conseil_demandeur'],
            "conseil_ministre": metadonnees['conseil_ministre'],
            "representant_designe": metadonnees['representant_designe'],
            "interprete": metadonnees['interprete']
        },
        "audience": {
            "date": metadonnees['date_audience'],
            "lieu": metadonnees['lieu_audience'],
            "date_decision": metadonnees['date_decision']
        },
        "fichiers": {
            "audio_original": os.path.basename(fichiers.get('audio', '') or ''),
            "page_couverture": "page_couverture_original.docx",
            "work_order_excel": "work_order.xlsx" if 'excel' in fichiers else None
        }
    }

    # Enrichissement Excel (si disponible)
    if metadata_excel:
        if "transcription" in metadata_excel:
            metadata_json["transcription"] = metadata_excel["transcription"]

        if "participants" in metadata_excel and metadata_excel["participants"].get("demandeur_nom_famille"):
            metadata_json["participants"]["demandeur_nom_famille"] = metadata_excel["participants"]["demandeur_nom_famille"]

        if "validation" in metadata_excel and metadata_excel["validation"].get("langue_audience"):
            metadata_json["dossier"]["langue"] = metadata_excel["validation"]["langue_audience"]

        logger.info("   Métadonnées enrichies depuis Excel Work Order")

    # Sauvegarder JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_json, f, indent=2, ensure_ascii=False)

    taille_kb = os.path.getsize(output_path) / 1024
    logger.info(f"metadata_work_order.json généré ({taille_kb:.1f} KB)")


def generer_metadata_json_sar(metadata_sar, bon_commande, output_path):
    """
    Générer le fichier metadata_work_order.json pour un Work Order SAR.

    Args:
        metadata_sar: Dict métadonnées SAR avec cases[]
        bon_commande: Numéro bon commande (ex: RCE-9439-DD)
        output_path: Chemin fichier JSON de sortie
    """
    metadata_json = {
        "work_order": {
            "number": bon_commande,
            "type": "SAR",
            "date_traitement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "cases": metadata_sar['cases']
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_json, f, indent=2, ensure_ascii=False)

    taille_kb = os.path.getsize(output_path) / 1024
    logger.info(f"metadata_work_order.json SAR généré ({taille_kb:.1f} KB)")


def creer_structure_projet_spr(output_dir, project_name, fichiers, metadata):
    """
    Créer la structure de dossier du projet SPR.

    Args:
        output_dir: Dossier parent (ex: Test_Demandes)
        project_name: Nom projet (ex: HAMMOUD-SPR-07390), ou None pour auto-générer
        fichiers: Dict {'audio': path, 'page_couverture': path, 'excel': path, 'zip_original': path}
        metadata: Métadonnées extraites

    Returns:
        str: Chemin du dossier projet créé
    """
    if not project_name:
        demandeur = metadata.get('demandeur', 'UNKNOWN').split()[0]
        numero = metadata['numero_dossier'].split('-')[1]
        project_name = f"{demandeur}-SPR-{numero}"

    project_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)

    # Copier fichier audio
    if fichiers.get('audio'):
        audio_dest = os.path.join(project_dir, os.path.basename(fichiers['audio']))
        shutil.copy2(fichiers['audio'], audio_dest)
        logger.info(f"Fichier audio copié: {os.path.basename(audio_dest)}")

    # Copier page couverture
    if fichiers.get('page_couverture'):
        cover_dest = os.path.join(project_dir, 'page_couverture_original.docx')
        shutil.copy2(fichiers['page_couverture'], cover_dest)
        logger.info("Page couverture copiée: page_couverture_original.docx")

    # Copier Excel
    if fichiers.get('excel'):
        excel_dest = os.path.join(project_dir, 'work_order.xlsx')
        shutil.copy2(fichiers['excel'], excel_dest)

    # Copier ZIP original
    if fichiers.get('zip_original'):
        zip_dest = os.path.join(project_dir, 'work_order_original.zip')
        shutil.copy2(fichiers['zip_original'], zip_dest)

    logger.info(f"Structure de projet créée: {project_dir}")
    return project_dir


def creer_structure_projet_sar(output_dir, bon_commande, metadata_sar, extracted_dir):
    """
    Créer la structure de dossier du projet SAR (multi-cases).

    Args:
        output_dir: Dossier parent
        bon_commande: Numéro bon commande
        metadata_sar: Métadonnées SAR avec cases[]
        extracted_dir: Dossier extrait du ZIP

    Returns:
        str: Chemin du dossier projet créé
    """
    project_dir = os.path.join(output_dir, f"{bon_commande}-SAR")
    os.makedirs(project_dir, exist_ok=True)

    for case in metadata_sar['cases']:
        case_dir = os.path.join(project_dir, 'cases', case['case_id'])
        os.makedirs(case_dir, exist_ok=True)

        # Copier page couverture
        cover_src_name = case['cover_page_file']
        cover_src = None
        for root, dirs, files in os.walk(extracted_dir):
            if cover_src_name in files:
                cover_src = os.path.join(root, cover_src_name)
                break

        if cover_src:
            cover_dest = os.path.join(case_dir, f"page_couverture_{case['case_id']}.docx")
            shutil.copy2(cover_src, cover_dest)

        # Copier fichiers audio
        if case.get('audio_data'):
            audio_dir = os.path.join(case_dir, 'audio')
            os.makedirs(audio_dir, exist_ok=True)

            spr_folder = case['audio_folder']
            audio_folder_src = os.path.join(extracted_dir, spr_folder, 'DAUDIO')

            if os.path.exists(audio_folder_src):
                for date, audio_files in case['audio_data'].items():
                    for audio_file in audio_files:
                        for root, dirs, files in os.walk(audio_folder_src):
                            if audio_file in files:
                                audio_src = os.path.join(root, audio_file)
                                audio_dest_name = f"{date}_{audio_file}"
                                audio_dest = os.path.join(audio_dir, audio_dest_name)
                                shutil.copy2(audio_src, audio_dest)

    logger.info(f"Structure de projet SAR créée: {project_dir}")
    logger.info(f"   {len(metadata_sar['cases'])} cas organisés")
    return project_dir
