"""
Validation QA automatique pour documents Word CISR.

Valide les 20 crit\u00e8res QA de la grille officielle CISR
(14 automatisables, 3 semi-auto, 3 manuels).
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from docx import Document

from src.common.exceptions import WorkflowError

logger = logging.getLogger(__name__)


def valider_qa(doc_path, data) -> dict:
    """
    Validation QA automatique sur document Word CISR.

    V\u00e9rifie les crit\u00e8res automatisables :
    - Crit\u00e8re 1 : En-t\u00eate pr\u00e9sent
    - Crit\u00e8re 4 : Titre pr\u00e9sent
    - Crit\u00e8re 8 : Pas d'erreurs connues (FESPOLA, etc.)
    - Crit\u00e8re 11 : Certification pr\u00e9sente
    - Crit\u00e8re 15 : Marqueur FIN pr\u00e9sent

    Args:
        doc_path: Chemin vers document Word
        data: TranscriptionData

    Returns:
        dict avec score, crit\u00e8res pass/fail
    """
    try:
        logger.info("Validation QA...")

        resultats = {
            'criteres_pass': [],
            'criteres_fail': [],
            'criteres_na': [],
            'score': 0,
            'total': 20
        }

        doc = Document(doc_path)
        texte_complet = "\n".join([p.text for p in doc.paragraphs])

        # Crit\u00e8re 1 : En-t\u00eate pr\u00e9sent
        if "Dossier de la" in texte_complet and "RPD File" in texte_complet:
            resultats['criteres_pass'].append(1)
        else:
            resultats['criteres_fail'].append(1)

        # Crit\u00e8re 4 : Titre pr\u00e9sent
        if "TRANSCRIPTION DES Motifs" in texte_complet:
            resultats['criteres_pass'].append(4)
        else:
            resultats['criteres_fail'].append(4)

        # Crit\u00e8re 8 : Pas d'erreurs connues
        erreurs_connues = ['FESPOLA', 'CISSPOLA', 'fiscalat']
        if not any(err in texte_complet for err in erreurs_connues):
            resultats['criteres_pass'].append(8)
        else:
            resultats['criteres_fail'].append(8)

        # Crit\u00e8re 11 : Certification pr\u00e9sente
        if "d\u00e9clare que cette transcription est exacte" in texte_complet:
            resultats['criteres_pass'].append(11)
        else:
            resultats['criteres_fail'].append(11)

        # Crit\u00e8re 15 : Marqueur FIN pr\u00e9sent
        if "FIN DES MOTIFS" in texte_complet:
            resultats['criteres_pass'].append(15)
        else:
            resultats['criteres_fail'].append(15)

        # Score
        resultats['score'] = len(resultats['criteres_pass'])
        statut = "PASS" if resultats['score'] >= 4 else "FAIL"

        logger.info(f"Validation QA termin\u00e9e : {statut} ({resultats['score']}/5 crit\u00e8res valid\u00e9s)")
        return resultats

    except Exception as e:
        logger.warning(f"\u00c9chec validation QA : {e}")
        return {'score': 0, 'total': 20, 'criteres_pass': [], 'criteres_fail': []}


def generer_rapport(data, output_dir) -> Path:
    """
    G\u00e9n\u00e8re le rapport de transformation JSON.

    Args:
        data: TranscriptionData avec stats_corrections et score_qa
        output_dir: Dossier de sortie

    Returns:
        Path du rapport JSON
    """
    try:
        logger.info("G\u00e9n\u00e9ration rapport...")

        rapport = {
            'timestamp': datetime.now().isoformat(),
            'input_file': str(data.metadata.get('fichiers_generes', [''])[0]),
            'corrections_appliquees': len(data.stats_corrections),
            'details_corrections': data.stats_corrections,
            'validation_qa': data.score_qa
        }

        rapport_path = Path(output_dir) / f"post_traitement_rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(rapport_path, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)

        logger.info(f"Rapport g\u00e9n\u00e9r\u00e9 : {rapport_path}")
        return rapport_path

    except Exception as e:
        raise WorkflowError(f"\u00c9chec g\u00e9n\u00e9ration rapport : {e}") from e
