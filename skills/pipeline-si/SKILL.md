# Pipeline SI (Section de l'Immigration / Immigration Division)

Pipeline complet de transcription pour les dossiers **SI (ID)** -- audience complete, multi-locuteurs, avec **generation de la page couverture** depuis un template. Ce skill orchestre les 4 workflows sequentiels pour les enquetes d'immigration (admissibilite, detention, renvoi).

---

## Declenchement

```
/pipeline-si <chemin_dossier_wo>
```

Utiliser ce skill **apres** que `analyse-work-assignment` a confirme que le type du dossier est **SI** (ou ID). Le chemin pointe vers le dossier du Work Order individuel (ex: `Test_Pipeline/Test_Demandes/0018-C1-12345/`).

---

## Prerequis

- Le skill `analyse-work-assignment` a ete execute sur le Work Assignment (ZIP)
- Le fichier `metadata_work_order.json` existe dans le dossier du Work Order
- Le type detecte dans les metadonnees est `SI` (ou `ID`)
- Le fichier audio `.a00` est localise et accessible
- Le template de page couverture SI est present : `data/templates/cover_page_SI_template.docx`
- La cle API AssemblyAI est configuree dans `.env` (`ASSEMBLYAI_API_KEY`)
- FFmpeg est disponible pour la conversion audio

---

## Actions

### Workflow 0 -- Preparation

1. **Lire `metadata_work_order.json`** depuis le dossier du Work Order
2. **Valider le type = SI** -- Verifier que le champ `type_transcription` est bien SI/ID. Si le type ne correspond pas, **arreter immediatement** et signaler l'erreur
3. **CRITIQUE : Page couverture NON fournie** (ou fournie VIDE sans metadonnees) :
   - Contrairement aux SPR et SAR, les dossiers SI ne contiennent **pas de page couverture pre-remplie**
   - Le systeme doit **GENERER** la page couverture a partir du template
4. **Generer la page couverture depuis le template** :
   - Template source : `data/templates/cover_page_SI_template.docx`
   - Remplir les champs avec les metadonnees disponibles
   - **Sources de metadonnees** (par ordre de priorite) :
     1. Fichier Excel Work Order (source primaire)
     2. Nom des fichiers dans le dossier (numeros de dossier, dates)
     3. Transcription audio (noms des participants, si necessaire en second passage)
5. **Valider le numero de dossier** :
   - Format SI : `0018-Cx-xxxxx` (PAS le format MCx-xxxxx utilise par SPR/SAR)
   - Detecter via regex : `r'0018-C\d-\d{5}'`
   - Si format MCx detecte, **alerter** : possible erreur de type

### Workflow 1 -- Reception et transcription

6. **Renommer le fichier audio** : `.a00` -> `.mp3` (le format .a00 est du MP2 dictaphone compatible MP3)
7. **Uploader et transcrire via AssemblyAI API REST** :
   ```
   POST https://api.assemblyai.com/v2/upload
   POST https://api.assemblyai.com/v2/transcript
   GET  https://api.assemblyai.com/v2/transcript/{id}
   ```
   Parametres obligatoires :
   - `language_code` : `'fr'`
   - `speaker_labels` : `True` (diarization ACTIVEE)
   - NE PAS utiliser le SDK AssemblyAI (incompatible Python 3.14)

### Workflow 2 -- Post-traitement

8. **Transcrire l'AUDIENCE COMPLETE** :
   - Comme pour les SAR, les SI transcrivent **TOUT** le contenu audio
   - NE PAS appliquer l'extraction de section MOTIFS (reserve aux SPR uniquement)
   - Contexte : enquetes d'immigration (admissibilite, detention, mesures de renvoi)
9. **Mapping des locuteurs SI** -- Les roles sont specifiques au contexte immigration :
   - Speaker A -> **COMMISSAIRE :**
   - Speaker B -> **PERSONNE CONCERNEE :** (PAS "Demandeur d'asile" -- terminologie SI)
   - Speaker C -> **CONSEIL :**
   - Speaker D -> **REPRESENTANT DU MINISTRE :**
   - Speaker E -> **INTERPRETE :** (si applicable)
   - **Difference terminologique critique** : En SI, le sujet de l'enquete est la "personne concernee", jamais le "demandeur d'asile" (terme SPR/SAR)
