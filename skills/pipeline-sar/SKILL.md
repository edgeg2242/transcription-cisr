# Pipeline SAR (Section d'Appel des Refugies / Refugee Appeal Division)

Pipeline complet de transcription pour les dossiers **SAR (RAD)** -- audience complete, multi-locuteurs. Ce skill orchestre les 4 workflows sequentiels : preparation, reception, post-traitement et certification pour produire un document Word conforme aux normes CISR de type SAR.

---

## Declenchement

```
/pipeline-sar <chemin_dossier_wo>
```

Utiliser ce skill **apres** que `analyse-work-assignment` a confirme que le type du dossier est **SAR** (ou RAD). Le chemin pointe vers le dossier du Work Order individuel (ex: `Test_Pipeline/Test_Demandes/MC5-34977/`).

---

## Prerequis

- Le skill `analyse-work-assignment` a ete execute sur le Work Assignment (ZIP)
- Le fichier `metadata_work_order.json` existe dans le dossier du Work Order
- Le type detecte dans les metadonnees est `SAR` (ou `RAD`)
- Le fichier audio `.a00` est localise et accessible
- La page couverture `.docx` est presente (structure simplifiee SAR)
- La cle API AssemblyAI est configuree dans `.env` (`ASSEMBLYAI_API_KEY`)
- FFmpeg est disponible pour la conversion audio

---

## Actions

### Workflow 0 -- Preparation

1. **Lire `metadata_work_order.json`** depuis le dossier du Work Order
2. **Valider le type = SAR** -- Verifier que le champ `type_transcription` est bien SAR/RAD. Si le type ne correspond pas, **arreter immediatement** et signaler l'erreur
3. **Traiter la page couverture SAR** -- Structure simplifiee :
   - Tableau **1L x 2C** contenant les numeros de dossiers uniquement (pas de metadonnees completes)
   - Extraire les deux numeros de dossier : **MC5-xxxxx** (SAR) + **MC2/3-xxxxx** (SPR original)
   - NE PAS s'attendre a un tableau 17L x 3C comme pour SPR
4. **Valider la coherence** des metadonnees :
   - Numeros de dossier format MC5/MC6 (SAR)
   - Absence de "Date decision" = OK (normal pour SAR)
   - Presence IUC (Identifiant Unique du Cas)

### Workflow 1 -- Reception et transcription

5. **Renommer le fichier audio** : `.a00` -> `.mp3` (le format .a00 est du MP2 dictaphone compatible MP3)
6. **Uploader et transcrire via AssemblyAI API REST** :
   ```
   POST https://api.assemblyai.com/v2/upload
   POST https://api.assemblyai.com/v2/transcript
   GET  https://api.assemblyai.com/v2/transcript/{id}
   ```
   Parametres obligatoires :
   - `language_code` : `'fr'`
   - `speaker_labels` : `True` (diarization ACTIVEE)
   - NE PAS utiliser le SDK AssemblyAI (incompatible Python 3.14)
7. **Diarization CRITIQUE** -- Identifier **4 a 6 locuteurs** distincts :
   - COMMISSAIRE(S) (1 a 3)
   - DEMANDEUR D'ASILE / APPELANT
   - CONSEIL du demandeur
   - REPRESENTANT DU MINISTRE
   - INTERPRETE (si applicable)
   - Valider que le nombre de locuteurs detectes est coherent (minimum 2, typiquement 4-6)

### Workflow 2 -- Post-traitement

8. **Transcrire l'AUDIENCE COMPLETE** (60-180 min) :
   - Pour les SAR, on transcrit **TOUT** le contenu audio, pas seulement les motifs
   - NE PAS appliquer l'extraction de section MOTIFS (c'est reserve aux SPR uniquement)
   - Duree attendue : 60 a 180 minutes d'audio
9. **Mapping des locuteurs** -- Associer chaque speaker detecte par AssemblyAI a son role :
   - Speaker A -> **COMMISSAIRE :**
   - Speaker B -> **DEMANDEUR D'ASILE :**
   - Speaker C -> **CONSEIL :**
   - Speaker D -> **INTERPRETE :**
   - Speaker E -> **REPRESENTANT DU MINISTRE :**
   - Le mapping se fait par analyse du contenu et du contexte des interventions
