#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow 1.6 : Auto-Optimisation Itérative

Analyse automatique des erreurs résiduelles et enrichissement du dictionnaire
pour améliorer les scores faibles/moyens (< 85/100) sans intervention manuelle.

Stratégie:
1. Identifier patterns d'erreurs récurrents dans textes à faible score
2. Enrichir dictionnaire automatiquement avec règles validées
3. Re-exécuter Workflow 1.5 avec dictionnaire enrichi
4. Itérer jusqu'à score cible atteint (85+) ou max 3 itérations
"""

import sys
import os
import copy
import json
import re
from typing import List, Dict, Tuple
from pathlib import Path
from collections import Counter

# Fix encoding Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import Workflow 1.5
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AutoOptimiseur:
    """Optimisation automatique des transcriptions à faible score"""

    def __init__(self, dictionnaire_path: str):
        self.dictionnaire_path = dictionnaire_path
        self.dictionnaire = self._charger_dictionnaire()

    def _charger_dictionnaire(self) -> dict:
        """Charger dictionnaire existant"""
        with open(self.dictionnaire_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyser_erreurs_residuelles(self, transcription_path: str, score: int) -> List[Dict]:
        """
        Analyser transcription pour détecter patterns d'erreurs récurrents.

        Stratégies de détection:
        1. Termes juridiques mal formés (regex patterns)
        2. Homophones courants français (cartel/cartable, etc.)
        3. Accents manquants sur noms propres
        4. Expressions françaises mal transcrites

        Returns:
            Liste de corrections candidates avec score confiance
        """
        with open(transcription_path, 'r', encoding='utf-8') as f:
            texte = f.read()

        corrections_candidates = []

        # STRATÉGIE 1: Termes juridiques mal formés
        corrections_candidates.extend(self._detecter_termes_juridiques_errones(texte))

        # STRATÉGIE 2: Homophones courants
        corrections_candidates.extend(self._detecter_homophones(texte))

        # STRATÉGIE 3: Accents manquants (É, È, À, Ç)
        corrections_candidates.extend(self._detecter_accents_manquants(texte))

        # STRATÉGIE 4: Expressions mal transcrites
        corrections_candidates.extend(self._detecter_expressions_erronees(texte))

        # Filtrer par score confiance (seuil: 80%)
        corrections_validees = [c for c in corrections_candidates if c['confiance'] >= 0.8]

        return corrections_validees

    def _detecter_termes_juridiques_errones(self, texte: str) -> List[Dict]:
        """Détecter termes juridiques mal formés avec patterns regex"""
        corrections = []

        # Pattern: "article XX" où XX != 96
        pattern_article = re.finditer(r'\barticle\s+(\d+)\b', texte, re.IGNORECASE)
        for match in pattern_article:
            numero = match.group(1)
            if numero not in ['96', '97']:
                corrections.append({
                    'incorrect': match.group(0),
                    'correct': 'article 96',
                    'confiance': 0.95,
                    'type': 'terme_juridique',
                    'raison': f"Article {numero} non standard CISR (96/97 attendus)"
                })

        # Pattern: "paragraphe XX" sans (1)
        pattern_paragraphe = re.finditer(r'\bparagraphe\s+(\d+)\b(?!\()', texte, re.IGNORECASE)
        for match in pattern_paragraphe:
            numero = match.group(1)
            if numero == '97':
                corrections.append({
                    'incorrect': match.group(0),
                    'correct': 'paragraphe 97(1)',
                    'confiance': 0.90,
                    'type': 'terme_juridique',
                    'raison': 'Paragraphe 97 nécessite (1)'
                })

        # Pattern: "la loi" sans majuscule après mention complète
        if re.search(r'Loi sur l\'Immigration', texte):
            pattern_loi = re.finditer(r'\b(?:de|selon|en vertu de)\s+la\s+loi\b', texte)
            for match in pattern_loi:
                corrections.append({
                    'incorrect': match.group(0),
                    'correct': match.group(0).replace('la loi', 'la Loi'),
                    'confiance': 0.85,
                    'type': 'terme_juridique',
                    'raison': 'Loi requiert majuscule (référence législative)'
                })

        return corrections

    def _detecter_homophones(self, texte: str) -> List[Dict]:
        """Détecter homophones courants mal transcrits"""
        corrections = []

        # Homophone: "cartel" → "cartable" (Cartable national de documentation)
        if re.search(r'\bcartel\s+national\b', texte, re.IGNORECASE):
            corrections.append({
                'incorrect': 'cartel national de documentation',
                'correct': 'Cartable national de documentation',
                'confiance': 0.95,
                'type': 'homophone',
                'raison': 'Cartable (classeur) vs cartel (organisation criminelle)'
            })

        # Homophone: "soit" → "doit" (contexte modal)
        pattern_soit = re.finditer(r'\b(qu\'il|qu\'elle|qui)\s+soit\s+(être|avoir|faire|démontrer|prouver)\b', texte)
        for match in pattern_soit:
            corrections.append({
                'incorrect': 'soit',
                'correct': 'doit',
                'confiance': 0.90,
                'type': 'homophone',
                'raison': 'Contexte modal (obligation) → doit'
            })

        return corrections

    def _detecter_accents_manquants(self, texte: str) -> List[Dict]:
        """Détecter accents manquants sur mots courants"""
        corrections = []

        # Mots courants sans accent
        patterns_accents = {
            r'\bEtat\b': ('État', 0.95, 'État (pays) requiert majuscule + accent'),
            r'\bMexique\b(?=\s*,)': ('Mexique', 0.90, 'Pays: Mexique (peut avoir accent régional)'),
            r'\ba\s+raison\s+de\b': ('en raison de', 0.95, 'Expression: "en raison de" (causalité)'),
        }

        for pattern, (correct, confiance, raison) in patterns_accents.items():
            if re.search(pattern, texte):
                match = re.search(pattern, texte)
                corrections.append({
                    'incorrect': match.group(0),
                    'correct': correct,
                    'confiance': confiance,
                    'type': 'accent_manquant',
                    'raison': raison
                })

        return corrections

    def _detecter_expressions_erronees(self, texte: str) -> List[Dict]:
        """Détecter expressions françaises mal transcrites"""
        corrections = []

        # Expression: "Si vous reveniez" → "Advenant votre retour" (style juridique)
        if re.search(r'\bSi\s+vous\s+(reveniez|retourniez)\b', texte, re.IGNORECASE):
            corrections.append({
                'incorrect': 'Si vous reveniez',
                'correct': 'Advenant votre retour',
                'confiance': 0.85,
                'type': 'expression_juridique',
                'raison': 'Style juridique CISR: "advenant" (conditionnel formel)'
            })

        # Expression: "en virtu" → "en vertu" (faute orthographe courante)
        if re.search(r'\ben\s+virtu\b', texte, re.IGNORECASE):
            corrections.append({
                'incorrect': 'en virtu',
                'correct': 'en vertu',
                'confiance': 1.0,
                'type': 'faute_orthographe',
                'raison': 'Orthographe correcte: "en vertu"'
            })

        return corrections

    def enrichir_dictionnaire(self, corrections: List[Dict]) -> dict:
        """
        Enrichir dictionnaire avec corrections validées.

        Évite les doublons et les conflits avec entrées existantes.
        """
        nouveau_dict = copy.deepcopy(self.dictionnaire)
        ajouts_par_pass = {'pass1': 0, 'pass2': 0, 'pass3': 0, 'pass4': 0}

        for correction in corrections:
            incorrect = correction['incorrect']
            correct = correction['correct']
            type_correction = correction['type']

            # Mapper type → pass
            if type_correction in ['terme_juridique', 'expression_juridique']:
                cle_pass = 'pass1_termes_juridiques'
                pass_num = 'pass1'
            elif type_correction in ['homophone', 'accent_manquant']:
                cle_pass = 'pass2_noms_propres_accents'
                pass_num = 'pass2'
            elif type_correction == 'accord_grammatical':
                cle_pass = 'pass3_accords_grammaticaux'
                pass_num = 'pass3'
            else:  # faute_orthographe, etc.
                cle_pass = 'pass4_mots_mal_reconnus'
                pass_num = 'pass4'

            # Vérifier doublon
            if incorrect not in nouveau_dict[cle_pass]:
                nouveau_dict[cle_pass][incorrect] = correct
                ajouts_par_pass[pass_num] += 1
                print(f"   ✅ Ajouté: '{incorrect}' → '{correct}' ({type_correction})")
            else:
                # Vérifier conflit
                if nouveau_dict[cle_pass][incorrect] != correct:
                    print(f"   ⚠️  CONFLIT: '{incorrect}' existe déjà ('{nouveau_dict[cle_pass][incorrect]}' vs '{correct}')")

        # Mettre à jour méta-données
        nouveau_dict['total_entrees'] = sum(len(nouveau_dict[f'pass{i}_{"termes_juridiques" if i==1 else "noms_propres_accents" if i==2 else "accords_grammaticaux" if i==3 else "mots_mal_reconnus"}']) for i in range(1, 5))
        nouveau_dict['version'] = f"{float(nouveau_dict['version']) + 0.1:.1f}"
        nouveau_dict['derniere_mise_a_jour'] = "2026-01-07"

        print(f"\n📊 Enrichissement: {sum(ajouts_par_pass.values())} nouvelles entrées")
        for pass_num, count in ajouts_par_pass.items():
            if count > 0:
                print(f"   {pass_num}: +{count} entrées")

        return nouveau_dict, sum(ajouts_par_pass.values())

    def sauvegarder_dictionnaire(self, dictionnaire: dict, backup: bool = True):
        """Sauvegarder dictionnaire enrichi avec backup automatique"""
        if backup:
            backup_path = self.dictionnaire_path.replace('.json', f'_v{dictionnaire["version"]}_backup.json')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.dictionnaire, f, ensure_ascii=False, indent=2)
            print(f"💾 Backup créé: {backup_path}")

        with open(self.dictionnaire_path, 'w', encoding='utf-8') as f:
            json.dump(dictionnaire, f, ensure_ascii=False, indent=2)
        print(f"✅ Dictionnaire sauvegardé: {self.dictionnaire_path}")


def optimiser_automatiquement(
    transcription_brute_path: str,
    metadata_path: str,
    dictionnaire_path: str,
    output_dir: str,
    score_cible: int = 85,
    max_iterations: int = 3
) -> Dict:
    """
    Optimisation automatique itérative pour atteindre score cible.

    Workflow:
    1. Exécuter Workflow 1.5 avec dictionnaire actuel
    2. Si score < cible: analyser erreurs résiduelles
    3. Enrichir dictionnaire automatiquement
    4. Re-exécuter Workflow 1.5
    5. Répéter jusqu'à score cible ou max_iterations

    Returns:
        Rapport final avec métriques d'amélioration
    """
    import subprocess

    print("=" * 70)
    print("WORKFLOW 1.6 : AUTO-OPTIMISATION ITÉRATIVE")
    print("=" * 70)

    optimiseur = AutoOptimiseur(dictionnaire_path)
    iteration = 0
    score_actuel = 0
    historique = []

    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 ITÉRATION {iteration}/{max_iterations}")
        print("-" * 70)

        # Exécuter Workflow 1.5
        output_transcription = os.path.join(output_dir, f"transcription_corrigee_iter{iteration}.txt")
        output_rapport = os.path.join(output_dir, f"rapport_corrections_iter{iteration}.json")

        cmd = [
            'python', 'implementation/transcription_corrections_intelligentes.py',
            '--input', transcription_brute_path,
            '--dictionnaire', dictionnaire_path,
            '--metadata', metadata_path,
            '--output', output_transcription,
            '--rapport', output_rapport
        ]

        print(f"🔍 Exécution Workflow 1.5 (itération {iteration})...")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            print(f"❌ Erreur Workflow 1.5: {result.stderr}")
            break

        # Lire score
        with open(output_rapport, 'r', encoding='utf-8') as f:
            rapport = json.load(f)

        score_actuel = rapport['qualite']['score']
        corrections_appliquees = rapport['statistiques']['total_corrections']

        print(f"✅ Score: {score_actuel}/100 ({corrections_appliquees} corrections)")

        historique.append({
            'iteration': iteration,
            'score': score_actuel,
            'corrections': corrections_appliquees,
            'niveau': rapport['qualite']['niveau']
        })

        # Vérifier si score cible atteint
        if score_actuel >= score_cible:
            print(f"\n🎯 OBJECTIF ATTEINT: Score {score_actuel}/100 ≥ {score_cible}/100")
            break

        # Si dernière itération, ne pas enrichir
        if iteration == max_iterations:
            print(f"\n⏭️  Itérations max atteintes ({max_iterations})")
            break

        # Analyser erreurs résiduelles
        print(f"\n🔍 Analyse erreurs résiduelles...")
        corrections_candidates = optimiseur.analyser_erreurs_residuelles(
            output_transcription,
            score_actuel
        )

        if not corrections_candidates:
            print(f"   ℹ️  Aucune erreur résiduelle automatiquement détectable")
            break

        print(f"   ✓ {len(corrections_candidates)} corrections candidates détectées")

        # Enrichir dictionnaire
        print(f"\n📝 Enrichissement dictionnaire...")
        nouveau_dict, nb_ajouts = optimiseur.enrichir_dictionnaire(corrections_candidates)

        if nb_ajouts == 0:
            print(f"   ℹ️  Aucune nouvelle entrée (toutes déjà présentes)")
            break

        # Sauvegarder dictionnaire enrichi
        optimiseur.sauvegarder_dictionnaire(nouveau_dict, backup=True)
        optimiseur.dictionnaire = nouveau_dict  # Mettre à jour instance

        print(f"\n➡️  Itération suivante avec dictionnaire enrichi...")

    # Rapport final
    print("\n" + "=" * 70)
    print("RÉSULTAT AUTO-OPTIMISATION")
    print("=" * 70)

    amelioration = score_actuel - historique[0]['score'] if len(historique) > 1 else 0

    print(f"\n📊 Progression:")
    for h in historique:
        print(f"   Itération {h['iteration']}: {h['score']}/100 ({h['niveau']}) - {h['corrections']} corrections")

    print(f"\n🎯 Résultat final:")
    print(f"   Score final: {score_actuel}/100")
    print(f"   Amélioration: +{amelioration} points")
    print(f"   Itérations: {iteration}")
    print(f"   Statut: {'✅ OBJECTIF ATTEINT' if score_actuel >= score_cible else '⚠️  Score cible non atteint'}")

    return {
        'score_final': score_actuel,
        'amelioration': amelioration,
        'iterations': iteration,
        'historique': historique,
        'objectif_atteint': score_actuel >= score_cible
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Workflow 1.6 : Auto-Optimisation Itérative')
    parser.add_argument('--input', required=True, help='Fichier transcription brute (.txt)')
    parser.add_argument('--metadata', required=True, help='Fichier metadata_work_order.json')
    parser.add_argument('--dictionnaire', required=True, help='Chemin dictionnaire corrections')
    parser.add_argument('--output-dir', required=True, help='Dossier sortie')
    parser.add_argument('--score-cible', type=int, default=85, help='Score cible à atteindre (défaut: 85)')
    parser.add_argument('--max-iterations', type=int, default=3, help='Nombre max itérations (défaut: 3)')

    args = parser.parse_args()

    # Créer dossier sortie
    os.makedirs(args.output_dir, exist_ok=True)

    # Exécuter optimisation
    resultat = optimiser_automatiquement(
        transcription_brute_path=args.input,
        metadata_path=args.metadata,
        dictionnaire_path=args.dictionnaire,
        output_dir=args.output_dir,
        score_cible=args.score_cible,
        max_iterations=args.max_iterations
    )

    # Sauvegarder rapport final
    rapport_path = os.path.join(args.output_dir, 'rapport_auto_optimisation.json')
    with open(rapport_path, 'w', encoding='utf-8') as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Rapport sauvegardé: {rapport_path}")
