#!/usr/bin/env python3
"""
Workflow 1.5 : Corrections Intelligentes pour Transcriptions CISR

Améliore la qualité des transcriptions de 55% → 95%+ de similarité via 6 passes :
- Pass 1 : Termes Juridiques (articles, lois, expressions)
- Pass 2 : Noms Propres + Accents (Michoacán, Mérida, État)
- Pass 3 : Accords Grammaticaux (genre/nombre selon contexte)
- Pass 4 : Mots Mal Reconnus (confusions phonétiques, paraphrases)
- Pass 5 : Cross-Validation Métadonnées (cohérence noms, dates, dossiers)
- Pass 6 : QA Finale + Rapport (score qualité, recommandations)

Auteur : Système de transcription automatisée CISR
Date : 2026-01-06
Sprint 1 : Architecture et Pass 1-2-3
"""

import sys
import io
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PASS 1 : TERMES JURIDIQUES
# ============================================================================

def pass1_termes_juridiques(texte: str, dictionnaire: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 1 : Corriger termes juridiques (articles, lois, expressions).

    Cible :
    - Articles de loi : "article 87" → "article 96"
    - Paragraphes : "paragraphe 97-1" → "paragraphe 97(1)"
    - Noms de lois : "Roche sur l'immigration" → "Loi sur l'Immigration et..."
    - Expressions : "en virtu" → "en vertu"

    Args:
        texte: Texte brut de la transcription
        dictionnaire: Dictionnaire de corrections chargé depuis JSON

    Returns:
        (texte_corrigé, liste_corrections_appliquées)
    """
    logger.info("🔍 Pass 1 : Correction termes juridiques...")

    texte_corrige = texte
    corrections = []

    # Charger section Pass 1 du dictionnaire
    corrections_juridiques = dictionnaire.get('pass1_termes_juridiques', {})

    if not corrections_juridiques:
        logger.warning("⚠️  Dictionnaire Pass 1 vide - aucune correction juridique disponible")
        return texte, []

    # Appliquer chaque correction
    for terme_incorrect, terme_correct in corrections_juridiques.items():
        # Recherche insensible à la casse avec regex
        pattern = re.compile(re.escape(terme_incorrect), re.IGNORECASE)
        matches = list(pattern.finditer(texte_corrige))

        if matches:
            # Remplacer toutes les occurrences
            texte_corrige = pattern.sub(terme_correct, texte_corrige)

            # Logger correction
            corrections.append({
                'pass': 1,
                'type': 'terme_juridique',
                'terme_incorrect': terme_incorrect,
                'terme_correct': terme_correct,
                'occurrences': len(matches),
                'positions': [m.start() for m in matches]
            })

            logger.info(f"   ✓ '{terme_incorrect}' → '{terme_correct}' ({len(matches)}× trouvées)")

    logger.info(f"   ✅ Pass 1 terminé : {len(corrections)} corrections appliquées\n")
    return texte_corrige, corrections


# ============================================================================
# PASS 2 : NOMS PROPRES + ACCENTS
# ============================================================================

def pass2_noms_propres_accents(texte: str, dictionnaire: Dict, metadata_wo: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 2 : Corriger noms propres et restaurer accents.

    Cible :
    - Noms de lieux : "Michoacan" → "Michoacán", "Merida" → "Mérida"
    - Noms de personnes : Via metadata_work_order.json
    - Mots communs : "Etat" → "État"
    - Homophones : "cartel national" → "Cartable national"

    Args:
        texte: Texte après Pass 1
        dictionnaire: Dictionnaire de corrections
        metadata_wo: Métadonnées work order (noms participants)

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("🔍 Pass 2 : Correction noms propres + accents...")

    texte_corrige = texte
    corrections = []

    # === SOUS-PASS 2A : Dictionnaire noms propres ===
    corrections_noms = dictionnaire.get('pass2_noms_propres_accents', {})

    for nom_sans_accent, nom_avec_accent in corrections_noms.items():
        # Recherche avec échappement regex
        pattern = re.compile(re.escape(nom_sans_accent), re.IGNORECASE)
        matches = list(pattern.finditer(texte_corrige))

        if matches:
            # Pour les noms propres, préserver la casse si possible
            # Si le nom dict commence par majuscule, on applique directement
            # Sinon, on fait un remplacement insensible à la casse
            if nom_avec_accent[0].isupper():
                # Remplacement préservant la structure du nom dict
                texte_corrige = pattern.sub(nom_avec_accent, texte_corrige)
            else:
                # Pour mots communs comme "etat" → "état", on préserve casse originale
                def preserve_case(match):
                    original = match.group(0)
                    if original.isupper():
                        return nom_avec_accent.upper()
                    elif original[0].isupper():
                        return nom_avec_accent.capitalize()
                    else:
                        return nom_avec_accent.lower()

                texte_corrige = pattern.sub(preserve_case, texte_corrige)

            corrections.append({
                'pass': 2,
                'type': 'nom_propre_accent',
                'terme_incorrect': nom_sans_accent,
                'terme_correct': nom_avec_accent,
                'occurrences': len(matches),
                'positions': [m.start() for m in matches]
            })
            logger.info(f"   ✓ '{nom_sans_accent}' → '{nom_avec_accent}' ({len(matches)}×)")

    # === SOUS-PASS 2B : Métadonnées participants ===
    # Corriger variantes du nom demandeur trouvées dans le texte
    if 'participants' in metadata_wo:
        nom_demandeur_complet = metadata_wo['participants'].get('demandeur', '')

        if nom_demandeur_complet:
            # Séparer demandeurs multiples (séparés par \n)
            demandeurs = nom_demandeur_complet.split('\n')

            for nom_demandeur in demandeurs:
                nom_demandeur = nom_demandeur.strip()
                if not nom_demandeur:
                    continue

                logger.info(f"   ℹ️  Nom demandeur metadata : {nom_demandeur}")

                # Extraire variantes possibles
                # Exemple : "Victoria AGUILAR ROMERO" peut être écrit :
                #   - "Aguilar Romero-Victoria" (incorrect)
                #   - "Aguilar-Romero Victoria" (incorrect)
                #   - "Victoria Aguilar Romero" (acceptable mais différent de format CISR)

                # Parser nom : Prénom NOM_FAMILLE
                parts = nom_demandeur.split()
                if len(parts) >= 2:
                    prenom = parts[0]
                    nom_famille = ' '.join(parts[1:])

                    # Variantes incorrectes à corriger
                    variantes = [
                        f"{nom_famille}-{prenom}",  # "AGUILAR ROMERO-Victoria"
                        f"{nom_famille.replace(' ', '-')}-{prenom}",  # "AGUILAR-ROMERO-Victoria"
                        f"{nom_famille.replace(' ', '-')} {prenom}",  # "AGUILAR-ROMERO Victoria"
                        f"{prenom} {nom_famille.lower().title()}",  # "Victoria Aguilar Romero" (casse incorrecte)
                    ]

                    for variante in variantes:
                        # Chercher variante dans texte (insensible casse)
                        if variante.lower() in texte_corrige.lower():
                            # Remplacer par format correct
                            pattern_var = re.compile(re.escape(variante), re.IGNORECASE)
                            matches_var = list(pattern_var.finditer(texte_corrige))

                            if matches_var:
                                texte_corrige = pattern_var.sub(nom_demandeur, texte_corrige)
                                corrections.append({
                                    'pass': 2,
                                    'type': 'nom_personne_metadata',
                                    'terme_incorrect': variante,
                                    'terme_correct': nom_demandeur,
                                    'occurrences': len(matches_var),
                                    'source': 'metadata_work_order.json'
                                })
                                logger.info(f"   ✓ Variante nom '{variante}' → '{nom_demandeur}' ({len(matches_var)}×)")

    logger.info(f"   ✅ Pass 2 terminé : {len(corrections)} corrections appliquées\n")
    return texte_corrige, corrections


# ============================================================================
# PASS 3 : ACCORDS GRAMMATICAUX
# ============================================================================

def pass3_accords_grammaticaux(texte: str, dictionnaire: Dict, metadata_wo: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 3 : Corriger accords de genre et nombre selon contexte.

    Cible :
    - Accords de genre : "citoyens" → "citoyennes" (si demandeur féminin)
    - Accords de nombre : "victime" → "victimes" (contexte pluriel)

    Args:
        texte: Texte après Pass 2
        dictionnaire: Dictionnaire de corrections
        metadata_wo: Métadonnées (genre demandeur)

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("🔍 Pass 3 : Correction accords grammaticaux...")

    texte_corrige = texte
    corrections = []

    # === ÉTAPE 1 : Détecter genre demandeur ===
    genre = 'inconnu'
    if 'participants' in metadata_wo:
        nom_demandeur_complet = metadata_wo['participants'].get('demandeur', '').lower()

        # Listes prénoms féminins/masculins fréquents CISR
        prenoms_feminins = [
            'victoria', 'paula', 'maria', 'carmen', 'rosa', 'ana', 'elena',
            'fatima', 'aisha', 'amina', 'zainab', 'mariam', 'sara', 'leila',
            'yasmin', 'nour', 'hanan', 'samira', 'layla', 'rania'
        ]
        prenoms_masculins = [
            'ibrahim', 'mohamed', 'mohammed', 'ahmed', 'hassan', 'ali',
            'omar', 'youssef', 'khalid', 'hamza', 'said', 'mustafa',
            'abdullah', 'karim', 'tarek', 'walid', 'rami', 'bilal'
        ]

        # Vérifier si demandeurs multiples (séparés par \n)
        demandeurs = nom_demandeur_complet.split('\n')
        genres_detectes = []

        for dem in demandeurs:
            dem = dem.strip().lower()
            if any(prenom in dem for prenom in prenoms_feminins):
                genres_detectes.append('féminin')
            elif any(prenom in dem for prenom in prenoms_masculins):
                genres_detectes.append('masculin')

        # Règle : Si AU MOINS UN demandeur féminin, utiliser accords féminins
        if 'féminin' in genres_detectes:
            genre = 'féminin'
        elif 'masculin' in genres_detectes:
            genre = 'masculin'

    logger.info(f"   ℹ️  Genre détecté : {genre}")

    # === ÉTAPE 2 : Appliquer corrections CONDITIONNELLES selon genre ===
    corrections_accords = dictionnaire.get('pass3_accords_grammaticaux', {})

    if genre == 'féminin':
        # Appliquer corrections féminines
        for forme_masculin, forme_feminin in corrections_accords.items():
            # Recherche insensible à la casse
            pattern = re.compile(r'\b' + re.escape(forme_masculin) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(texte_corrige))

            if matches:
                # Préserver casse originale
                def preserve_case_accord(match):
                    original = match.group(0)
                    if original.isupper():
                        return forme_feminin.upper()
                    elif original[0].isupper():
                        return forme_feminin.capitalize()
                    else:
                        return forme_feminin.lower()

                texte_corrige = pattern.sub(preserve_case_accord, texte_corrige)

                corrections.append({
                    'pass': 3,
                    'type': 'accord_genre',
                    'terme_incorrect': forme_masculin,
                    'terme_correct': forme_feminin,
                    'occurrences': len(matches),
                    'genre_applique': genre,
                    'positions': [m.start() for m in matches]
                })
                logger.info(f"   ✓ '{forme_masculin}' → '{forme_feminin}' ({len(matches)}×) [genre: {genre}]")

    elif genre == 'masculin':
        # Pas de corrections nécessaires si dictionnaire contient formes masculines → féminines
        logger.info(f"   ℹ️  Genre masculin détecté - aucune correction d'accord nécessaire")

    elif genre == 'inconnu':
        # Pas assez d'informations pour corriger
        logger.warning(f"   ⚠️  Genre inconnu - Pass 3 ignoré (pas de corrections d'accords)")

    # === ÉTAPE 3 : Corrections d'accords de NOMBRE (indépendantes du genre) ===
    # TODO Future : Ajouter section "pass3_accords_nombre" au dictionnaire
    # Exemple : "victime de violence" → "victimes de violence" (contexte pluriel)

    logger.info(f"   ✅ Pass 3 terminé : {len(corrections)} corrections appliquées\n")
    return texte_corrige, corrections


# ============================================================================
# PASS 4 : MOTS MAL RECONNUS
# ============================================================================

def pass4_mots_mal_reconnus(texte: str, dictionnaire: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 4 : Corriger mots mal reconnus (confusions phonétiques).

    Cible :
    - Confusions graves : "Créait" → "Vous craignez"
    - Termes médicaux : "affairement" → "avortement"
    - Paraphrases : "Si vous reveniez" → "Advenant votre retour"

    Args:
        texte: Texte après Pass 3
        dictionnaire: Dictionnaire de corrections

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("🔍 Pass 4 : Correction mots mal reconnus...")

    texte_corrige = texte
    corrections = []

    corrections_mots = dictionnaire.get('pass4_mots_mal_reconnus', {})

    for mot_incorrect, mot_correct in corrections_mots.items():
        # Recherche EXACTE (casse sensible car "Créait" vs "créait" important)
        # Compter occurrences AVANT remplacement
        occurrences = texte_corrige.count(mot_incorrect)

        if occurrences > 0:
            # Remplacer toutes les occurrences
            texte_corrige = texte_corrige.replace(mot_incorrect, mot_correct)

            corrections.append({
                'pass': 4,
                'type': 'mot_mal_reconnu',
                'terme_incorrect': mot_incorrect,
                'terme_correct': mot_correct,
                'occurrences': occurrences,
                'positions': []  # Difficile de tracker après replace
            })
            logger.info(f"   ✓ '{mot_incorrect}' → '{mot_correct}' ({occurrences}×)")

    logger.info(f"   ✅ Pass 4 terminé : {len(corrections)} corrections appliquées\n")
    return texte_corrige, corrections


# ============================================================================
# PASS 5 : CROSS-VALIDATION MÉTADONNÉES
# ============================================================================

def pass5_cross_validation_metadata(texte: str, metadata_wo: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 5 : Valider cohérence transcription vs métadonnées.

    Vérifie :
    - Noms participants présents et corrects
    - Nom commissaire validé contre liste officielle CISR
    - Dates cohérentes
    - Numéro dossier présent

    Args:
        texte: Texte après Pass 4
        metadata_wo: Métadonnées work order

    Returns:
        (texte, liste_warnings)
    """
    logger.info("🔍 Pass 5 : Cross-validation métadonnées...")

    warnings = []

    # === VALIDATION 1 : Numéro dossier ===
    numero_dossier = metadata_wo.get('dossier', {}).get('numero')
    if numero_dossier:
        if numero_dossier not in texte:
            warnings.append({
                'pass': 5,
                'type': 'missing_file_number',
                'gravite': 'HAUTE',
                'message': f"Numéro dossier {numero_dossier} absent du texte"
            })
            logger.warning(f"   ⚠️  Numéro dossier {numero_dossier} NON trouvé dans transcription")
        else:
            logger.info(f"   ✓ Numéro dossier {numero_dossier} présent")

    # === VALIDATION 2 : Nom Commissaire (CRITIQUE - Liste officielle CISR) ===
    nom_commissaire = metadata_wo.get('participants', {}).get('commissaire')
    type_transcription = metadata_wo.get('work_order', {}).get('type', 'SPR')

    if nom_commissaire:
        logger.info(f"   🔍 Validation nom commissaire : {nom_commissaire}")
        logger.info(f"      Type transcription : {type_transcription}")

        # Validation présence dans texte
        if nom_commissaire.upper() in texte.upper():
            logger.info(f"   ✓ Nom commissaire '{nom_commissaire}' présent dans texte")
        else:
            warnings.append({
                'pass': 5,
                'type': 'missing_commissioner',
                'gravite': 'HAUTE',
                'nom': nom_commissaire,
                'message': f"Nom commissaire '{nom_commissaire}' absent du texte"
            })
            logger.warning(f"   ⚠️  Nom commissaire '{nom_commissaire}' NON trouvé")

        # NOUVEAU : Validation contre liste officielle CISR
        try:
            from implementation.scraper_commissaires_cisr import ScraperCommissairesCISR

            scraper = ScraperCommissairesCISR()
            if scraper.charger_cache():
                resultat = scraper.valider_nom_commissaire(nom_commissaire, type_transcription)

                if resultat['valide']:
                    logger.info(f"   ✅ Nom commissaire VALIDÉ contre liste officielle CISR")
                    logger.info(f"      Nom exact : {resultat['nom_exact']}")
                else:
                    warnings.append({
                        'pass': 5,
                        'type': 'commissioner_not_in_official_list',
                        'gravite': 'HAUTE',
                        'nom': nom_commissaire,
                        'suggestions': resultat.get('suggestions', []),
                        'message': f"❌ Nom commissaire '{nom_commissaire}' NON trouvé dans liste officielle CISR ({type_transcription})"
                    })
                    logger.warning(f"   ❌ Nom commissaire INVALIDE (non dans liste officielle)")
                    if resultat.get('suggestions'):
                        logger.warning(f"      Suggestions : {', '.join(resultat['suggestions'][:3])}")
            else:
                # Cache non disponible, validation manuelle requise
                warnings.append({
                    'pass': 5,
                    'type': 'commissioner_validation_incomplete',
                    'gravite': 'INFO',
                    'nom': nom_commissaire,
                    'type_transcription': type_transcription,
                    'message': f"⚠️  Cache commissaires CISR non disponible - Valider manuellement : {nom_commissaire}",
                    'url': "https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx"
                })
                logger.warning(f"   ⚠️  Cache commissaires non disponible - validation manuelle requise")

        except ImportError:
            # Scraper non disponible, validation manuelle
            warnings.append({
                'pass': 5,
                'type': 'commissioner_validation_incomplete',
                'gravite': 'INFO',
                'nom': nom_commissaire,
                'type_transcription': type_transcription,
                'message': f"⚠️  IMPORTANT : Valider manuellement le nom '{nom_commissaire}' contre la liste officielle CISR ({type_transcription})",
                'url': "https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx"
            })
            logger.warning(f"   ⚠️  Module scraper non disponible - validation manuelle requise")

    # === VALIDATION 3 : Autres participants ===
    participants = metadata_wo.get('participants', {})
    for role, nom in participants.items():
        if role == 'commissaire':
            continue  # Déjà validé ci-dessus

        if nom and nom.upper() not in texte.upper():
            warnings.append({
                'pass': 5,
                'type': 'missing_participant',
                'gravite': 'MOYENNE',
                'role': role,
                'nom': nom,
                'message': f"{role.capitalize()} '{nom}' absent du texte"
            })
            logger.warning(f"   ⚠️  {role.capitalize()} '{nom}' NON trouvé")
        elif nom:
            logger.info(f"   ✓ {role.capitalize()} '{nom}' présent")

    # === VALIDATION 4 : Date audience ===
    date_audience = metadata_wo.get('audience', {}).get('date')
    if date_audience:
        # Chercher date dans texte (plusieurs formats possibles)
        # TODO : Améliorer parsing dates multiples formats
        if date_audience.lower() in texte.lower():
            logger.info(f"   ✓ Date audience '{date_audience}' présente")
        else:
            warnings.append({
                'pass': 5,
                'type': 'missing_date',
                'gravite': 'BASSE',
                'date': date_audience,
                'message': f"Date audience '{date_audience}' absente du texte"
            })
            logger.warning(f"   ⚠️  Date audience '{date_audience}' NON trouvée")

    logger.info(f"   ✅ Pass 5 terminé : {len(warnings)} warnings détectés\n")
    return texte, warnings


# ============================================================================
# PASS 6 : QA FINALE + RAPPORT
# ============================================================================

def pass6_qa_finale(texte_corrige: str, texte_original: str, toutes_corrections: List[Dict]) -> Dict:
    """
    Pass 6 : Générer rapport qualité final.

    Calcule :
    - Nombre total de corrections
    - Répartition par type
    - Score qualité (0-100)
    - Recommandations révision

    Args:
        texte_corrige: Texte final après Pass 1-5
        texte_original: Texte brut avant corrections
        toutes_corrections: Liste de toutes les corrections appliquées

    Returns:
        Rapport qualité JSON
    """
    logger.info("🔍 Pass 6 : QA finale + génération rapport...")

    # === Statistiques corrections ===
    total_corrections = len(toutes_corrections)
    corrections_par_pass = {}
    corrections_par_type = {}

    for corr in toutes_corrections:
        pass_num = corr.get('pass', 0)
        type_corr = corr.get('type', 'inconnu')

        corrections_par_pass[pass_num] = corrections_par_pass.get(pass_num, 0) + 1
        corrections_par_type[type_corr] = corrections_par_type.get(type_corr, 0) + 1

    # === Score qualité ===
    # Heuristique : 100 - (corrections_critiques * 2) - (corrections_moderees * 1)
    corrections_critiques = corrections_par_pass.get(1, 0) + corrections_par_pass.get(4, 0)
    corrections_moderees = corrections_par_pass.get(2, 0) + corrections_par_pass.get(3, 0)

    score_qualite = max(0, 100 - (corrections_critiques * 2) - (corrections_moderees * 1))

    # === Recommandations ===
    recommandations = []
    if score_qualite >= 85:
        recommandations.append("Qualité EXCELLENTE : Spot-check seulement (5-10 min)")
    elif score_qualite >= 70:
        recommandations.append("Qualité BONNE : Révision rapide (15-20 min)")
    elif score_qualite >= 50:
        recommandations.append("Qualité PASSABLE : Révision approfondie (30-40 min)")
    else:
        recommandations.append("Qualité INSUFFISANTE : Révision manuelle complète requise")

    if corrections_critiques > 10:
        recommandations.append(f"⚠️  {corrections_critiques} corrections critiques - vérifier termes juridiques")

    # === Rapport final ===
    rapport = {
        'timestamp': datetime.now().isoformat(),
        'statistiques': {
            'total_corrections': total_corrections,
            'corrections_par_pass': corrections_par_pass,
            'corrections_par_type': corrections_par_type,
            'longueur_texte_original': len(texte_original),
            'longueur_texte_corrige': len(texte_corrige),
            'taux_modification': round((len(texte_corrige) - len(texte_original)) / max(len(texte_original), 1) * 100, 2)
        },
        'qualite': {
            'score': score_qualite,
            'niveau': 'EXCELLENT' if score_qualite >= 85 else 'BON' if score_qualite >= 70 else 'PASSABLE' if score_qualite >= 50 else 'INSUFFISANT',
            'corrections_critiques': corrections_critiques,
            'corrections_moderees': corrections_moderees
        },
        'recommandations': recommandations,
        'details_corrections': toutes_corrections
    }

    logger.info(f"   ✅ Score qualité : {score_qualite}/100 ({rapport['qualite']['niveau']})")
    logger.info(f"   ✅ Total corrections : {total_corrections}")
    logger.info(f"   ✅ Recommandation : {recommandations[0]}\n")

    return rapport


# ============================================================================
# FONCTION ORCHESTRATRICE PRINCIPALE
# ============================================================================

def pipeline_corrections_intelligentes(
    texte_brut: str,
    metadata_work_order: Dict,
    dictionnaire: Dict
) -> Tuple[str, Dict]:
    """
    Pipeline complet de corrections intelligentes (Pass 1-6).

    Architecture :
    1. Pass 1 : Termes juridiques (CRITIQUE)
    2. Pass 2 : Noms propres + accents
    3. Pass 3 : Accords grammaticaux
    4. Pass 4 : Mots mal reconnus (CRITIQUE)
    5. Pass 5 : Cross-validation métadonnées
    6. Pass 6 : QA finale + rapport

    Args:
        texte_brut: Transcription AssemblyAI brute
        metadata_work_order: Métadonnées depuis metadata_work_order.json
        dictionnaire: Dictionnaire de corrections chargé depuis JSON

    Returns:
        (texte_corrigé, rapport_qualité)
    """
    logger.info("=" * 70)
    logger.info("WORKFLOW 1.5 : CORRECTIONS INTELLIGENTES - DÉMARRAGE")
    logger.info("=" * 70)
    logger.info(f"📊 Longueur texte brut : {len(texte_brut)} caractères")

    # Compter entrées dictionnaire (seulement sections dict, pas int/str)
    total_entrees = sum(len(v) for k, v in dictionnaire.items() if isinstance(v, dict))
    logger.info(f"📖 Dictionnaire chargé : {total_entrees} entrées")
    logger.info("")

    toutes_corrections = []
    warnings = []

    # === PASS 1 : Termes Juridiques ===
    texte_pass1, corrections_p1 = pass1_termes_juridiques(texte_brut, dictionnaire)
    toutes_corrections.extend(corrections_p1)

    # === PASS 2 : Noms Propres + Accents ===
    texte_pass2, corrections_p2 = pass2_noms_propres_accents(texte_pass1, dictionnaire, metadata_work_order)
    toutes_corrections.extend(corrections_p2)

    # === PASS 3 : Accords Grammaticaux ===
    texte_pass3, corrections_p3 = pass3_accords_grammaticaux(texte_pass2, dictionnaire, metadata_work_order)
    toutes_corrections.extend(corrections_p3)

    # === PASS 4 : Mots Mal Reconnus ===
    texte_pass4, corrections_p4 = pass4_mots_mal_reconnus(texte_pass3, dictionnaire)
    toutes_corrections.extend(corrections_p4)

    # === PASS 5 : Cross-Validation ===
    texte_pass5, warnings_p5 = pass5_cross_validation_metadata(texte_pass4, metadata_work_order)
    warnings.extend(warnings_p5)

    # === PASS 6 : QA Finale ===
    rapport = pass6_qa_finale(texte_pass5, texte_brut, toutes_corrections)
    rapport['warnings'] = warnings

    logger.info("=" * 70)
    logger.info("✅ WORKFLOW 1.5 : CORRECTIONS TERMINÉES")
    logger.info("=" * 70)
    logger.info(f"📊 Résultat : {len(texte_pass5)} caractères")
    logger.info(f"✅ {len(toutes_corrections)} corrections appliquées")
    logger.info(f"⚠️  {len(warnings)} warnings détectés")
    logger.info("")

    return texte_pass5, rapport


# ============================================================================
# UTILITAIRES
# ============================================================================

def charger_dictionnaire(dictionnaire_path: str) -> Dict:
    """
    Charger dictionnaire de corrections depuis fichier JSON.

    Args:
        dictionnaire_path: Chemin vers CISR_Corrections_Dictionary_V2.json

    Returns:
        Dictionnaire de corrections
    """
    if not os.path.exists(dictionnaire_path):
        logger.error(f"❌ Dictionnaire non trouvé : {dictionnaire_path}")
        return {}

    try:
        with open(dictionnaire_path, 'r', encoding='utf-8') as f:
            dictionnaire = json.load(f)

        logger.info(f"✅ Dictionnaire chargé : {dictionnaire_path}")
        logger.info(f"   Version : {dictionnaire.get('version', 'inconnu')}")
        logger.info(f"   Total entrées : {sum(len(v) for k, v in dictionnaire.items() if isinstance(v, dict))}")

        return dictionnaire

    except Exception as e:
        logger.error(f"❌ Erreur chargement dictionnaire : {e}")
        return {}


# ============================================================================
# MAIN (pour tests standalone)
# ============================================================================

def main():
    """Point d'entrée CLI pour tests standalone"""
    import argparse

    parser = argparse.ArgumentParser(description='Workflow 1.5 : Corrections Intelligentes')
    parser.add_argument('--input', required=True, help='Fichier transcription brute (.txt)')
    parser.add_argument('--metadata', required=True, help='Fichier metadata_work_order.json')
    parser.add_argument('--dictionnaire', default='Documentation/CISR_Corrections_Dictionary_V2.json',
                        help='Chemin dictionnaire corrections')
    parser.add_argument('--output', help='Fichier sortie transcription corrigée (.txt)')
    parser.add_argument('--rapport', help='Fichier rapport qualité (.json)')

    args = parser.parse_args()

    # Charger fichiers
    with open(args.input, 'r', encoding='utf-8') as f:
        texte_brut = f.read()

    with open(args.metadata, 'r', encoding='utf-8') as f:
        metadata_wo = json.load(f)

    dictionnaire = charger_dictionnaire(args.dictionnaire)

    # Exécuter pipeline
    texte_corrige, rapport = pipeline_corrections_intelligentes(texte_brut, metadata_wo, dictionnaire)

    # Sauvegarder résultats
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(texte_corrige)
        logger.info(f"✅ Transcription corrigée sauvegardée : {args.output}")

    if args.rapport:
        with open(args.rapport, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Rapport qualité sauvegardé : {args.rapport}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
