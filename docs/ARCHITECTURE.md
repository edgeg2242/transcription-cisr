# Architecture — Pipeline de Transcription CISR

## Vue d'Ensemble

Le pipeline traite des Work Assignments (ZIP) recus de la CISR et produit des documents Word certifies.

### Flux de Donnees
```
Work Assignment (ZIP)
  |-- Work Order Excel (.xlsx) -- source de verite pour tous les WO
  |-- Pages couvertures (.docx) -- metadonnees par WO
  +-- Sous-dossiers MC-xxxxx/
      +-- DAUDIO/YYYY-MM-DD/_HHMM/MCx-xxxxx/xxxx.a00 -- audio par WO
          |
          v
  Workflow 0 : Analyse + Extraction
  -> metadata_work_order.json (1 par WO)
          |
          v
  Workflow 1 : Transcription
  -> .a00 renomme .mp3 -> AssemblyAI -> transcription_brute.txt
          |
          v
  Workflow 2 : Post-traitement
  -> 6 passes corrections -> Document Word CISR
          |
          v
  Workflow 3 : Certification + Depot
  -> Document final certifie, nomenclature CISR, upload FTP/SFTP
```

## Structure Modules src/

### src/common/
Code partage entre tous les workflows.
- `exceptions.py` : WorkOrderError, WorkflowError
- `constants.py` : TypeTranscription (bilingue FR/EN), marges CISR par type, polices, patterns regex
- `logging_setup.py` : Configuration logging + fix UTF-8 Windows (sys.stdout.reconfigure)
- `file_utils.py` : Decompression ZIP (avec protection Zip Slip), renommage .a00->.mp3, glob audio

### src/workflow_0_preparation/
Analyse et extraction des Work Assignments.
- `main.py` : CLI + orchestration (mode simple et multi-WO)
- `work_assignment_analyzer.py` : Analyse initiale adaptative de la structure d'un nouveau WA
- `excel_parser.py` : Parsing Excel multi-WO (source de verite : lignes apres headers jusqu'a ligne vide)
- `cover_page_extractor.py` : Extraction metadonnees pages couvertures SPR/SAR (generation pour SI)
- `audio_locator.py` : Localisation audio dans structure profonde DAUDIO, matching strict (startswith)
- `metadata_generator.py` : Generation metadata_work_order.json enrichi Excel
- `validators.py` : Validation metadonnees (champs obligatoires par type)

### src/workflow_1_reception/
Transcription audio via AssemblyAI.
- `main.py` : Orchestration reception
- `audio_preparer.py` : Renommage .a00->.mp3, decoupage FFmpeg si necessaire
- `transcriber.py` : API REST AssemblyAI (upload, transcription, polling, diarization)

### src/workflow_2_post_traitement/
Nettoyage, corrections et formatage Word.
- `main.py` : Orchestration post-traitement
- `text_cleaner.py` : Nettoyage texte (tics, repetitions) + extraction MOTIFS SPR (8 patterns regex)
- `corrections.py` : Pipeline 6 passes (juridique, noms/accents, accords, mots, cross-validation, QA)
- `section_formatter.py` : Pass 7 formatage titres/sections/gras
- `speaker_mapper.py` : Mapping locuteurs (A->COMMISSAIRE, B->Demandeur, etc.)
- `word_formatter.py` : Document Word CISR (marges asymetriques, tableaux bilingues, lignes intercalaires)
- `qa_validator.py` : Validation QA 20 criteres + comparaison qualite batch

### src/workflow_3_certification/
Certification et depot final.
- `main.py` : Signature, nomenclature CISR, upload FTP/SFTP, email notification

### src/tools/
Utilitaires autonomes.
- `dictionary_learner.py` : Enrichissement auto dictionnaire (compare brut vs referentiel)
- `commissioner_scraper.py` : Cache liste commissaires CISR (scraping page officielle)
- `batch_generator.py` : Traitement batch multi-WO
- `auto_optimizer.py` : Auto-optimisation pipeline (workflow 1.6)

## Schema metadata_work_order.json
```json
{
  "numero_dossier": "MC3-16722",
  "type_transcription": "SPR",
  "demandeur": "Nom PRENOM",
  "commissaire": "Prenom Nom",
  "date_audience": "2025-12-09",
  "date_decision": "2025-12-09",
  "iuc": "1234567890",
  "huis_clos": false,
  "interpretes": [],
  "conseils": [],
  "audio_file": "path/to/6722.a00",
  "duree_audio_minutes": 11,
  "work_order_number": "RCE-9878-AA",
  "region": "EASTERN"
}
```

## Structure Work Assignment Typique
```
RCE-9878-AA.zip (Work Assignment)
|-- Work Order RCE-9878-AA.xlsx          <- 1 Excel pour TOUS les WO
|-- MC3-03924/                           <- Sous-dossier WO 1
|   +-- DAUDIO/2025-12-09/_1046/MC3-03924/3924.a00
|-- MC3-16722/                           <- Sous-dossier WO 2
|   +-- DAUDIO/2025-12-09/_1046/MC3-16722/6722.a00
|-- MC3-03924 SPR.61.01 - Page couverture.docx  <- Page couverture WO 1
+-- MC3-16722 SPR.61.01 - Page couverture.docx  <- Page couverture WO 2
```

## Ressources
- `data/dictionaries/corrections_v2.1.json` : Dictionnaire corrections linguistiques
- `data/cache/commissaires_cisr.json` : Cache liste commissaires
- `data/templates/` : Templates Word (page couverture SI, signature certification)
- `referentiels/` : Transcriptions humaines gold standard par type
