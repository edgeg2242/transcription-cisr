"""
Mapping des locuteurs pour les transcriptions CISR.

Associe les labels AssemblyAI (Speaker A, B, C...) aux r\u00f4les CISR
(COMMISSAIRE, DEMANDEUR, CONSEIL, etc.) selon des heuristiques.
"""

import re
import logging
from typing import Dict, List

from src.common.constants import TypeTranscription, LOCUTEURS_BY_TYPE, MARQUEURS_DEBUT_PARAGRAPHE

logger = logging.getLogger(__name__)


def mapper_locuteurs(interventions: Dict[str, str], args) -> Dict[str, str]:
    """
    Mappe les labels AssemblyAI vers les r\u00f4les CISR.

    Heuristiques :
    - Le locuteur avec le plus de texte = COMMISSAIRE (SPR)
    - Mapping par ordre pour SAR/SI/SAI (bas\u00e9 sur locuteurs attendus)

    Args:
        interventions: {label_assemblyai: texte} ex: {'A': '...', 'B': '...'}
        args: Arguments CLI contenant section (SPR/SAR/SI/SAI)

    Returns:
        {label_assemblyai: role_cisr} ex: {'A': 'COMMISSAIRE', 'B': 'DEMANDEUR'}
    """
    logger.info("Mapping des locuteurs...")

    section = getattr(args, 'section', 'SPR')
    locuteurs_attendus = LOCUTEURS_BY_TYPE.get(section, ['COMMISSAIRE'])

    if not interventions:
        logger.warning("Aucune intervention \u00e0 mapper")
        return {}

    # Trier locuteurs par volume de texte (d\u00e9croissant)
    locuteurs_tries = sorted(
        interventions.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    mapping = {}

    if section == 'SPR':
        # SPR : 1 seul locuteur (COMMISSAIRE) \u2014 le plus prolixe
        mapping[locuteurs_tries[0][0]] = 'COMMISSAIRE'
        for label, _ in locuteurs_tries[1:]:
            mapping[label] = 'AUTRE'
    else:
        # SAR/SI/SAI : Multi-locuteurs
        for i, (label, _texte) in enumerate(locuteurs_tries):
            if i < len(locuteurs_attendus):
                mapping[label] = locuteurs_attendus[i]
            else:
                mapping[label] = f'LOCUTEUR_{label}'

    for label, role in mapping.items():
        volume = len(interventions.get(label, ''))
        logger.info(f"  {label} -> {role} ({volume} caract\u00e8res)")

    return mapping


def structurer_dialogue(texte: str, mapping: Dict[str, str]) -> str:
    """
    Applique le mapping des locuteurs au texte pour cr\u00e9er le dialogue structur\u00e9.

    Args:
        texte: Texte corrig\u00e9
        mapping: {label: role} mapping des locuteurs

    Returns:
        Texte avec r\u00f4les CISR au lieu de labels AssemblyAI
    """
    texte_structure = texte

    for label, role in mapping.items():
        patterns = [
            (f"Speaker {label}:", f"{role} :"),
            (f"Locuteur {label}:", f"{role} :"),
            (f"LOCUTEUR {label}:", f"{role} :"),
        ]
        for old, new in patterns:
            texte_structure = texte_structure.replace(old, new)

    return texte_structure


def creer_paragraphes(texte: str) -> List[str]:
    """
    D\u00e9coupe le texte structur\u00e9 en paragraphes Word.

    Args:
        texte: Texte structur\u00e9 avec r\u00f4les CISR

    Returns:
        Liste de paragraphes
    """
    logger.info("Cr\u00e9ation des paragraphes...")

    paragraphes = []
    lignes = texte.split('\n')
    paragraphe_courant = []

    roles_cisr = ['COMMISSAIRE', 'DEMANDEUR', 'CONSEIL', 'INTERPR\u00c8TE',
                  'REPR\u00c9SENTANT', 'PERSONNE CONCERN\u00c9E', 'APPELANT']

    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            if paragraphe_courant:
                paragraphes.append(' '.join(paragraphe_courant))
                paragraphe_courant = []
            continue

        # Nouveau paragraphe si marqueur de d\u00e9but d\u00e9tect\u00e9
        est_nouveau = False
        for marqueur in MARQUEURS_DEBUT_PARAGRAPHE:
            if ligne.startswith(marqueur):
                if paragraphe_courant:
                    paragraphes.append(' '.join(paragraphe_courant))
                    paragraphe_courant = []
                est_nouveau = True
                break

        # Nouveau paragraphe si changement de locuteur
        if not est_nouveau and ':' in ligne[:40]:
            for role in roles_cisr:
                if ligne.startswith(f"{role} :"):
                    if paragraphe_courant:
                        paragraphes.append(' '.join(paragraphe_courant))
                        paragraphe_courant = []
                    break

        paragraphe_courant.append(ligne)

    if paragraphe_courant:
        paragraphes.append(' '.join(paragraphe_courant))

    logger.info(f"Paragraphes cr\u00e9\u00e9s : {len(paragraphes)}")
    return paragraphes
