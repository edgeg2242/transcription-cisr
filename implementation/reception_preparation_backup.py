#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WARNING — FICHIER BACKUP OBSOLÈTE
==================================
Ce fichier est un backup historique qui utilise FFmpeg LOCAL pour la conversion audio.
Cela viole la CONTRAINTE #10 du CLAUDE.md qui exige l'utilisation de CloudConvert API
pour la compatibilité serveur distant.

NE PAS UTILISER ce fichier en production.
Utiliser à la place : implementation/reception_preparation.py (version principale)
qui utilise CloudConvert API (implementation/audio_converter_api.py).

Ce fichier est conservé uniquement comme référence historique.
==================================

Workflow: Réception et Préparation de Demande de Transcription CISR
Framework: "ii" (Information/Implémentation)

LIRE: instruction/reception_preparation.md AVANT d'exécuter ce script.

Ce workflow implémente la phase initiale de réception d'une demande de transcription,
extraction des métadonnées, validation et génération du rapport initial.
"""

import os
import sys
import json
import argparse
import logging
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configurer FFmpeg portable
try:
    ffmpeg_config_path = Path(__file__).parent.parent / 'ffmpeg_config.py'
    if ffmpeg_config_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("ffmpeg_config", ffmpeg_config_path)
        ffmpeg_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ffmpeg_config)
except Exception:
    pass  # FFmpeg config optionnel

# Ajouter le répertoire .claudecode/skills au path pour importer le skill CISR
skill_path = Path(__file__).parent.parent / '.claudecode' / 'skills'
sys.path.insert(0, str(skill_path))

try:
    from cisr_transcription_assistant import CISRTranscriptionAssistant
except ImportError as e:
    print(f"❌ ERREUR: Impossible d'importer CISRTranscriptionAssistant")
    print(f"   Chemin recherché: {skill_path}")
    print(f"   Erreur: {e}")
    sys.exit(1)


# Configuration logging
def setup_logging(demande_folder: Path) -> logging.Logger:
    """Configure le logging pour ce workflow."""
    log_dir = demande_folder / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'reception_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def decouper_audio_selon_remarks(audio_file: Path, metadata_work_order: Dict, logger: logging.Logger) -> Optional[Path]:
    """
    Découpe le fichier audio selon les Recording Unit Remarks du Work Order Excel.

    Cette fonction lit les instructions de découpage depuis metadata_work_order.json
    (enrichi par Workflow 0) et utilise FFmpeg pour créer une version découpée du fichier audio.

    Args:
        audio_file: Chemin vers le fichier audio original
        metadata_work_order: Dict métadonnées depuis metadata_work_order.json
        logger: Logger pour journalisation

    Returns:
        Path vers fichier audio découpé si découpage appliqué, None sinon

    Exemples Recording Remarks:
        - "commence à 1:33" → Commence à 1 minute 33 secondes
        - "commence à 0:46" → Commence à 46 secondes
        - "arrête à 8:30" → Arrête à 8 minutes 30 secondes

    Raises:
        subprocess.CalledProcessError: Si FFmpeg échoue
        FileNotFoundError: Si FFmpeg n'est pas installé
    """
    # Vérifier si métadonnées transcription disponibles
    if 'transcription' not in metadata_work_order:
        logger.info("   ℹ️  Aucune métadonnée transcription (Excel) - découpage ignoré")
        return None

    transcription_meta = metadata_work_order['transcription']
    recording_remarks = transcription_meta.get('recording_remarks')

    if not recording_remarks:
        logger.info("   ℹ️  Aucun Recording Remark - découpage ignoré")
        return None

    # Extraire start_time_seconds (déjà parsé par workflow 0)
    audio_decoupage = transcription_meta.get('audio_decoupage', {})
    start_seconds = audio_decoupage.get('start_time_seconds')

    if not start_seconds or start_seconds <= 0:
        logger.info(f"   ℹ️  Recording Remark présent mais aucun découpage détecté: '{recording_remarks}'")
        return None

    # === DÉCOUPAGE AUDIO AVEC FFMPEG ===
    logger.info(f"   🎯 Découpage audio détecté: '{recording_remarks}'")
    logger.info(f"      Démarrer à: {start_seconds}s ({start_seconds//60}:{start_seconds%60:02d})")

    # Générer nom fichier de sortie
    output_file = audio_file.parent / f"{audio_file.stem}_trimmed{audio_file.suffix}"

    # Commande FFmpeg
    # -i input.wav : Fichier d'entrée
    # -ss {seconds} : Démarrer à X secondes
    # -c copy : Copier codec (pas de réencodage, très rapide)
    # output_trimmed.wav : Fichier de sortie
    cmd = [
        'ffmpeg',
        '-i', str(audio_file),
        '-ss', str(start_seconds),
        '-c', 'copy',
        '-y',  # Overwrite sans demander
        str(output_file)
    ]

    try:
        logger.info(f"   🔧 Exécution FFmpeg...")
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # Vérifier que fichier créé
        if output_file.exists():
            original_size = audio_file.stat().st_size / (1024 * 1024)  # MB
            trimmed_size = output_file.stat().st_size / (1024 * 1024)  # MB
            economies = original_size - trimmed_size

            logger.info(f"   ✅ Audio découpé avec succès:")
            logger.info(f"      Fichier original: {original_size:.2f} MB")
            logger.info(f"      Fichier découpé: {trimmed_size:.2f} MB")
            logger.info(f"      Économie: {economies:.2f} MB ({economies/original_size*100:.1f}%)")
            logger.info(f"      📁 {output_file.name}")

            return output_file
        else:
            logger.error(f"   ❌ FFmpeg terminé mais fichier non créé: {output_file}")
            return None

    except FileNotFoundError:
        logger.error("   ❌ FFmpeg non trouvé - installation requise")
        logger.error("      Windows: choco install ffmpeg")
        logger.error("      Mac: brew install ffmpeg")
        logger.error("      Linux: sudo apt-get install ffmpeg")
        return None

    except subprocess.CalledProcessError as e:
        logger.error(f"   ❌ Erreur FFmpeg: {e}")
        logger.error(f"      stderr: {e.stderr}")
        return None


class ReceptionPreparationWorkflow:
    """Workflow de réception et préparation de demande de transcription CISR."""

    def __init__(self, demande_folder: Path, section: Optional[str] = None,
                 email_notification: bool = False, metadata_json_path: Optional[str] = None):
        """
        Initialise le workflow.

        Args:
            demande_folder: Chemin vers le dossier contenant page couverture + audio
            section: Type de section CISR (SPR, SAR, SI, SAI) - optionnel, auto-détecté
            email_notification: Activer les notifications email
            metadata_json_path: Chemin vers metadata_work_order.json (workflow 0)
        """
        self.demande_folder = Path(demande_folder)
        self.section = section
        self.email_notification = email_notification
        self.metadata_json_path = metadata_json_path
        self.logger = setup_logging(self.demande_folder)
        self.assistant = CISRTranscriptionAssistant()

        # Résultats du workflow
        self.metadata = {}
        self.divergences = []
        self.audio_info = {}

        # Pré-charger métadonnées depuis workflow 0 si disponible
        if self.metadata_json_path and Path(self.metadata_json_path).exists():
            self._load_metadata_from_workflow0()

    def _load_metadata_from_workflow0(self) -> None:
        """
        Charge les métadonnées depuis metadata_work_order.json généré par workflow 0.

        Format attendu:
        {
          "dossier": {"numero": "TC5-07390", "section": "SPR", "iuc": "1118522122", ...},
          "participants": {"demandeur": "...", "commissaire": "...", ...},
          "audience": {"date": "23 octobre 2025", "lieu": "...", ...}
        }
        """
        try:
            with open(self.metadata_json_path, 'r', encoding='utf-8') as f:
                metadata_wo = json.load(f)

            # Mapper format workflow 0 → format workflow 1
            self.metadata = {
                'section_type': metadata_wo.get('dossier', {}).get('section', 'SPR'),
                'numero_dossier': metadata_wo.get('dossier', {}).get('numero'),
                'date_audience': metadata_wo.get('audience', {}).get('date'),
                'heure_debut': metadata_wo.get('audience', {}).get('heure_debut', 'N/A'),
                'heure_fin': metadata_wo.get('audience', {}).get('heure_fin', 'N/A'),
                'lieu_audience': metadata_wo.get('audience', {}).get('lieu'),
                'date_decision': metadata_wo.get('audience', {}).get('date_decision'),
                'iuc': metadata_wo.get('dossier', {}).get('iuc'),
                'huis_clos': metadata_wo.get('dossier', {}).get('huis_clos', False),
                'participants': [
                    metadata_wo.get('participants', {}).get('demandeur'),
                    metadata_wo.get('participants', {}).get('commissaire'),
                    metadata_wo.get('participants', {}).get('conseil_demandeur'),
                    metadata_wo.get('participants', {}).get('interprete')
                ],
                'metadata_work_order_original': metadata_wo  # Conserver original
            }

            # Auto-détecter section si non fournie
            if not self.section:
                self.section = self.metadata['section_type']

            self.logger.info(f"✅ Métadonnées pré-chargées depuis workflow 0 : {self.metadata_json_path}")
            self.logger.info(f"   Section: {self.metadata['section_type']}")
            self.logger.info(f"   Dossier: {self.metadata['numero_dossier']}")
            self.logger.info(f"   Demandeur: {metadata_wo.get('participants', {}).get('demandeur')}")

        except Exception as e:
            self.logger.warning(f"⚠️  Impossible de charger metadata_work_order.json: {e}")
            self.logger.warning("   Extraction depuis page couverture sera utilisée")

    def step1_reception_demande(self) -> bool:
        """
        Étape 1: Réception de la demande.
        Vérifie l'existence du dossier et des fichiers requis.

        Returns:
            True si succès, False sinon
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 1/6: Réception de la demande")
        self.logger.info("=" * 60)

        # Vérifier existence dossier
        if not self.demande_folder.exists():
            self.logger.error(f"❌ Dossier introuvable: {self.demande_folder}")
            return False

        self.logger.info(f"✅ Dossier trouvé: {self.demande_folder}")

        # Lister les fichiers
        fichiers = list(self.demande_folder.glob('*'))
        self.logger.info(f"📁 Fichiers trouvés: {len(fichiers)}")

        # Rechercher page couverture DOCX
        docx_files = list(self.demande_folder.glob('*.docx'))
        if not docx_files:
            self.logger.error("❌ Aucun fichier DOCX (page couverture) trouvé")
            return False

        self.metadata['page_couverture_path'] = str(docx_files[0])
        self.logger.info(f"✅ Page couverture: {docx_files[0].name}")

        # Rechercher fichiers audio
        audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(self.demande_folder.glob(f'*{ext}'))

        if not audio_files:
            self.logger.error("❌ Aucun fichier audio trouvé")
            return False

        self.metadata['audio_files'] = [str(f) for f in audio_files]
        self.logger.info(f"✅ Fichiers audio trouvés: {len(audio_files)}")
        for audio in audio_files:
            self.logger.info(f"   - {audio.name}")

        return True

    def step2_extraction_page_couverture(self) -> bool:
        """
        Étape 2: Extraction métadonnées page couverture.
        Utilise le skill CISR pour extraire les informations.

        Returns:
            True si succès, False sinon
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 2/6: Extraction page couverture")
        self.logger.info("=" * 60)

        # Si métadonnées déjà chargées depuis workflow 0, skip extraction
        if self.metadata.get('metadata_work_order_original'):
            self.logger.info("Skip - Métadonnées déjà chargées depuis workflow 0")
            self.logger.info(f"   Section: {self.metadata.get('section_type', 'N/A')}")
            self.logger.info(f"   Numéro dossier: {self.metadata.get('numero_dossier', 'N/A')}")
            self.logger.info(f"   Date audience: {self.metadata.get('date_audience', 'N/A')}")
            return True

        try:
            page_data = self.assistant.extract_page_couverture(
                self.metadata['page_couverture_path']
            )

            # Fusionner avec metadata (seulement si pas déjà depuis workflow 0)
            self.metadata.update(page_data)

            self.logger.info("✅ Métadonnées extraites:")
            self.logger.info(f"   Section: {page_data.get('section_type', 'N/A')}")
            self.logger.info(f"   Numéro dossier: {page_data.get('numero_dossier', 'N/A')}")
            self.logger.info(f"   Date audience: {page_data.get('date_audience', 'N/A')}")
            self.logger.info(f"   Heure début: {page_data.get('heure_debut', 'N/A')}")
            self.logger.info(f"   Heure fin: {page_data.get('heure_fin', 'N/A')}")
            self.logger.info(f"   Participants: {', '.join(page_data.get('participants', []))}")

            # Auto-détection section si non fournie
            if not self.section and 'section_type' in page_data:
                self.section = page_data['section_type']
                self.logger.info(f"🔍 Section auto-détectée: {self.section}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Erreur extraction page couverture: {e}")
            return False

    def step3_validation_metadata(self) -> bool:
        """
        Étape 3: Validation des métadonnées extraites.
        Vérifie le format, notamment pour SAR (double numéro).

        Returns:
            True si succès, False sinon
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 3/6: Validation métadonnées")
        self.logger.info("=" * 60)

        erreurs = []

        # Vérifier champs obligatoires
        champs_requis = ['section_type', 'numero_dossier']

        for champ in champs_requis:
            if champ not in self.metadata or not self.metadata[champ]:
                erreurs.append(f"Champ obligatoire manquant: {champ}")

        # Vérification spécifique SAR: double numéro
        if self.metadata.get('section_type') == 'SAR':
            numero = self.metadata.get('numero_dossier', '')
            if '/' not in numero or 'SPR' not in numero or 'SAR' not in numero:
                erreurs.append(
                    "SAR: Double numéro requis (format: SPR-XXXXX / SAR-XXXXX)"
                )
                self.logger.warning("⚠️  SAR Protégé B: Double numéro manquant ou invalide")
            else:
                self.logger.info("✅ SAR: Double numéro validé")

        # Vérifier format date
        try:
            if 'date_audience' in self.metadata:
                # Essayer de parser la date (formats acceptés: YYYY-MM-DD, DD/MM/YYYY)
                date_str = self.metadata['date_audience']
                if date_str:  # Vérifier que date_str n'est pas None
                    if '-' in date_str:
                        datetime.strptime(date_str, '%Y-%m-%d')
                    elif '/' in date_str:
                        datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            erreurs.append(f"Format date invalide: {self.metadata['date_audience']}")

        # Afficher résultats
        if erreurs:
            self.logger.error(f"❌ Validation échouée: {len(erreurs)} erreur(s)")
            for erreur in erreurs:
                self.logger.error(f"   - {erreur}")
            return False

        self.logger.info("✅ Validation métadonnées réussie")
        return True

    def step3_5_decoupage_audio(self) -> bool:
        """
        Étape 3.5: Découpage audio selon Recording Unit Remarks (NOUVEAU - Sprint 0.2).

        Cette étape lit les instructions de découpage depuis metadata_work_order.json
        (enrichi par Workflow 0) et découpe les fichiers audio AVANT analyse/transcription.

        Returns:
            True si succès (découpage appliqué ou ignoré), False si erreur critique
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 3.5/7: Découpage audio (Recording Remarks)")
        self.logger.info("=" * 60)

        # Vérifier si metadata_work_order.json disponible
        if not self.metadata_json_path or not Path(self.metadata_json_path).exists():
            self.logger.info("   ℹ️  Aucun metadata_work_order.json - découpage ignoré")
            self.logger.info("      (Exécuter Workflow 0 en premier pour bénéficier du découpage)")
            return True

        # Charger metadata_work_order.json
        try:
            with open(self.metadata_json_path, 'r', encoding='utf-8') as f:
                metadata_wo = json.load(f)
        except Exception as e:
            self.logger.warning(f"   ⚠️  Erreur lecture metadata_work_order.json: {e}")
            self.logger.warning("      Découpage ignoré")
            return True

        # Vérifier qu'il y a des fichiers audio
        if 'audio_files' not in self.metadata or not self.metadata['audio_files']:
            self.logger.warning("   ⚠️  Aucun fichier audio trouvé - découpage ignoré")
            return True

        # Découper chaque fichier audio (généralement 1 seul, mais peut être multiple)
        audio_files = [Path(f) for f in self.metadata['audio_files']]
        fichiers_decoupe = []

        for audio_file in audio_files:
            self.logger.info(f"\n   📁 Traitement: {audio_file.name}")

            # Appeler fonction de découpage
            audio_trimmed = decouper_audio_selon_remarks(audio_file, metadata_wo, self.logger)

            if audio_trimmed:
                fichiers_decoupe.append(str(audio_trimmed))
            else:
                # Pas de découpage appliqué, garder fichier original
                fichiers_decoupe.append(str(audio_file))

        # Mettre à jour la liste des fichiers audio dans metadata
        if fichiers_decoupe:
            self.metadata['audio_files'] = fichiers_decoupe
            self.logger.info(f"\n   ✅ Étape découpage audio terminée")
            self.logger.info(f"      {len(fichiers_decoupe)} fichier(s) prêt(s) pour analyse")
        else:
            self.logger.info(f"\n   ℹ️  Aucun fichier audio disponible après découpage")

        return True

    def step4_analyse_audio(self) -> bool:
        """
        Étape 4: Analyse préliminaire des fichiers audio.
        Vérifie durée, qualité, nombre de fichiers.

        Returns:
            True si succès, False sinon
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 4/6: Analyse audio préliminaire")
        self.logger.info("=" * 60)

        try:
            from pydub import AudioSegment
            from pydub.utils import mediainfo
        except ImportError:
            self.logger.warning("⚠️  pydub non installé - analyse audio limitée")
            self.logger.warning("   Installation: pip install pydub")
            # Continuer sans analyse détaillée
            self.audio_info = {
                'nombre_fichiers': len(self.metadata['audio_files']),
                'analyse_complete': False
            }
            return True

        audio_files = [Path(f) for f in self.metadata['audio_files']]
        total_duration = 0
        fichiers_info = []

        for audio_file in audio_files:
            try:
                # Charger audio
                audio = AudioSegment.from_file(str(audio_file))
                duration = len(audio) / 1000.0  # Convertir ms → secondes
                total_duration += duration

                # Informations détaillées
                info = mediainfo(str(audio_file))

                fichier_info = {
                    'nom': audio_file.name,
                    'duree_secondes': duration,
                    'duree_formatee': self._format_duration(duration),
                    'sample_rate': info.get('sample_rate', 'N/A'),
                    'channels': info.get('channels', 'N/A'),
                    'format': audio_file.suffix[1:].upper()
                }

                fichiers_info.append(fichier_info)

                self.logger.info(f"📊 {audio_file.name}:")
                self.logger.info(f"   Durée: {fichier_info['duree_formatee']}")
                self.logger.info(f"   Format: {fichier_info['format']}")
                self.logger.info(f"   Sample rate: {fichier_info['sample_rate']}")
                self.logger.info(f"   Channels: {fichier_info['channels']}")

            except Exception as e:
                self.logger.error(f"❌ Erreur analyse {audio_file.name}: {e}")
                return False

        self.audio_info = {
            'nombre_fichiers': len(audio_files),
            'duree_totale_secondes': total_duration,
            'duree_totale_formatee': self._format_duration(total_duration),
            'fichiers': fichiers_info,
            'analyse_complete': True
        }

        self.logger.info("✅ Analyse audio terminée")
        self.logger.info(f"📊 Durée totale: {self.audio_info['duree_totale_formatee']}")

        return True

    def step5_validation_croisee(self) -> bool:
        """
        Étape 5: Validation croisée page couverture ↔ audio.
        CRITIQUE: Détecte divergences et envoie email immédiat si nécessaire.

        Returns:
            True si succès (même avec divergences), False si erreur technique
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 5/6: Validation croisée page ↔ audio")
        self.logger.info("=" * 60)

        try:
            # Préparer métadonnées audio pour validation
            audio_metadata = {
                'duree_totale': self.audio_info.get('duree_totale_secondes', 0),
                'nombre_fichiers': self.audio_info.get('nombre_fichiers', 0)
            }

            # Validation via skill CISR
            validation = self.assistant.validate_page_couverture(
                self.metadata,
                audio_metadata
            )

            self.divergences = validation.get('divergences', [])
            actions_requises = validation.get('actions_requises', [])

            if validation['valide']:
                self.logger.info("✅ Validation croisée: AUCUNE divergence")
                return True

            # Divergences détectées
            self.logger.warning(f"⚠️  DIVERGENCES DÉTECTÉES: {len(self.divergences)}")
            for div in self.divergences:
                self.logger.warning(f"   - {div}")

            # Actions requises (emails, etc.)
            if actions_requises:
                self.logger.warning(f"🚨 ACTIONS REQUISES: {len(actions_requises)}")
                for action in actions_requises:
                    self.logger.warning(f"   - {action}")

                # Envoyer email si notification activée
                if self.email_notification:
                    self._send_divergence_email(validation)

            # Sauvegarder divergences dans fichier JSON
            divergences_file = self.demande_folder / 'divergences.json'
            with open(divergences_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'divergences': self.divergences,
                    'actions_requises': actions_requises,
                    'validation_complete': validation
                }, f, indent=2, ensure_ascii=False)

            self.logger.warning(f"📄 Divergences sauvegardées: {divergences_file}")

            return True  # Succès technique, même avec divergences

        except Exception as e:
            self.logger.error(f"❌ Erreur validation croisée: {e}")
            return False

    def step6_generation_rapport(self) -> bool:
        """
        Étape 6: Génération du rapport initial.
        Utilise le skill CISR pour formater le rapport.

        Returns:
            True si succès, False sinon
        """
        self.logger.info("=" * 60)
        self.logger.info("ÉTAPE 6/6: Génération rapport initial")
        self.logger.info("=" * 60)

        try:
            # Générer rapport via skill
            rapport = self.assistant.generate_rapport(
                section_type=self.metadata.get('section_type', 'SPR'),
                numero_dossier=self.metadata.get('numero_dossier', 'N/A')
            )

            # Ajouter informations supplémentaires
            rapport += f"\n\n## Métadonnées Extraites\n\n"
            rapport += f"- **Date audience**: {self.metadata.get('date_audience', 'N/A')}\n"
            rapport += f"- **Heure**: {self.metadata.get('heure_debut', 'N/A')} à {self.metadata.get('heure_fin', 'N/A')}\n"
            rapport += f"- **Participants**: {', '.join(self.metadata.get('participants', []))}\n"

            rapport += f"\n## Analyse Audio\n\n"
            rapport += f"- **Nombre de fichiers**: {self.audio_info.get('nombre_fichiers', 'N/A')}\n"
            rapport += f"- **Durée totale**: {self.audio_info.get('duree_totale_formatee', 'N/A')}\n"

            if self.divergences:
                rapport += f"\n## ⚠️ DIVERGENCES DÉTECTÉES\n\n"
                for i, div in enumerate(self.divergences, 1):
                    rapport += f"{i}. {div}\n"
            else:
                rapport += f"\n## ✅ Validation\n\nAucune divergence détectée.\n"

            rapport += f"\n---\n\n"
            rapport += f"**Généré le**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            rapport += f"**Workflow**: reception_preparation (Framework \"ii\")\n"

            # Sauvegarder rapport
            rapport_file = self.demande_folder / 'rapport_initial.md'
            with open(rapport_file, 'w', encoding='utf-8') as f:
                f.write(rapport)

            self.logger.info(f"✅ Rapport généré: {rapport_file}")

            # Sauvegarder métadonnées JSON
            metadata_file = self.demande_folder / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': self.metadata,
                    'audio_info': self.audio_info,
                    'divergences': self.divergences,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ Métadonnées JSON: {metadata_file}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Erreur génération rapport: {e}")
            return False

    def _send_divergence_email(self, validation: Dict) -> None:
        """
        Envoie un email de notification de divergences.

        Args:
            validation: Résultat de la validation croisée
        """
        try:
            dossier_info = {
                'numero_dossier': self.metadata.get('numero_dossier', 'N/A'),
                'section_type': self.metadata.get('section_type', 'N/A'),
                'date_audience': self.metadata.get('date_audience', 'N/A')
            }

            from dotenv import load_dotenv
            load_dotenv()

            destinataires = os.getenv('CISR_EMAIL_TO_UNITE_ENREGISTREMENT', '').split(',')
            cc = os.getenv('CISR_EMAIL_CC', '').split(',')
            destinataires.extend(cc)

            self.assistant.send_divergence_email(
                destinataires=destinataires,
                divergences=validation.get('divergences', []),
                dossier_info=dossier_info
            )

            self.logger.info(f"📧 Email de divergences envoyé à {len(destinataires)} destinataire(s)")

        except Exception as e:
            self.logger.error(f"❌ Erreur envoi email: {e}")

    def _format_duration(self, seconds: float) -> str:
        """Formate une durée en secondes vers HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def run(self) -> int:
        """
        Exécute le workflow complet.

        Returns:
            Code de sortie (0 = succès, 1 = erreur)
        """
        self.logger.info("🚀 Démarrage workflow: reception_preparation")
        self.logger.info(f"📁 Dossier: {self.demande_folder}")
        self.logger.info(f"📧 Notifications email: {'ACTIVÉES' if self.email_notification else 'DÉSACTIVÉES'}")

        start_time = datetime.now()

        # Exécuter les 6 étapes
        steps = [
            self.step1_reception_demande,
            self.step2_extraction_page_couverture,
            self.step3_validation_metadata,
            self.step3_5_decoupage_audio,  # NOUVEAU - Sprint 0.2
            self.step4_analyse_audio,
            self.step5_validation_croisee,
            self.step6_generation_rapport
        ]

        for i, step in enumerate(steps, 1):
            if not step():
                self.logger.error(f"❌ ÉCHEC à l'étape {i}/7")
                self.logger.error(f"⏱️  Durée totale: {datetime.now() - start_time}")
                return 1

        # Succès
        duration = datetime.now() - start_time
        self.logger.info("=" * 60)
        self.logger.info("✅ WORKFLOW TERMINÉ AVEC SUCCÈS")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Durée totale: {duration}")
        self.logger.info(f"📊 Fichiers générés:")
        self.logger.info(f"   - {self.demande_folder / 'metadata.json'}")
        self.logger.info(f"   - {self.demande_folder / 'rapport_initial.md'}")
        if self.divergences:
            self.logger.info(f"   - {self.demande_folder / 'divergences.json'}")
            self.logger.warning(f"⚠️  {len(self.divergences)} divergence(s) détectée(s)")

        return 0


