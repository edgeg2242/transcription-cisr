# PRD — Pipeline de Transcription CISR

## Vision
Pipeline automatise de transcription pour la CISR (Commission de l'Immigration et du Statut de Refugie du Canada / Immigration and Refugee Board of Canada). Transforme les enregistrements audio d'audiences en documents Word conformes aux normes CISR.

## Utilisateur Cible
Fournisseur externe de transcription (ex: Regdeck FR) travaillant sous contrat avec la CISR. Recoit des Work Assignments (ZIP) contenant audio + metadonnees, produit des transcriptions Word certifiees.

## Pipeline (4 Workflows)
0. **Preparation** : Analyse Work Assignment (ZIP) -> detection type -> extraction metadonnees Excel/pages couvertures -> localisation audio
1. **Reception** : Renommage .a00->.mp3 -> transcription AssemblyAI (API REST) -> transcription brute
2. **Post-traitement** : Nettoyage -> corrections 6 passes (dictionnaire) -> mapping locuteurs -> formatage Word CISR -> validation QA
3. **Certification** : Page certification -> nettoyage annotations -> nomenclature CISR -> depot (FTP/SFTP)

## 4 Types de Documents (Bilingue FR/EN)
| FR | EN | Numeros | Contenu Audio | Priorite |
|----|----|---------|----|-----|
| SPR (Section Protection Refugies) | RPD (Refugee Protection Division) | MC1/MC2/MC3/MC4 | MOTIFS seulement (10-30 min) | P0 -- Implemente |
| SAR (Section d'Appel des Refugies) | RAD (Refugee Appeal Division) | MC5/MC6 | Audience complete (60-180 min) | P1 -- En cours |
| SI (Section de l'Immigration) | ID (Immigration Division) | 0018-Cx-xxxxx | Audience complete | P2 -- A faire |
| SAI (Section d'Appel de l'Immigration) | IAD (Immigration Appeal Division) | MC0 | Audience complete | P2 -- A faire |

## Criteres de Succes
- Similarite >=95% vs transcriptions humaines (gold standard dans referentiels/)
- 20 criteres QA passes (14 automatisables, 3 semi-auto, 3 manuels)
- Nomenclature fichier CISR conforme
- Document Word formate selon normes CISR (marges, polices, tableaux)

## Stack Technique
- Python 3.14 (pas de SDK AssemblyAI -- API REST directement)
- python-docx, openpyxl, docxcompose
- AssemblyAI API REST (transcription + diarization)
- FFmpeg (decoupage audio si necessaire)
- Fichiers .a00 = format dictaphone MP2, renommable en .mp3

## Dependances Externes
- API AssemblyAI (cle dans .env)
- Liste officielle commissaires CISR (https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx)
- Guide du Fournisseur Externe CISR (source de verite pour conventions de transcription)
