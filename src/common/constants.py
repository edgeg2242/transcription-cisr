"""
Constantes centralisées pour le pipeline de transcription CISR.

Nomenclature bilingue:
  SPR = RPD (Section Protection des Réfugiés / Refugee Protection Division)
  SAR = RAD (Section d'Appel des Réfugiés / Refugee Appeal Division)
  SI  = ID  (Section de l'Immigration / Immigration Division)
  SAI = IAD (Section d'Appel de l'Immigration / Immigration Appeal Division)
"""


class TypeTranscription:
    """Types de documents CISR — bilingue FR/EN."""
    SPR = "SPR"  # RPD — MC1/MC2/MC3/MC4
    SAR = "SAR"  # RAD — MC5/MC6
    SI = "SI"    # ID  — 0018-Cx-xxxxx
    SAI = "SAI"  # IAD — MC0

    # Mapping bilingue FR → EN
    FR_TO_EN = {
        "SPR": "RPD",
        "SAR": "RAD",
        "SI": "ID",
        "SAI": "IAD",
    }

    # Mapping EN → FR
    EN_TO_FR = {v: k for k, v in FR_TO_EN.items()}

    # Numéros dossier par type
    PREFIXES_DOSSIER = {
        "SPR": ["MC1", "MC2", "MC3", "MC4"],
        "SAR": ["MC5", "MC6"],
        "SI": ["0018"],
        "SAI": ["MC0"],
    }

    ALL_TYPES = [SPR, SAR, SI, SAI]


# ---------------------------------------------------------------------------
# Marges Word CISR (en pouces)
# ---------------------------------------------------------------------------

MARGINS_SPR = {
    "top": 1.25,
    "bottom": 0.63,
    "left": 0.50,
    "right": 0.50,
}

MARGINS_SAR = {
    "top": 0.89,
    "bottom": 1.00,
    "left": 1.00,
    "right": 1.00,
}

# SI et SAI: à confirmer avec référentiels (défaut = SPR pour l'instant)
MARGINS_SI = dict(MARGINS_SPR)
MARGINS_SAI = dict(MARGINS_SAR)

MARGINS_BY_TYPE = {
    TypeTranscription.SPR: MARGINS_SPR,
    TypeTranscription.SAR: MARGINS_SAR,
    TypeTranscription.SI: MARGINS_SI,
    TypeTranscription.SAI: MARGINS_SAI,
}

# ---------------------------------------------------------------------------
# Police et formatage
# ---------------------------------------------------------------------------

FONT_NAME = "Arial"
FONT_SIZE_PT = 11

# ---------------------------------------------------------------------------
# Structure tableaux métadonnées par type
# ---------------------------------------------------------------------------

# SPR: Tableau 1 = 17L × 3C (métadonnées bilingues avec lignes vides intercalaires)
#       Tableau 2 = 1L × 1C (séparateur)
# SAR: Tableau 1 = 1L × 2C (numéros dossiers seulement)
#       Tableau 2 = 15L × 3C (métadonnées bilingues)

TABLE_CONFIG = {
    TypeTranscription.SPR: {
        "tableau_1": {"rows": 17, "cols": 3},  # Métadonnées FR|Valeur|EN
        "tableau_2": {"rows": 1, "cols": 1},   # Séparateur
    },
    TypeTranscription.SAR: {
        "tableau_1": {"rows": 1, "cols": 2},   # Numéros dossiers
        "tableau_2": {"rows": 15, "cols": 3},  # Métadonnées FR|Valeur|EN
    },
}

# ---------------------------------------------------------------------------
# Titres documents par type
# ---------------------------------------------------------------------------

TITRE_SPR = "TRANSCRIPTION DES Motifs de la décision rendue de vive voix"
TITRE_SAR = "Transcription complète de l'audience"

# ---------------------------------------------------------------------------
# Locuteurs par type
# ---------------------------------------------------------------------------

LOCUTEURS_SPR = ["COMMISSAIRE"]

LOCUTEURS_SAR = [
    "COMMISSAIRE",
    "DEMANDEUR D'ASILE",
    "CONSEIL",
    "INTERPRÈTE",
    "REPRÉSENTANT DU MINISTRE",
]

LOCUTEURS_SI = [
    "COMMISSAIRE",
    "PERSONNE CONCERNÉE",
    "CONSEIL",
    "REPRÉSENTANT DU MINISTRE",
    "INTERPRÈTE",
]

LOCUTEURS_SAI = [
    "COMMISSAIRE",
    "APPELANT",
    "CONSEIL DE L'APPELANT",
    "REPRÉSENTANT DU MINISTRE",
    "INTERPRÈTE",
]

LOCUTEURS_BY_TYPE = {
    TypeTranscription.SPR: LOCUTEURS_SPR,
    TypeTranscription.SAR: LOCUTEURS_SAR,
    TypeTranscription.SI: LOCUTEURS_SI,
    TypeTranscription.SAI: LOCUTEURS_SAI,
}

# ---------------------------------------------------------------------------
# Patterns regex — Extraction MOTIFS (SPR seulement)
# ---------------------------------------------------------------------------

MOTIFS_DEBUT_PATTERNS = [
    r"Donc,?\s*j'ai eu aujourd'hui à examiner",
    r"Voici les? motifs? de (ma|la) décision",
    r"Ma décision aujourd'hui,?\s*c'est que",
    r"Je vais (maintenant|directement) vous donner (ma|les) décision",
    r"Je rends ma décision",
    r"Alors,?\s*voici (ma|les) décision",
    r"J'ai rendu ma décision",
    r"Je vous annonce ma décision",
]

MOTIFS_FIN_PATTERNS = [
    r"Merci pour votre témoignage",
    r"L'audience est (terminée|levée|ajournée)",
    r"Je vous remercie pour votre travail",
]

# ---------------------------------------------------------------------------
# Marqueurs de rupture de paragraphes
# ---------------------------------------------------------------------------

MARQUEURS_DEBUT_PARAGRAPHE = [
    "Donc,",
    "D'abord,",
    "Concernant",
    "Ma décision",
    "Advenant",
    "Vous avez",
    "Vous êtes",
    "On dit",
    "Parmi",
    "J'ai également",
    "J'ai aussi",
    "Tout cela",
    "En ce qui concerne",
    "Pour les raisons",
    "Finalement,",
    "En conclusion,",
    "Une fois",
    "Si vous",
]

PATTERNS_NUMEROTATION = [
    r"^Le premier ",
    r"^Le deuxième ",
    r"^Le troisième ",
    r"^Le dernier ",
    r"^Un des derniers ",
]

# ---------------------------------------------------------------------------
# Chemins par défaut
# ---------------------------------------------------------------------------

DICTIONNAIRE_PATH = "data/dictionaries/corrections_v2.1.json"
CACHE_COMMISSAIRES_PATH = "data/cache/commissaires_cisr.json"
TEMPLATE_SI_PATH = "data/templates/cover_page_SI_template.docx"
TEMPLATE_SIGNATURE_PATH = "data/templates/signature_certification.docx"
