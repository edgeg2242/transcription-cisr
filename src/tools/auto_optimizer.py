"""
Auto-optimisation itérative des transcriptions CISR.

Analyse les erreurs résiduelles et enrichit le dictionnaire de corrections
pour améliorer les scores faibles/moyens (< 85/100) sans intervention manuelle.

Stratégie :
1. Identifier patterns d'erreurs récurrents dans textes à faible score
2. Enrichir dictionnaire automatiquement avec règles validées (confiance >= 80%)
3. Re-exécuter corrections avec dictionnaire enrichi
4. Itérer jusqu'à score cible atteint (85+) ou max 3 itérations
"""

import os
import re
import copy
import json
import logging
from typing import List, Dict
from pathlib import Path

from src.common.logging_setup import fix_utf8_windows

fix_utf8_windows()
logger = logging.getLogger(__name__)


class AutoOptimiseur:
    """Optimisation automatique des transcriptions à faible score."""

    def __init__(self, dictionnaire_path: str):
        self.dictionnaire_path = dictionnaire_path
        self.dictionnaire = self._charger_dictionnaire()

    def _charger_dictionnaire(self) -> dict:
        """Charger dictionnaire existant."""
        with open(self.dictionnaire_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyser_erreurs_residuelles(self, transcription_path: str, score: int) -> List[Dict]:
        """
        Analyser transcription pour détecter patterns d'erreurs récurrents.

        Stratégies :
        1. Termes juridiques mal formés (regex)
        2. Homophones courants français
        3. Accents manquants
        4. Expressions mal transcrites

        Returns:
            Liste de corrections candidates avec score confiance (>= 0.8)
        """
        with open(transcription_path, 'r', encoding='utf-8') as f:
            texte = f.read()

        corrections_candidates = []
        corrections_candidates.extend(self._detecter_termes_juridiques_errones(texte))
        corrections_candidates.extend(self._detecter_homophones(texte))
        corrections_candidates.extend(self._detecter_accents_manquants(texte))
        corrections_candidates.extend(self._detecter_expressions_erronees(texte))

        return [c for c in corrections_candidates if c['confiance'] >= 0.8]

    def _detecter_termes_juridiques_errones(self, texte: str) -> List[Dict]:
        """Détecter termes juridiques mal formés."""
        corrections = []

        for match in re.finditer(r'\barticle\s+(\d+)\b', texte, re.IGNORECASE):
            numero = match.group(1)
            if numero not in ['96', '97']:
                corrections.append({
                    'incorrect': match.group(0), 'correct': 'article 96',
                    'confiance': 0.95, 'type': 'terme_juridique',
                    'raison': f"Article {numero} non standard CISR"
                })

        for match in re.finditer(r'\bparagraphe\s+(\d+)\b(?!\()', texte, re.IGNORECASE):
            if match.group(1) == '97':
                corrections.append({
                    'incorrect': match.group(0), 'correct': 'paragraphe 97(1)',
                    'confiance': 0.90, 'type': 'terme_juridique',
                    'raison': 'Paragraphe 97 nécessite (1)'
                })

        if re.search(r'Loi sur l\'Immigration', texte):
            for match in re.finditer(r'\b(?:de|selon|en vertu de)\s+la\s+loi\b', texte):
                corrections.append({
                    'incorrect': match.group(0),
                    'correct': match.group(0).replace('la loi', 'la Loi'),
                    'confiance': 0.85, 'type': 'terme_juridique',
                    'raison': 'Loi requiert majuscule'
                })

        return corrections

    def _detecter_homophones(self, texte: str) -> List[Dict]:
        """Détecter homophones courants mal transcrits."""
        corrections = []

        if re.search(r'\bcartel\s+national\b', texte, re.IGNORECASE):
            corrections.append({
                'incorrect': 'cartel national de documentation',
                'correct': 'Cartable national de documentation',
                'confiance': 0.95, 'type': 'homophone',
                'raison': 'Cartable (classeur) vs cartel'
            })

        return corrections

    def _detecter_accents_manquants(self, texte: str) -> List[Dict]:
        """Détecter accents manquants sur mots courants."""
        corrections = []

        patterns_accents = {
            r'\bEtat\b': ('État', 0.95, 'État requiert accent'),
            r'\ba\s+raison\s+de\b': ('en raison de', 0.95, 'Expression: en raison de'),
        }

        for pattern, (correct, confiance, raison) in patterns_accents.items():
            match = re.search(pattern, texte)
            if match:
                corrections.append({
                    'incorrect': match.group(0), 'correct': correct,
                    'confiance': confiance, 'type': 'accent_manquant',
                    'raison': raison
                })

        return corrections

    def _detecter_expressions_erronees(self, texte: str) -> List[Dict]:
        """Détecter expressions françaises mal transcrites."""
        corrections = []

        if re.search(r'\ben\s+virtu\b', texte, re.IGNORECASE):
            corrections.append({
                'incorrect': 'en virtu', 'correct': 'en vertu',
                'confiance': 1.0, 'type': 'faute_orthographe',
                'raison': 'Orthographe correcte: en vertu'
            })

        return corrections

    def enrichir_dictionnaire(self, corrections: List[Dict]) -> tuple:
        """
        Enrichir dictionnaire avec corrections validées.

        Returns:
            (nouveau_dictionnaire, nombre_ajouts)
        """
        nouveau_dict = copy.deepcopy(self.dictionnaire)
        nb_ajouts = 0

        type_to_pass = {
            'terme_juridique': 'pass1_termes_juridiques',
            'expression_juridique': 'pass1_termes_juridiques',
            'homophone': 'pass2_noms_propres_accents',
            'accent_manquant': 'pass2_noms_propres_accents',
            'accord_grammatical': 'pass3_accords_grammaticaux',
            'faute_orthographe': 'pass4_mots_mal_reconnus',
        }

        for correction in corrections:
            incorrect = correction['incorrect']
            correct = correction['correct']
            cle_pass = type_to_pass.get(correction['type'], 'pass4_mots_mal_reconnus')

            if cle_pass not in nouveau_dict:
                nouveau_dict[cle_pass] = {}

            if incorrect not in nouveau_dict[cle_pass]:
                nouveau_dict[cle_pass][incorrect] = correct
                nb_ajouts += 1
                logger.info(f"  Ajouté: '{incorrect}' -> '{correct}'")

        return nouveau_dict, nb_ajouts

    def sauvegarder_dictionnaire(self, dictionnaire: dict, backup: bool = True):
        """Sauvegarder dictionnaire enrichi avec backup automatique."""
        if backup:
            backup_path = self.dictionnaire_path.replace('.json', '_backup.json')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.dictionnaire, f, ensure_ascii=False, indent=2)
            logger.info(f"Backup créé: {backup_path}")

        with open(self.dictionnaire_path, 'w', encoding='utf-8') as f:
            json.dump(dictionnaire, f, ensure_ascii=False, indent=2)
        logger.info(f"Dictionnaire sauvegardé: {self.dictionnaire_path}")
