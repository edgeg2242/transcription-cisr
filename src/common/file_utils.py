"""
Utilitaires fichiers partagés — ZIP, audio, glob.
"""
import os
import re
import glob
import zipfile
import logging
from pathlib import Path

from src.common.exceptions import WorkOrderError
from src.common.constants import TypeTranscription

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Décompression ZIP (avec protection Zip Slip)
# ---------------------------------------------------------------------------

def decompresser_zip(zip_path: str | Path, extract_dir: str | Path) -> Path:
    """
    Décompresse un ZIP Work Assignment avec protection Zip Slip.

    Args:
        zip_path: Chemin vers le fichier ZIP.
        extract_dir: Dossier de destination.

    Returns:
        Chemin du dossier d'extraction.

    Raises:
        WorkOrderError: ZIP invalide, erreur extraction, ou Zip Slip détecté.
    """
    zip_path = Path(zip_path)
    extract_dir = Path(extract_dir)

    if not zip_path.exists():
        raise WorkOrderError(f"Fichier ZIP introuvable : {zip_path}")

    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
        target = extract_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Protection Zip Slip
            for member in zip_ref.namelist():
                member_path = (target / member).resolve()
                if not str(member_path).startswith(str(target)):
                    raise WorkOrderError(
                        f"Zip Slip détecté : chemin suspect '{member}'"
                    )
            zip_ref.extractall(extract_dir)

        nb_fichiers = sum(1 for _ in extract_dir.rglob("*") if _.is_file())
        logger.info(f"ZIP décompressé : {nb_fichiers} fichiers extraits dans {extract_dir}")
        return extract_dir

    except zipfile.BadZipFile as e:
        raise WorkOrderError(f"Fichier ZIP invalide : {e}") from e
    except WorkOrderError:
        raise
    except Exception as e:
        raise WorkOrderError(f"Erreur décompression ZIP : {e}") from e


# ---------------------------------------------------------------------------
# Localisation fichier audio (.a00)
# ---------------------------------------------------------------------------

def localiser_fichier_audio(
    dossier_path: str | Path,
    numero_dossier: str,
) -> Path:
    """
    Localise le fichier .a00 dans l'arborescence DAUDIO profonde.

    Structure attendue:
        MC3-56703/DAUDIO/2025-12-09/_0231/MC3-56703/6703.a00

    Matching STRICT par startswith (pas `in`) — Contrainte #5.

    Args:
        dossier_path: Chemin vers le dossier MC3-xxxxx.
        numero_dossier: Numéro complet (ex: "MC3-56703").

    Returns:
        Chemin absolu vers le fichier .a00.

    Raises:
        FileNotFoundError: Aucun fichier audio trouvé ou aucun match strict.
    """
    dossier_path = Path(dossier_path)
    audio_files = list(dossier_path.rglob("*.a00"))

    if not audio_files:
        raise FileNotFoundError(
            f"Aucun fichier audio .a00 trouvé dans {dossier_path}"
        )

    # Matching strict par les 4 derniers chiffres du numéro de dossier
    dernier_4 = numero_dossier[-4:]
    correspondants = [
        f for f in audio_files
        if f.name.startswith(f"{dernier_4}.") or f.name.startswith(f"{dernier_4}_")
    ]

    if correspondants:
        logger.info(f"Audio trouvé pour {numero_dossier} : {correspondants[0].name}")
        return correspondants[0]

    # Pas de fallback silencieux — erreur explicite
    noms = [f.name for f in audio_files]
    raise FileNotFoundError(
        f"Aucun fichier audio correspondant à {numero_dossier} "
        f"(attendu: {dernier_4}.a00). Fichiers présents: {noms}"
    )


# ---------------------------------------------------------------------------
# Renommage .a00 → .mp3 (PAS de conversion)
# ---------------------------------------------------------------------------

def renommer_a00_en_mp3(audio_path: str | Path) -> Path:
    """
    Renomme un fichier .a00 en .mp3.

    Les fichiers .a00 sont du MP2 dictaphone, directement lisibles en .mp3.
    PAS de conversion nécessaire — simple renommage.

    Args:
        audio_path: Chemin vers le fichier .a00.

    Returns:
        Chemin du fichier .mp3 renommé.

    Raises:
        FileNotFoundError: Fichier .a00 introuvable.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

    if audio_path.suffix.lower() == ".mp3":
        logger.info(f"Fichier déjà en .mp3 : {audio_path.name}")
        return audio_path

    mp3_path = audio_path.with_suffix(".mp3")
    os.rename(audio_path, mp3_path)
    logger.info(f"Renommé : {audio_path.name} → {mp3_path.name}")
    return mp3_path


# ---------------------------------------------------------------------------
# Détection type transcription
# ---------------------------------------------------------------------------

def detecter_type_transcription(chemin: str) -> str:
    """
    Détecte le type de transcription (SPR/SAR/SI/SAI) depuis un chemin.

    Ordre de priorité pour éviter faux positifs:
    1. SPR/RPD en premier (car "RAD" peut apparaître dans "Refugee Protection Division")
    2. SAR/RAD avec exclusion "PROTECTION"
    3. SI/ID
    4. SAI/IAD

    Args:
        chemin: Chemin complet (ZIP, dossier, Excel).

    Returns:
        TypeTranscription constant (SPR, SAR, SI, SAI).
        Défaut: SPR si aucun pattern détecté.
    """
    fullpath = chemin.upper()

    # Priorité 1: SPR/RPD
    if "SPR" in fullpath or "RPD FILE" in fullpath or "BENCH" in fullpath:
        return TypeTranscription.SPR

    # Priorité 2: SAR/RAD (avec exclusion "PROTECTION")
    if "SAR" in fullpath or ("RAD" in fullpath and "PROTECTION" not in fullpath):
        return TypeTranscription.SAR

    # Priorité 3: SI/ID (numéro 0018-Cx)
    if "0018" in fullpath or (" SI " in fullpath and "IMMIGRATION" in fullpath):
        return TypeTranscription.SI

    # Priorité 4: SAI/IAD
    if "SAI" in fullpath or "IAD" in fullpath:
        return TypeTranscription.SAI

    logger.warning(f"Type non détecté depuis '{chemin}', défaut à SPR")
    return TypeTranscription.SPR
