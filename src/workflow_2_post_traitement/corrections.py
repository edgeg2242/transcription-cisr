"""
Pipeline de corrections intelligentes pour transcriptions CISR (6 passes).

Pass 1 : Termes juridiques (articles, lois, expressions)
Pass 2 : Noms propres + accents (Michoacán, Mérida, État)
Pass 3 : Accords grammaticaux (genre/nombre selon contexte)
Pass 4 : Mots mal reconnus (confusions phonétiques)
Pass 5 : Cross-validation métadonnées (cohérence noms, dates, dossiers)
Pass 6 : QA finale + rapport (score qualité, recommandations)
"""

import re
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# PASS 1 : TERMES JURIDIQUES
# ============================================================================

def pass1_termes_juridiques(texte: str, dictionnaire: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 1 : Corriger termes juridiques (articles, lois, expressions).

    Args:
        texte: Texte brut de la transcription
        dictionnaire: Dictionnaire de corrections chargé depuis JSON

    Returns:
        (texte_corrigé, liste_corrections_appliquées)
    """
    logger.info("Pass 1 : Correction termes juridiques...")

    texte_corrige = texte
    corrections = []

    corrections_juridiques = dictionnaire.get('pass1_termes_juridiques', {})
    if not corrections_juridiques:
        logger.warning("Dictionnaire Pass 1 vide - aucune correction juridique disponible")
        return texte, []

    for terme_incorrect, terme_correct in corrections_juridiques.items():
        pattern = re.compile(re.escape(terme_incorrect), re.IGNORECASE)
        matches = list(pattern.finditer(texte_corrige))

        if matches:
            texte_corrige = pattern.sub(terme_correct, texte_corrige)
            corrections.append({
                'pass': 1,
                'type': 'terme_juridique',
                'terme_incorrect': terme_incorrect,
                'terme_correct': terme_correct,
                'occurrences': len(matches),
                'positions': [m.start() for m in matches]
            })
            logger.info(f"  '{terme_incorrect}' -> '{terme_correct}' ({len(matches)}x)")

    logger.info(f"  Pass 1 terminé : {len(corrections)} corrections")
    return texte_corrige, corrections


# ============================================================================
# PASS 2 : NOMS PROPRES + ACCENTS
# ============================================================================

def pass2_noms_propres_accents(texte: str, dictionnaire: Dict, metadata_wo: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 2 : Corriger noms propres et restaurer accents.

    Args:
        texte: Texte après Pass 1
        dictionnaire: Dictionnaire de corrections
        metadata_wo: Métadonnées work order (noms participants)

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("Pass 2 : Correction noms propres + accents...")

    texte_corrige = texte
    corrections = []

    # Sous-pass 2A : Dictionnaire noms propres
    corrections_noms = dictionnaire.get('pass2_noms_propres_accents', {})

    for nom_sans_accent, nom_avec_accent in corrections_noms.items():
        pattern = re.compile(re.escape(nom_sans_accent), re.IGNORECASE)
        matches = list(pattern.finditer(texte_corrige))

        if matches:
            if nom_avec_accent[0].isupper():
                texte_corrige = pattern.sub(nom_avec_accent, texte_corrige)
            else:
                def preserve_case(match, replacement=nom_avec_accent):
                    original = match.group(0)
                    if original.isupper():
                        return replacement.upper()
                    elif original[0].isupper():
                        return replacement.capitalize()
                    return replacement.lower()

                texte_corrige = pattern.sub(preserve_case, texte_corrige)

            corrections.append({
                'pass': 2,
                'type': 'nom_propre_accent',
                'terme_incorrect': nom_sans_accent,
                'terme_correct': nom_avec_accent,
                'occurrences': len(matches),
                'positions': [m.start() for m in matches]
            })
            logger.info(f"  '{nom_sans_accent}' -> '{nom_avec_accent}' ({len(matches)}x)")

    # Sous-pass 2B : Métadonnées participants
    if 'participants' in metadata_wo:
        nom_demandeur_complet = metadata_wo['participants'].get('demandeur', '')
        if nom_demandeur_complet:
            demandeurs = nom_demandeur_complet.split('\n')
            for nom_demandeur in demandeurs:
                nom_demandeur = nom_demandeur.strip()
                if not nom_demandeur:
                    continue

                parts = nom_demandeur.split()
                if len(parts) >= 2:
                    prenom = parts[0]
                    nom_famille = ' '.join(parts[1:])

                    variantes = [
                        f"{nom_famille}-{prenom}",
                        f"{nom_famille.replace(' ', '-')}-{prenom}",
                        f"{nom_famille.replace(' ', '-')} {prenom}",
                        f"{prenom} {nom_famille.lower().title()}",
                    ]

                    for variante in variantes:
                        if variante.lower() in texte_corrige.lower():
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
                                logger.info(f"  Variante '{variante}' -> '{nom_demandeur}' ({len(matches_var)}x)")

    logger.info(f"  Pass 2 terminé : {len(corrections)} corrections")
    return texte_corrige, corrections


# ============================================================================
# PASS 3 : ACCORDS GRAMMATICAUX
# ============================================================================

def pass3_accords_grammaticaux(texte: str, dictionnaire: Dict, metadata_wo: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 3 : Corriger accords de genre et nombre selon contexte.

    Args:
        texte: Texte après Pass 2
        dictionnaire: Dictionnaire de corrections
        metadata_wo: Métadonnées (genre demandeur)

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("Pass 3 : Correction accords grammaticaux...")

    texte_corrige = texte
    corrections = []

    # Détecter genre demandeur
    genre = _detecter_genre_demandeur(metadata_wo)
    logger.info(f"  Genre détecté : {genre}")

    corrections_accords = dictionnaire.get('pass3_accords_grammaticaux', {})

    if genre == 'féminin':
        for forme_masculin, forme_feminin in corrections_accords.items():
            pattern = re.compile(r'\b' + re.escape(forme_masculin) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(texte_corrige))

            if matches:
                def preserve_case_accord(match, replacement=forme_feminin):
                    original = match.group(0)
                    if original.isupper():
                        return replacement.upper()
                    elif original[0].isupper():
                        return replacement.capitalize()
                    return replacement.lower()

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
                logger.info(f"  '{forme_masculin}' -> '{forme_feminin}' ({len(matches)}x) [genre: {genre}]")

    elif genre == 'masculin':
        logger.info("  Genre masculin - aucune correction d'accord nécessaire")

    elif genre == 'inconnu':
        logger.warning("  Genre inconnu - Pass 3 ignoré")

    logger.info(f"  Pass 3 terminé : {len(corrections)} corrections")
    return texte_corrige, corrections


def _detecter_genre_demandeur(metadata_wo: Dict) -> str:
    """Détecte le genre du demandeur à partir des métadonnées."""
    if 'participants' not in metadata_wo:
        return 'inconnu'

    nom_demandeur_complet = metadata_wo['participants'].get('demandeur', '').lower()

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

    demandeurs = nom_demandeur_complet.split('\n')
    genres_detectes = []

    for dem in demandeurs:
        dem = dem.strip().lower()
        if any(prenom in dem for prenom in prenoms_feminins):
            genres_detectes.append('féminin')
        elif any(prenom in dem for prenom in prenoms_masculins):
            genres_detectes.append('masculin')

    if 'féminin' in genres_detectes:
        return 'féminin'
    elif 'masculin' in genres_detectes:
        return 'masculin'
    return 'inconnu'


# ============================================================================
# PASS 4 : MOTS MAL RECONNUS
# ============================================================================

def pass4_mots_mal_reconnus(texte: str, dictionnaire: Dict) -> Tuple[str, List[Dict]]:
    """
    Pass 4 : Corriger mots mal reconnus (confusions phonétiques).

    Utilise un remplacement EXACT (sensible à la casse) car
    "Créait" vs "créait" peut être significatif.

    Args:
        texte: Texte après Pass 3
        dictionnaire: Dictionnaire de corrections

    Returns:
        (texte_corrigé, liste_corrections)
    """
    logger.info("Pass 4 : Correction mots mal reconnus...")

    texte_corrige = texte
    corrections = []

    corrections_mots = dictionnaire.get('pass4_mots_mal_reconnus', {})

    for mot_incorrect, mot_correct in corrections_mots.items():
        occurrences = texte_corrige.count(mot_incorrect)
        if occurrences > 0:
            texte_corrige = texte_corrige.replace(mot_incorrect, mot_correct)
            corrections.append({
                'pass': 4,
                'type': 'mot_mal_reconnu',
                'terme_incorrect': mot_incorrect,
                'terme_correct': mot_correct,
                'occurrences': occurrences,
            })
            logger.info(f"  '{mot_incorrect}' -> '{mot_correct}' ({occurrences}x)")

    logger.info(f"  Pass 4 terminé : {len(corrections)} corrections")
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

    Note : Ne modifie pas le texte, retourne des warnings.

    Args:
        texte: Texte après Pass 4
        metadata_wo: Métadonnées work order

    Returns:
        (texte_inchangé, liste_warnings)
    """
    logger.info("Pass 5 : Cross-validation métadonnées...")

    warnings = []

    # Validation 1 : Numéro dossier
    numero_dossier = metadata_wo.get('dossier', {}).get('numero')
    if numero_dossier:
        if numero_dossier not in texte:
            warnings.append({
                'pass': 5, 'type': 'missing_file_number', 'gravite': 'HAUTE',
                'message': f"Numéro dossier {numero_dossier} absent du texte"
            })
            logger.warning(f"  Numéro dossier {numero_dossier} NON trouvé")
        else:
            logger.info(f"  Numéro dossier {numero_dossier} présent")

    # Validation 2 : Nom Commissaire
    nom_commissaire = metadata_wo.get('participants', {}).get('commissaire')
    type_transcription = metadata_wo.get('work_order', {}).get('type', 'SPR')

    if nom_commissaire:
        if nom_commissaire.upper() in texte.upper():
            logger.info(f"  Nom commissaire '{nom_commissaire}' présent")
        else:
            warnings.append({
                'pass': 5, 'type': 'missing_commissioner', 'gravite': 'HAUTE',
                'nom': nom_commissaire,
                'message': f"Nom commissaire '{nom_commissaire}' absent du texte"
            })
            logger.warning(f"  Nom commissaire '{nom_commissaire}' NON trouvé")

        # Validation contre liste officielle CISR (si cache disponible)
        _valider_commissaire_cisr(nom_commissaire, type_transcription, warnings)

    # Validation 3 : Autres participants
    participants = metadata_wo.get('participants', {})
    for role, nom in participants.items():
        if role == 'commissaire':
            continue
        if nom and nom.upper() not in texte.upper():
            warnings.append({
                'pass': 5, 'type': 'missing_participant', 'gravite': 'MOYENNE',
                'role': role, 'nom': nom,
                'message': f"{role.capitalize()} '{nom}' absent du texte"
            })
            logger.warning(f"  {role.capitalize()} '{nom}' NON trouvé")
        elif nom:
            logger.info(f"  {role.capitalize()} '{nom}' présent")

    # Validation 4 : Date audience
    date_audience = metadata_wo.get('audience', {}).get('date')
    if date_audience:
        if date_audience.lower() in texte.lower():
            logger.info(f"  Date audience '{date_audience}' présente")
        else:
            warnings.append({
                'pass': 5, 'type': 'missing_date', 'gravite': 'BASSE',
                'date': date_audience,
                'message': f"Date audience '{date_audience}' absente du texte"
            })

    logger.info(f"  Pass 5 terminé : {len(warnings)} warnings")
    return texte, warnings


def _valider_commissaire_cisr(nom_commissaire: str, type_transcription: str, warnings: List[Dict]):
    """Valide le nom du commissaire contre le cache de la liste officielle CISR."""
    try:
        cache_path = Path(__file__).parent.parent.parent / "data" / "cache" / "commissaires_cisr.json"
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            commissaires = cache.get('commissaires', [])
            noms_normalises = [c.upper() for c in commissaires]

            if nom_commissaire.upper() in noms_normalises:
                logger.info(f"  Nom commissaire VALIDÉ contre liste officielle CISR")
            else:
                warnings.append({
                    'pass': 5, 'type': 'commissioner_not_in_official_list',
                    'gravite': 'HAUTE', 'nom': nom_commissaire,
                    'message': f"Nom commissaire '{nom_commissaire}' NON trouvé dans liste officielle CISR ({type_transcription})"
                })
                logger.warning(f"  Nom commissaire INVALIDE (non dans liste officielle)")
        else:
            warnings.append({
                'pass': 5, 'type': 'commissioner_validation_incomplete',
                'gravite': 'INFO', 'nom': nom_commissaire,
                'message': f"Cache commissaires CISR non disponible - Valider manuellement : {nom_commissaire}",
                'url': "https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx"
            })
    except Exception:
        logger.warning("  Cache commissaires non disponible - validation manuelle requise")


# ============================================================================
# PASS 6 : QA FINALE + RAPPORT
# ============================================================================

def pass6_qa_finale(texte_corrige: str, texte_original: str, toutes_corrections: List[Dict]) -> Dict:
    """
    Pass 6 : Générer rapport qualité final.

    Score = 100 - (corrections_critiques * 2) - (corrections_moderees * 1)
    Note : Score mesure la qualité du texte ORIGINAL, pas du résultat.

    Args:
        texte_corrige: Texte final après Pass 1-5
        texte_original: Texte brut avant corrections
        toutes_corrections: Liste de toutes les corrections appliquées

    Returns:
        Rapport qualité dict
    """
    logger.info("Pass 6 : QA finale + rapport...")

    total_corrections = len(toutes_corrections)
    corrections_par_pass = {}
    corrections_par_type = {}

    for corr in toutes_corrections:
        pass_num = corr.get('pass', 0)
        type_corr = corr.get('type', 'inconnu')
        corrections_par_pass[pass_num] = corrections_par_pass.get(pass_num, 0) + 1
        corrections_par_type[type_corr] = corrections_par_type.get(type_corr, 0) + 1

    # Score qualité
    corrections_critiques = corrections_par_pass.get(1, 0) + corrections_par_pass.get(4, 0)
    corrections_moderees = corrections_par_pass.get(2, 0) + corrections_par_pass.get(3, 0)
    score_qualite = max(0, 100 - (corrections_critiques * 2) - (corrections_moderees * 1))

    # Recommandations
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
        recommandations.append(f"{corrections_critiques} corrections critiques - vérifier termes juridiques")

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

    logger.info(f"  Score qualité : {score_qualite}/100 ({rapport['qualite']['niveau']})")
    logger.info(f"  Total corrections : {total_corrections}")
    return rapport


# ============================================================================
# PIPELINE ORCHESTRATEUR
# ============================================================================

def pipeline_corrections_intelligentes(
    texte_brut: str,
    metadata_work_order: Dict,
    dictionnaire: Dict
) -> Tuple[str, Dict]:
    """
    Pipeline complet de corrections intelligentes (Pass 1-6).

    Args:
        texte_brut: Transcription AssemblyAI brute
        metadata_work_order: Métadonnées depuis metadata_work_order.json
        dictionnaire: Dictionnaire de corrections

    Returns:
        (texte_corrigé, rapport_qualité)
    """
    logger.info("=" * 70)
    logger.info("CORRECTIONS INTELLIGENTES - DÉMARRAGE")
    logger.info("=" * 70)
    logger.info(f"Longueur texte brut : {len(texte_brut)} caractères")

    total_entrees = sum(len(v) for k, v in dictionnaire.items() if isinstance(v, dict))
    logger.info(f"Dictionnaire : {total_entrees} entrées")

    toutes_corrections = []
    warnings = []

    # Pass 1 : Termes Juridiques
    texte_pass1, corrections_p1 = pass1_termes_juridiques(texte_brut, dictionnaire)
    toutes_corrections.extend(corrections_p1)

    # Pass 2 : Noms Propres + Accents
    texte_pass2, corrections_p2 = pass2_noms_propres_accents(texte_pass1, dictionnaire, metadata_work_order)
    toutes_corrections.extend(corrections_p2)

    # Pass 3 : Accords Grammaticaux
    texte_pass3, corrections_p3 = pass3_accords_grammaticaux(texte_pass2, dictionnaire, metadata_work_order)
    toutes_corrections.extend(corrections_p3)

    # Pass 4 : Mots Mal Reconnus
    texte_pass4, corrections_p4 = pass4_mots_mal_reconnus(texte_pass3, dictionnaire)
    toutes_corrections.extend(corrections_p4)

    # Pass 5 : Cross-Validation
    texte_pass5, warnings_p5 = pass5_cross_validation_metadata(texte_pass4, metadata_work_order)
    warnings.extend(warnings_p5)

    # Pass 6 : QA Finale
    rapport = pass6_qa_finale(texte_pass5, texte_brut, toutes_corrections)
    rapport['warnings'] = warnings

    logger.info("=" * 70)
    logger.info("CORRECTIONS TERMINÉES")
    logger.info(f"  {len(toutes_corrections)} corrections, {len(warnings)} warnings")
    logger.info("=" * 70)

    return texte_pass5, rapport


def charger_dictionnaire(dictionnaire_path: str) -> Dict:
    """
    Charger dictionnaire de corrections depuis fichier JSON.

    Args:
        dictionnaire_path: Chemin vers corrections_v2.1.json

    Returns:
        Dictionnaire de corrections
    """
    if not Path(dictionnaire_path).exists():
        logger.error(f"Dictionnaire non trouvé : {dictionnaire_path}")
        return {}

    try:
        with open(dictionnaire_path, 'r', encoding='utf-8') as f:
            dictionnaire = json.load(f)

        logger.info(f"Dictionnaire chargé : {dictionnaire_path}")
        logger.info(f"  Version : {dictionnaire.get('version', 'inconnu')}")
        return dictionnaire

    except Exception as e:
        logger.error(f"Erreur chargement dictionnaire : {e}")
        return {}
