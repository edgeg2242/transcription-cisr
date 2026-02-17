# Transcription CISR — Pipeline Automatisé

## Langue
TOUJOURS communiquer en français. Code source en anglais accepté.
Commentaires code en français acceptés.

## Aperçu
Pipeline de transcription automatisée pour la CISR (Commission de l'Immigration
et du Statut de Réfugié du Canada / Immigration and Refugee Board of Canada).
Traite les audiences audio (.a00 = MP2 dictaphone, renommable en .mp3),
transcrit via AssemblyAI, génère des documents Word conformes aux normes CISR.

## Stack
- Python 3.14 (pas de SDK AssemblyAI — utiliser API REST directement)
- python-docx, openpyxl, docxcompose
- AssemblyAI API REST (transcription + diarization)
- FFmpeg (découpage audio si nécessaire)
- Fichiers .a00 = renommer en .mp3 (PAS de conversion nécessaire)

## Pipeline (4 workflows)
0. **Préparation** : ZIP → analyse structure → Excel parsing → métadonnées
1. **Réception** : .a00 → .mp3 (renommage) → AssemblyAI → transcription brute
2. **Post-traitement** : Nettoyage → corrections 6 passes → document Word CISR
3. **Certification** : Signature → nomenclature → dépôt final

## 4 Types de Documents (CRITIQUE — Bilingue FR/EN)
| FR | EN | Numéros dossier |
|----|----|----|
| SPR (Section Protection des Réfugiés) | RPD (Refugee Protection Division) | MC1/MC2/MC3/MC4 |
| SAR (Section d'Appel des Réfugiés) | RAD (Refugee Appeal Division) | MC5/MC6 |
| SI (Section de l'Immigration) | ID (Immigration Division) | 0018-Cx-xxxxx |
| SAI (Section d'Appel de l'Immigration) | IAD (Immigration Appeal Division) | MC0 |

Ces 4 types ont des structures, formats et contenus FONDAMENTALEMENT DIFFÉRENTS.
TOUJOURS vérifier le type AVANT d'appliquer tout formatage.
@docs/TYPES_DOCUMENTS.md

## Terminologie Critique
- **Work Assignment** : Fichier ZIP initial (contient PLUSIEURS Work Orders)
- **Work Order** : Dossier individuel pour UNE transcription (MC3-xxxxx)
- NE PAS supposer 1 ZIP = 1 Work Order (typiquement 4-10 WO par ZIP)

## Analyse Initiale Adaptative
Les clients changent parfois la structure des documents fournis. TOUJOURS faire
une analyse initiale de chaque nouveau Work Assignment reçu pour comprendre
la structure des fichiers/dossiers avant de lancer le pipeline.
Utiliser le skill `/analyse-work-assignment` pour cela.

## Architecture & Documentation
@docs/ARCHITECTURE.md — Flux données, modules src/, schéma metadata JSON
@docs/CONTRAINTES.md — Toutes contraintes #1-#14 (audio, Excel, pages couvertures, Word, qualité)
@docs/CONVENTIONS_TRANSCRIPTION.md — Règles CISR (Guide Fournisseur) + grille QA 20 erreurs
@docs/TYPES_DOCUMENTS.md — Comparatif bilingue SPR/SAR/SI/SAI complet
@docs/DECISIONS.md — Choix techniques et pourquoi
@docs/PRD.md — Vision projet, critères succès, priorités par type

## Skills Globaux Disponibles
- **task-segmentation** : Tâches kanban >=5 items → sous-tâches parallèles VK
- **code-review** : Audit PRs avec 4 agents parallèles. AVANT chaque merge.
- **youtube-summarizer** : Extraire/synthétiser contenu vidéo YouTube
- **find-skills** : Découvrir et installer de nouveaux skills
- **inference-sh** : 150+ apps IA cloud (LLMs, génération, recherche)
- **agentic-browser** : Automatisation navigateur (scraping, formulaires)

## Skills Projet CISR (Dans skills/)
- **/analyse-work-assignment** : Analyse initiale adaptative d'un nouveau WA
- **/pipeline-spr** : Pipeline complet transcription SPR (MOTIFS seulement)
- **/pipeline-sar** : Pipeline complet transcription SAR (audience complète)
- **/pipeline-si** : Pipeline complet transcription SI (page couverture générée)
- **/pipeline-sai** : Pipeline complet transcription SAI (appel immigration)
- **/validation-qualite** : Comparer résultat vs référentiel gold standard
- **/enrichissement-dictionnaire** : Enrichir dictionnaire corrections post-WO
- **/learning-loop** : Boucle d'apprentissage continu (analyse erreurs → amélioration systématique)

## Référentiels (Gold Standard)
referentiels/ contient des transcriptions humaines validées par type.
Utiliser pour comparer, enrichir le dictionnaire, valider le formatage.
@referentiels/README.md

## Règles pour CHAQUE Tâche
- Lire les fichiers existants AVANT de modifier
- NE JAMAIS supposer SPR = SAR (formats différents)
- Matching audio STRICT (startswith, jamais `in`)
- Échouer bruyamment : jamais de fallback silencieux
- .a00 → renommer en .mp3 (PAS de conversion)
- FFmpeg pour découpage audio uniquement
- Fix UTF-8 Windows au début de chaque script
- Utiliser /code-review avant merge de PR
- Utiliser /learning-loop après chaque lot de WO traité
