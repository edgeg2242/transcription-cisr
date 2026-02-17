"""
Détection et formatage des titres de sections CISR.

Détecte les titres de sections dans les transcriptions
et prépare le formatage gras pour le document Word.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Patterns de titres de sections CISR
TITRE_PATTERNS = [
    # Titres explicites en majuscules
    r'^(MOTIFS ET DÉCISION|MOTIFS DE LA DÉCISION)\s*$',
    r'^(DÉCISION|DECISION)\s*$',
    r'^(ANALYSE|CONCLUSION|INTRODUCTION)\s*$',
    r'^(ALLÉGATIONS|ALLEGATIONS)\s*$',
    r'^(QUESTIONS EN LITIGE|QUESTION EN LITIGE)\s*$',
    r'^(CONTEXTE|FAITS)\s*$',
    r'^(PREUVE DOCUMENTAIRE|PREUVES DOCUMENTAIRES)\s*$',
    r'^(CRÉDIBILITÉ|CREDIBILITE)\s*$',
    r'^(PROTECTION DE L\'ÉTAT|PROTECTION DE L.ÉTAT)\s*$',
    r'^(POSSIBILITÉ DE REFUGE INTÉRIEUR|PRI)\s*$',
    r'^(IDENTITÉ|IDENTITE)\s*$',
    r'^(RISQUE GÉNÉRALISÉ|RISQUE GENERALISE)\s*$',
    r'^(AGENT DE PERSÉCUTION|AGENT DE PERSECUTION)\s*$',
    r'^(LIEN AVEC UN MOTIF DE LA CONVENTION)\s*$',
    # Numérotation avec titres
    r'^[IVX]+\.\s+[A-ZÉÈÊÀÂÔÎÙÛÇ]',
    r'^\d+\.\s+[A-ZÉÈÊÀÂÔÎÙÛÇ]{2,}',
    # Titres entre tirets
    r'^-{3,}\s*.+\s*-{3,}$',
]

# Patterns compilés pour performance
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TITRE_PATTERNS]


def detecter_titre_section(texte: str) -> Tuple[bool, str]:
    """
    Détecte si un paragraphe est un titre de section.

    Args:
        texte: Texte du paragraphe à analyser

    Returns:
        (est_titre, nom_titre) — True si c'est un titre, avec le nom nettoyé
    """
    texte_strip = texte.strip()

    if not texte_strip:
        return False, ''

    # Vérifier contre les patterns
    for pattern in _COMPILED_PATTERNS:
        if pattern.match(texte_strip):
            return True, texte_strip

    # Heuristique : ligne courte tout en majuscules (> 3 chars)
    if (len(texte_strip) > 3 and len(texte_strip) < 80
            and texte_strip == texte_strip.upper()
            and not texte_strip.startswith(('COMMISSAIRE', 'DEMANDEUR', 'CONSEIL', 'INTERPRÈTE', 'REPRÉSENTANT'))):
        return True, texte_strip

    return False, ''