10. **Appliquer les corrections en 6 passes** :
    - Pass 1 : Termes juridiques (articles de loi, references legales)
    - Pass 2 : Noms propres et accents
    - Pass 3 : Accords grammaticaux
    - Pass 4 : Mots mal reconnus (dictionnaire de corrections)
    - Pass 5 : Cross-validation metadonnees (nom commissaire vs liste officielle CISR)
    - Pass 6 : QA finale et scoring
11. **Generer le document Word CISR format SAR** :
    - **Marges SAR** :
      - Haut : 1.25"
      - Bas : **0.69"** (different de SPR 0.63")
      - Gauche : **1.00"** (DOUBLE de SPR 0.50")
      - Droite : **1.00"** (DOUBLE de SPR 0.50")
    - **Tableau 1** : **1L x 2C** -- Numeros de dossiers uniquement (MC5-xxxxx | MC2/3-xxxxx)
    - **Tableau 2** : **15L x 3C** -- Metadonnees bilingues FR/EN (structure inversee par rapport a SPR)
    - **Titre** : "Transcription complete de l'audience" (PAS "TRANSCRIPTION DES Motifs...")
    - **Pas de "Date decision"** dans le document final
    - **Police** : Arial 11pt
    - **Identification locuteurs** : Chaque intervention prefixee par le role en MAJUSCULES GRAS

### Workflow 3 -- Certification et depot

12. **Ajouter le bloc de certification** :
    - Signature du transcripteur
    - Date de certification
    - Nom de l'agence
    - Marqueur "FIN DE LA TRANSCRIPTION"
13. **Appliquer la nomenclature SAR** :
    - Format fichier : `MC5-xxxxx_transcription_YYYYMMDD.docx`
14. **Generer le rapport QA** :
    - Score qualite initiale (formule : 100 - critiques x 2 - moderees x 1)
    - Liste des corrections appliquees par passe
    - Alertes sur les elements necessitant revision manuelle

---

## Specificites SAR CRITIQUES

Ces differences par rapport au pipeline SPR sont **non negociables** :

| Aspect | SPR | SAR |
|--------|-----|-----|
| **Contenu transcrit** | MOTIFS seulement (15-30 min) | AUDIENCE COMPLETE (60-180 min) |
| **Locuteurs** | 1 (Commissaire) | 4-6 (multi-parties) |
| **Diarization** | Non requise | CRITIQUE |
| **Marges L/R** | 0.50" | **1.00"** (DOUBLE) |
| **Marges Bas** | 0.63" | **0.69"** |
| **Tableau 1** | 17L x 3C (metadonnees) | **1L x 2C** (numeros dossiers) |
| **Tableau 2** | 1L x 1C (vide) | **15L x 3C** (metadonnees) |
| **Titre** | "TRANSCRIPTION DES Motifs..." | "Transcription complete..." |
| **Date decision** | OUI | **NON** |
| **Page couverture** | Fournie, tableau detaille | Fournie, **tableau simplifie** |
| **Numeros dossier** | MC1/MC2/MC3/MC4 | **MC5/MC6** |
| **Extraction MOTIFS** | OUI (patterns regex) | **NON** (audience entiere) |

**Regles imperatives** :
- NE JAMAIS appliquer les marges SPR (0.50") a un document SAR
- NE JAMAIS extraire seulement les MOTIFS d'un audio SAR
- NE JAMAIS generer un tableau 17L x 3C pour un document SAR
- TOUJOURS valider que le type detecte est bien SAR avant de formater
- TOUJOURS activer la diarization pour les transcriptions SAR

---

## References

- @docs/CONTRAINTES.md -- Contraintes #1 (page couverture SAR), #3 (detection type chemin), #12 (types differents)
- @docs/TYPES_DOCUMENTS.md -- Tableau comparatif complet SPR/SAR/SI/SAI, bloqueurs production SAR
- @docs/CONVENTIONS_TRANSCRIPTION.md -- Regles de transcription, identification locuteurs, ponctuation

---

## Sorties

| Fichier | Description |
|---------|-------------|
| `MC5-xxxxx_transcription_YYYYMMDD.docx` | Document Word conforme CISR format SAR |
| `MC5-xxxxx_rapport_qa.json` | Rapport qualite avec score et corrections detaillees |
| `MC5-xxxxx_transcription_brute.txt` | Transcription brute AssemblyAI (archive) |
| `MC5-xxxxx_transcription_PIPELINE_COMPLET.txt` | Transcription apres les 6 passes de correction (archive) |