def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(
        description='Workflow: Réception et Préparation de Demande de Transcription CISR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python reception_preparation.py --demande-folder ./dossier_SPR12345
  python reception_preparation.py --demande-folder ./dossier_SAR --section SAR --email-notification

Fichiers requis dans le dossier:
  - Page couverture (*.docx)
  - Fichier(s) audio (*.mp3, *.wav, *.m4a, etc.)

Fichiers générés:
  - metadata.json (métadonnées extraites)
  - rapport_initial.md (rapport formaté)
  - divergences.json (si divergences détectées)
  - logs/reception_YYYYMMDD_HHMMSS.log (journal d'exécution)
        """
    )

    parser.add_argument(
        '--demande-folder',
        required=True,
        help='Chemin vers le dossier contenant page couverture + audio'
    )

    parser.add_argument(
        '--metadata-json',
        help='Fichier metadata_work_order.json (workflow 0) pour pré-charger métadonnées'
    )

    parser.add_argument(
        '--section',
        choices=['SPR', 'SAR', 'SI', 'SAI'],
        help='Type de section CISR (optionnel, auto-détecté depuis page couverture ou metadata.json)'
    )

    parser.add_argument(
        '--email-notification',
        action='store_true',
        help='Activer les notifications email en cas de divergences'
    )

    args = parser.parse_args()

    # Créer et exécuter le workflow
    workflow = ReceptionPreparationWorkflow(
        demande_folder=args.demande_folder,
        section=args.section,
        email_notification=args.email_notification,
        metadata_json_path=args.metadata_json
    )

    exit_code = workflow.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
