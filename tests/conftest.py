"""
Fixtures pytest communes pour les tests du pipeline CISR.
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Retourne le chemin racine du projet."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root):
    """Retourne le chemin du dossier data/."""
    return project_root / "data"


@pytest.fixture
def sample_metadata():
    """Métadonnées SPR minimales pour tests."""
    return {
        "numero_dossier": "MC3-16722",
        "type_transcription": "SPR",
        "demandeur": "Victoria AGUILAR ROMERO",
        "commissaire": "Jane Smith",
        "date_audience": "2025-12-09",
        "date_decision": "2025-12-09",
        "iuc": "1234567890",
        "huis_clos": False,
        "interpretes": [],
        "conseils": [],
        "audio_file": "6722.a00",
        "duree_audio_minutes": 11,
        "work_order_number": "RCE-9878-AA",
        "region": "EASTERN",
        "dossier": {"numero": "MC3-16722", "section": "SPR"},
        "participants": {
            "demandeur": "Victoria AGUILAR ROMERO",
            "commissaire": "Jane Smith",
            "conseil_demandeur": "",
            "interprete": ""
        },
        "audience": {
            "date": "9 décembre 2025",
            "lieu": "Montréal",
            "date_decision": "9 décembre 2025"
        }
    }


@pytest.fixture
def sample_metadata_sar():
    """Métadonnées SAR minimales pour tests."""
    return {
        "numero_dossier": "MC5-40476",
        "type_transcription": "SAR",
        "dossier": {"numero": "MC5-40476", "section": "SAR"},
        "participants": {
            "demandeur": "Ahmed HASSAN",
            "commissaire": "Marie Dupont",
            "conseil_demandeur": "Me Robert Tremblay",
            "representant_ministre": "Me Julie Martin",
            "interprete": "Fatima Nour"
        },
        "audience": {
            "date": "15 janvier 2026",
            "lieu": "Toronto"
        }
    }


@pytest.fixture
def sample_transcription_brute():
    """Transcription brute minimale pour tests."""
    separator = "=" * 70
    return (
        f"TEXTE INTEGRAL\n{separator}\n"
        "Donc, j'ai eu aujourd'hui à examiner la demande d'asile de Madame "
        "Victoria Aguilar Romero, citoyenne du Mexique. Après analyse de la "
        "preuve documentaire et du témoignage, j'accueille la demande d'asile. "
        "Voici les motifs de ma décision. L'audience est terminée. "
        "Merci pour votre témoignage.\n"
        f"{separator}\n"
        f"TRANSCRIPTION PAR LOCUTEUR\n{separator}\n\n"
        f"{separator}\nLOCUTEUR A\n{separator}\n"
        "Donc, j'ai eu aujourd'hui à examiner la demande d'asile.\n"
    )


@pytest.fixture
def sample_dictionnaire():
    """Dictionnaire de corrections minimal pour tests."""
    return {
        "version": "2.1",
        "pass1_termes_juridiques": {
            "article 87": "article 96",
            "en virtu": "en vertu"
        },
        "pass2_noms_propres_accents": {
            "Etat": "État",
            "Michoacan": "Michoacán"
        },
        "pass3_accords_grammaticaux": {
            "citoyen": "citoyenne"
        },
        "pass4_mots_mal_reconnus": {
            "affairement": "avortement"
        },
        "suppressions": []
    }
