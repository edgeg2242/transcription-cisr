"""
Validation des metadonnees extraites.
"""
import re
import logging
from src.common.exceptions import WorkOrderError

logger = logging.getLogger(__name__)


def valider_metadonnees_spr(metadonnees):
    """
    Validation des metadonnees SPR extraites.

    Verifications:
    - Champs obligatoires presents
    - Numero dossier au bon format
    - IUC 10 chiffres (si present)

    Args:
        metadonnees: Dict metadonnees a valider

    Raises:
        WorkOrderError: Si validation echoue
    """
    champs_obligatoires = [
        'numero_dossier', 'demandeur', 'commissaire',
        'date_audience', 'lieu_audience'
    ]

    for champ in champs_obligatoires:
        if not metadonnees.get(champ):
            raise WorkOrderError(f"Champ obligatoire manquant: {champ}")

    # Valider format numero dossier
    if not re.match(r'[A-Z]{2}\d-\d+', metadonnees['numero_dossier']):
        raise WorkOrderError(
            f"Format numero dossier invalide: {metadonnees['numero_dossier']}"
        )

    # Valider IUC (si present)
    if metadonnees.get('iuc') and not re.match(r'\d{10}', metadonnees['iuc']):
        raise WorkOrderError(
            f"Format IUC invalide: {metadonnees['iuc']}"
        )

    logger.info("Validation metadonnees reussie")
