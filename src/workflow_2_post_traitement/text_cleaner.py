"""
Nettoyage de texte et extraction de sections pour le pipeline CISR.

Responsabilités :
- Extraire la section TEXTE INTEGRAL d'une transcription brute
- Extraire les interventions par locuteur (diarization)
- Nettoyer le texte (tics de langage, répétitions)
- Extraire la section MOTIFS pour les transcriptions SPR
"""

import re
import logging
from typing import Dict, Optional

from src.common.constants import MOTIFS_DEBUT_PATTERNS, MOTIFS_FIN_PATTERNS

logger = logging.getLogger(__name__)


def extraire_texte_integral(contenu_brut: str) -> str:
    """
    Extrait la section TEXTE INTEGRAL de la transcription brute.

    Args:
        contenu_brut: Contenu complet du fichier TXT AssemblyAI

    Returns:
        Texte intégral uniquement
    """
    match = re.search(
        r'TEXTE INTEGRAL\s*={70}\s*\n(.*?)\n={70}\s*\nTRANSCRIPTION PAR LOCUTEUR',
        contenu_brut,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()

    logger.warning("Section TEXTE INTEGRAL non trouvée, utilisation contenu complet")
    return contenu_brut


def extraire_interventions_par_locuteur(contenu_brut: str) -> Dict[str, str]:
    """
    Extrait les interventions par locuteur depuis la section diarization.

    Args:
        contenu_brut: Contenu complet du fichier TXT

    Returns:
        {locuteur: texte_concatene}
    """
    interventions = {}

    pattern = r'={70}\s*\nLOCUTEUR ([A-Z])\s*\n={70}\s*\n(.*?)(?=\n={70}|$)'
    matches = re.finditer(pattern, contenu_brut, re.DOTALL)

    for match in matches:
        locuteur = match.group(1)
        texte = match.group(2).strip()

        if locuteur in interventions:
            interventions[locuteur] += " " + texte
        else:
            interventions[locuteur] = texte

    logger.info(f"Locuteurs extraits : {list(interventions.keys())}")
    return interventions


def nettoyer_texte(texte: str, dictionnaire: dict) -> str:
    """
    Nettoie le texte en supprimant les éléments non substantiels.

    Suppressions :
    - Tics de langage (euh, hmm, etc.)
    - Répétitions immédiates
    - Espaces multiples
    - Éléments listés dans le dictionnaire (section suppressions)

    Args:
        texte: Texte brut à nettoyer
        dictionnaire: Dictionnaire de corrections

    Returns:
        Texte nettoyé
    """
    logger.info("Nettoyage du texte...")

    texte_nettoye = texte

    # Supprimer tics de langage courants
    tics = [
        r'\b[Ee]uh\b',
        r'\b[Hh]mm?\b',
        r'\b[Oo]k\b(?!\s*[,.])',
        r'\b[Bb]en\b(?=\s*,)',
    ]
    for tic in tics:
        texte_nettoye = re.sub(tic, '', texte_nettoye)

    # Supprimer répétitions immédiates (ex: "le le" → "le")
    texte_nettoye = re.sub(r'\b(\w+)\s+\1\b', r'\1', texte_nettoye, flags=re.IGNORECASE)

    # Supprimer espaces multiples
    texte_nettoye = re.sub(r'  +', ' ', texte_nettoye)

    # Supprimer éléments du dictionnaire (section suppressions)
    suppressions = dictionnaire.get('suppressions', [])
    for pattern_supp in suppressions:
        texte_nettoye = texte_nettoye.replace(pattern_supp, '')

    logger.info(f"Nettoyage terminé ({len(texte)} -> {len(texte_nettoye)} caractères)")
    return texte_nettoye


def extraire_section_motifs(texte: str) -> Optional[str]:
    """
    Extrait la section MOTIFS d'une transcription SPR complète.

    Les transcriptions SPR contiennent l'audience complète mais seuls
    les MOTIFS de la décision du commissaire doivent être transcrits.

    Utilise les patterns définis dans constants.MOTIFS_DEBUT_PATTERNS
    et constants.MOTIFS_FIN_PATTERNS.

    Args:
        texte: Texte intégral de la transcription

    Returns:
        Section MOTIFS uniquement, ou None si non trouvée
    """
    logger.info("Recherche section MOTIFS dans transcription SPR...")

    # Chercher début des MOTIFS
    debut_idx = None
    for pattern in MOTIFS_DEBUT_PATTERNS:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            debut_idx = match.start()
            logger.info(f"Début MOTIFS trouvé à position {debut_idx}")
            break

    if debut_idx is None:
        logger.warning("Aucun pattern de début MOTIFS trouvé")
        return None

    # Chercher fin des MOTIFS
    fin_idx = len(texte)
    for pattern in MOTIFS_FIN_PATTERNS:
        match = re.search(pattern, texte[debut_idx:], re.IGNORECASE)
        if match:
            fin_idx = debut_idx + match.end()
            logger.info(f"Fin MOTIFS trouvée à position {fin_idx}")
            break

    motifs = texte[debut_idx:fin_idx].strip()
    logger.info(f"Section MOTIFS extraite ({len(motifs)} caractères)")
    return motifs
