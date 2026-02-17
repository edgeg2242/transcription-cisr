"""
Préparation des fichiers audio pour transcription CISR.

Responsabilités :
- Renommage .a00 → .mp3 (format dictaphone = MP2, pas de conversion)
- Découpage FFmpeg si nécessaire
- Log des Recording Remarks (informatif seulement, pas de découpage — Contrainte #9)
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from src.common.file_utils import renommer_a00_en_mp3

logger = logging.getLogger(__name__)


def preparer_audio(audio_file: Path) -> Path:
    """
    Prépare un fichier audio pour transcription.

    Si le fichier est .a00, le renomme en .mp3.
    Sinon, retourne le chemin tel quel.

    Args:
        audio_file: Chemin vers le fichier audio

    Returns:
        Chemin vers le fichier audio prêt pour transcription
    """
    if audio_file.suffix.lower() == '.a00':
        return renommer_a00_en_mp3(audio_file)
    return audio_file


def log_recording_remarks(audio_file: Path, metadata_work_order: Dict) -> None:
    """
    Log les Recording Unit Remarks du Work Order Excel (informatif seulement).

    Les fichiers audio reçus de la CISR sont déjà pré-découpés (Contrainte #9).
    Cette fonction ne fait PAS de découpage — elle log les Recording Remarks
    à titre informatif uniquement.

    Args:
        audio_file: Chemin vers le fichier audio
        metadata_work_order: Dict métadonnées depuis metadata_work_order.json
    """
    if 'transcription' not in metadata_work_order:
        logger.info("Aucune métadonnée transcription - pas de Recording Remarks")
        return

    transcription_meta = metadata_work_order['transcription']
    recording_remarks = transcription_meta.get('recording_remarks')

    if not recording_remarks:
        logger.info("Aucun Recording Remark")
        return

    audio_decoupage = transcription_meta.get('audio_decoupage', {})
    start_seconds = audio_decoupage.get('start_time_seconds')

    if not start_seconds or start_seconds <= 0:
        logger.info(f"Recording Remark présent mais aucun timestamp: '{recording_remarks}'")
        return

    logger.warning(
        f"Recording Remark: '{recording_remarks}' "
        f"(start={start_seconds}s / {start_seconds // 60}:{start_seconds % 60:02d}) — "
        f"ignoré car fichiers audio déjà pré-découpés par la CISR"
    )
