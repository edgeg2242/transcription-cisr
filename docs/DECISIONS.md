# Decisions Techniques

## API REST AssemblyAI vs SDK
**Decision** : Utiliser l'API REST directement
**Date** : 2025-12-30
**Raison** : Le SDK AssemblyAI (v0.17.0) depend de Pydantic v1, incompatible avec Python 3.14. Erreur : `AttributeError: 'Settings' object has no attribute 'api_key'`
**Alternative** : Downgrader Python vers 3.11 ou attendre mise a jour SDK Pydantic v2

## Renommage .a00->.mp3 vs Conversion Audio
**Decision** : Simple renommage d'extension (.a00 -> .mp3)
**Date** : 2025-12-30
**Raison** : Les fichiers .a00 sont du format dictaphone v4.01, reellement du MP2 audio. Un simple renommage en .mp3 suffit -- aucune conversion FFmpeg necessaire.
**Decouverte** : `xxd -l 256 fichier.a00` revele headers "dic" et "v4.01"

## FFmpeg Conserve pour Decoupage Audio
**Decision** : Garder FFmpeg dans le pipeline
**Date** : 2026-01-07
**Raison** : Bien que le renommage .a00->.mp3 remplace la conversion, FFmpeg reste necessaire pour le decoupage audio lorsque requis.
**Note** : Ne PAS utiliser pour conversion .a00->wav (inutile)

## CloudConvert Abandonne
**Decision** : Retirer CloudConvert API du pipeline
**Date** : 2026-01-07
**Raison** : Le renommage .a00->.mp3 rend CloudConvert inutile. Supprime dependance API externe et cout.
**Ancien fichier** : `audio_converter_api.py` -- supprime

## python-docx pour Formatage Word CISR
**Decision** : Utiliser python-docx + docxcompose
**Raison** : Permet le controle precis des marges asymetriques, tableaux bilingues, polices et styles CISR.

## Framework "ii" -> Chef d'Orchestre / Vibe Kanban
**Decision** : Abandonner le framework Information/Implementation
**Date** : 2026-02-17
**Raison** : Double maintenance (instruction/*.md + implementation/*.py) trop lourde et confuse. Le nouveau workflow utilise CLAUDE.md concis (~150 lignes) + docs/ pour la documentation detaillee + skills/ comme interface principale.
**Impact** : Suppression des dossiers instruction/ et .claudecode/skills/

## Skills Projet comme Interface Principale
**Decision** : Creer 8 skills CISR projet comme point d'entree principal
**Date** : 2026-02-17
**Raison** : Les skills encapsulent des workflows complets reutilisables. Le transcripteur utilise `/pipeline-spr <chemin>` au lieu de lancer des scripts manuellement.

## Encodage UTF-8 Windows
**Decision** : Forcer UTF-8 au debut de chaque script
**Date** : 2025-12-30
**Raison** : La console Windows utilise CP1252 par defaut, causant des UnicodeEncodeError avec caracteres speciaux.
**Code** : `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`

## Structure Audio Pre-Decoupee
**Decision** : Ne PAS concatener les fichiers audio multi-WO
**Date** : 2026-01-06
**Raison** : Les fichiers audio dans les ZIP multi-Work Orders sont deja pre-decoupes par la CISR. Chaque dossier MC-xxxxx contient son propre fichier audio unique. Les Recording Remarks sont informatives seulement.