10. **Appliquer les corrections en 6 passes** :
    - Pass 1 : Termes juridiques (LIPR, articles immigration, mesures de renvoi)
    - Pass 2 : Noms propres et accents
    - Pass 3 : Accords grammaticaux
    - Pass 4 : Mots mal reconnus (dictionnaire de corrections)
    - Pass 5 : Cross-validation metadonnees (nom commissaire vs liste officielle CISR section SI)
    - Pass 6 : QA finale et scoring
11. **Generer le document Word CISR format SI** :
    - Appliquer le formatage specifique SI (marges, tableaux, titre)
    - Police : Arial 11pt
    - Identification locuteurs : chaque intervention prefixee par le role en MAJUSCULES GRAS
    - Integrer les metadonnees de la page couverture generee

### Workflow 3 -- Certification et depot

12. **Ajouter le bloc de certification** :
    - Signature du transcripteur
    - Date de certification
    - Nom de l'agence
    - Marqueur "FIN DE LA TRANSCRIPTION"
13. **Appliquer la nomenclature SI** :
    - Format fichier integrant le numero 0018-Cx-xxxxx
14. **Generer le rapport QA** :
    - Score qualite initiale
    - Liste des corrections appliquees par passe
    - **Alerte specifique** : Validation de la page couverture generee (comparer avec les metadonnees source)
    - Alertes sur les elements necessitant revision manuelle

---

## Specificites SI CRITIQUES

### Page couverture GENEREE -- Difference majeure

C'est la difference fondamentale entre le pipeline SI et les pipelines SPR/SAR :

| Aspect | SPR / SAR | SI |
|--------|-----------|-----|
| **Page couverture** | Fournie en .docx pre-remplie | **NON fournie -- GENEREE depuis template** |
| **Source metadonnees** | Extraction depuis .docx existant | **Construction depuis Excel + noms fichiers + audio** |
| **Template** | Aucun (document fourni) | `data/templates/cover_page_SI_template.docx` |

**Procedure de generation** :
1. Charger le template `cover_page_SI_template.docx`
2. Extraire les metadonnees depuis l'Excel Work Order (colonnes pertinentes)
3. Completer avec les informations extraites des noms de fichiers (numero dossier, dates)
4. Si des champs restent vides apres Excel + noms fichiers, les marquer comme `[A COMPLETER]`
5. Sauvegarder la page couverture generee dans le dossier du Work Order

### Terminologie et numeros de dossier

| Aspect | SPR | SAR | SI |
|--------|-----|-----|-----|
| **Numeros** | MC1/MC2/MC3/MC4 | MC5/MC6 | **0018-Cx-xxxxx** |
| **Sujet** | Demandeur d'asile | Appelant | **Personne concernee** |
| **Contexte** | Protection refugies | Appel decision SPR | **Enquete immigration** |
| **Types enquetes** | N/A | N/A | Admissibilite, detention, renvoi |

### Locuteurs SI vs SPR vs SAR

| Role | SPR | SAR | SI |
|------|-----|-----|-----|
| Locuteur principal | COMMISSAIRE (seul) | COMMISSAIRE(S) | COMMISSAIRE |
| Sujet de l'audience | N/A (motifs seulement) | DEMANDEUR D'ASILE | **PERSONNE CONCERNEE** |
| Avocat | N/A | CONSEIL | CONSEIL |
| Gouvernement | N/A | REPRESENTANT DU MINISTRE | REPRESENTANT DU MINISTRE |
| Traducteur | N/A | INTERPRETE | INTERPRETE |

---

## References

- @docs/CONTRAINTES.md -- Contraintes #12 (types fondamentalement differents), #14 (nomenclature Work Assignment vs Work Order)
- @docs/TYPES_DOCUMENTS.md -- Tableau comparatif SI, bloqueurs production SI, convention nomenclature fichiers SI

---

## Sorties

| Fichier | Description |
|---------|-------------|
| `0018-Cx-xxxxx_transcription_YYYYMMDD.docx` | Document Word conforme CISR format SI |
| `0018-Cx-xxxxx_page_couverture.docx` | Page couverture **GENEREE** depuis template |
| `0018-Cx-xxxxx_rapport_qa.json` | Rapport qualite avec score et corrections detaillees |
| `0018-Cx-xxxxx_transcription_brute.txt` | Transcription brute AssemblyAI (archive) |
| `0018-Cx-xxxxx_transcription_PIPELINE_COMPLET.txt` | Transcription apres les 6 passes de correction (archive) |
