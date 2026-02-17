"""
Transcription audio via API REST AssemblyAI.

Utilise l'API REST directement (pas le SDK, incompatible Python 3.14/Pydantic v1).

Flux :
1. Upload audio vers AssemblyAI
2. Lancer transcription (avec diarization si multi-locuteurs)
3. Polling jusqu'à completion
4. Retourner transcription brute
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, Optional

from src.common.exceptions import UploadError, WorkflowError

logger = logging.getLogger(__name__)

ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"


def _get_api_key() -> str:
    """Récupère la clé API AssemblyAI depuis les variables d'environnement."""
    api_key = os.getenv('ASSEMBLYAI_API_KEY')
    if not api_key:
        raise WorkflowError("ASSEMBLYAI_API_KEY non définie dans .env")
    return api_key


def upload_audio(audio_path: Path) -> str:
    """
    Upload un fichier audio vers AssemblyAI.

    Args:
        audio_path: Chemin vers le fichier audio (.mp3, .wav)

    Returns:
        URL du fichier uploadé sur AssemblyAI

    Raises:
        UploadError: Si l'upload échoue
    """
    api_key = _get_api_key()
    headers = {"authorization": api_key}

    logger.info(f"Upload audio vers AssemblyAI: {audio_path.name}...")

    with open(audio_path, 'rb') as f:
        response = requests.post(
            f"{ASSEMBLYAI_BASE_URL}/upload",
            headers=headers,
            data=f
        )

    if response.status_code != 200:
        raise UploadError(f"Upload échoué (HTTP {response.status_code}): {response.text}")

    upload_url = response.json()['upload_url']
    logger.info(f"Upload réussi: {upload_url[:60]}...")
    return upload_url


def transcrire(
    audio_url: str,
    language_code: str = "fr",
    speaker_labels: bool = True,
    speakers_expected: Optional[int] = None,
) -> Dict:
    """
    Lance une transcription AssemblyAI et attend le résultat.

    Args:
        audio_url: URL audio (retournée par upload_audio)
        language_code: Code langue (défaut: fr)
        speaker_labels: Activer diarization (défaut: True)
        speakers_expected: Nombre de locuteurs attendus (optionnel)

    Returns:
        Dict avec transcription complète (texte + utterances + mots)

    Raises:
        WorkflowError: Si la transcription échoue
    """
    api_key = _get_api_key()
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }

    # Configurer requête transcription
    payload = {
        "audio_url": audio_url,
        "language_code": language_code,
        "speaker_labels": speaker_labels,
    }

    if speakers_expected:
        payload["speakers_expected"] = speakers_expected

    logger.info(f"Lancement transcription (langue={language_code}, diarization={speaker_labels})...")

    # Lancer transcription
    response = requests.post(
        f"{ASSEMBLYAI_BASE_URL}/transcript",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise WorkflowError(f"Erreur transcription (HTTP {response.status_code}): {response.text}")

    transcript_id = response.json()['id']
    logger.info(f"Transcription lancée: {transcript_id}")

    # Polling jusqu'à completion
    return _poll_transcription(transcript_id, headers)


def _poll_transcription(transcript_id: str, headers: Dict, interval: int = 5, timeout: int = 3600) -> Dict:
    """
    Attend la fin de la transcription par polling.

    Args:
        transcript_id: ID de la transcription
        headers: Headers HTTP avec API key
        interval: Intervalle de polling en secondes
        timeout: Timeout maximum en secondes

    Returns:
        Résultat complet de la transcription
    """
    elapsed = 0

    while elapsed < timeout:
        response = requests.get(
            f"{ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}",
            headers=headers
        )

        result = response.json()
        status = result['status']

        if status == 'completed':
            logger.info(f"Transcription terminée ({elapsed}s)")
            return result

        elif status == 'error':
            raise WorkflowError(f"Transcription échouée: {result.get('error', 'unknown')}")

        logger.info(f"  En cours... ({elapsed}s, statut={status})")
        time.sleep(interval)
        elapsed += interval

    raise WorkflowError(f"Timeout transcription après {timeout}s")


def sauvegarder_transcription_brute(result: Dict, output_path: Path) -> Path:
    """
    Sauvegarde le résultat de transcription en fichier TXT structuré.

    Format :
    - Section TEXTE INTEGRAL
    - Section TRANSCRIPTION PAR LOCUTEUR (si diarization)

    Args:
        result: Résultat AssemblyAI
        output_path: Chemin du fichier de sortie

    Returns:
        Chemin du fichier sauvegardé
    """
    separator = "=" * 70

    with open(output_path, 'w', encoding='utf-8') as f:
        # Section texte intégral
        f.write(f"TEXTE INTEGRAL\n{separator}\n")
        f.write(result.get('text', '') + "\n")
        f.write(f"{separator}\n\n")

        # Section par locuteur (si diarization disponible)
        utterances = result.get('utterances', [])
        if utterances:
            f.write(f"TRANSCRIPTION PAR LOCUTEUR\n{separator}\n\n")

            # Regrouper par locuteur
            locuteurs = {}
            for utt in utterances:
                speaker = utt.get('speaker', 'Unknown')
                if speaker not in locuteurs:
                    locuteurs[speaker] = []
                locuteurs[speaker].append(utt['text'])

            for speaker, textes in sorted(locuteurs.items()):
                f.write(f"\n{separator}\nLOCUTEUR {speaker}\n{separator}\n")
                f.write("\n".join(textes) + "\n")

    logger.info(f"Transcription brute sauvegardée: {output_path}")
    return output_path
