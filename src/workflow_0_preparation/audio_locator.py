"""
Localisation des fichiers audio dans la structure Work Assignment.
"""
import os
import logging
from src.common.exceptions import WorkOrderError

logger = logging.getLogger(__name__)


def trouver_fichier_audio(dossier_base):
    """
    Localiser le(s) fichier(s) audio recursivement.
    Extensions supportees: .a00, .wav, .mp3, .m4a

    Args:
        dossier_base: Dossier racine pour la recherche

    Returns:
        list: Liste de chemins vers fichiers audio, tries par taille (plus gros en premier)

    Raises:
        WorkOrderError: Si aucun fichier audio trouve
    """
    extensions_audio = ('.a00', '.wav', '.mp3', '.m4a')
    fichiers_audio = []

    for root, dirs, files in os.walk(dossier_base):
        for file in files:
            if file.lower().endswith(extensions_audio):
                fichiers_audio.append(os.path.join(root, file))

    if not fichiers_audio:
        raise WorkOrderError("Aucun fichier audio trouve dans le work order")

    fichiers_audio.sort(key=lambda x: os.path.getsize(x), reverse=True)

    logger.info(f"Fichier(s) audio trouve(s): {len(fichiers_audio)}")
    for audio in fichiers_audio:
        taille_mb = os.path.getsize(audio) / (1024 * 1024)
        logger.info(f"   - {os.path.basename(audio)} ({taille_mb:.2f} MB)")

    return fichiers_audio
