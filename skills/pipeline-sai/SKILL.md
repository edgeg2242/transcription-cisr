# Skill : Pipeline SAI (Section d'Appel de l'Immigration)

## Description

Pipeline complet de transcription pour les dossiers **SAI** (Section d'Appel de l'Immigration / IAD = Immigration Appeal Division). Couvre les 4 workflows du pipeline : preparation, reception, post-traitement et certification. Produit un document Word .docx conforme aux normes CISR a partir d'un fichier audio d'audience SAI.

Les dossiers SAI concernent les **appels en matiere d'immigration** (PAS les refugies -- a ne pas confondre avec SAR). Les participants sont distincts : appelant (pas "demandeur d'asile"), conseil de l'appelant, representant du ministre.

---

## Declenchement

```
/pipeline-sai <chemin_dossier_wo>
```

Utiliser cette skill **apres** que `/analyse-work-assignment` a confirme que le type du dossier est **SAI** (IAD).

---

## Prerequis

- `/analyse-work-assignment` execute avec succes sur le Work Assignment ZIP
- Fichier `metadata_work_order.json` existant dans le dossier du Work Order
- Type confirme = SAI dans les metadonnees
- Fichier audio `.a00` localise dans la structure `DAUDIO/`
- Page couverture `.docx` fournie (comme SPR/SAR -- pas generee comme SI)
- Variables d'environnement configurees :
  - `ASSEMBLYAI_API_KEY` : Cle API pour transcription
  - `CLOUDCONVERT_API_KEY` : Cle API pour conversion audio (si serveur distant)

---

## Actions

### Workflow 0 -- Preparation

1. **Lire** `metadata_work_order.json` depuis `<chemin_dossier_wo>/`
2. **Valider** que le type = SAI (IAD = Immigration Appeal Division)
   - Numeros de dossier attendus : `MC0-xxxxx`
   - Si type different, ARRETER et signaler l'erreur
3. **Localiser** la page couverture `.docx` fournie
   - Les pages couvertures SAI sont FOURNIES (comme SPR/SAR)
   - Pattern fichier : `MC0-xxxxx [...] Page couverture [...].docx`
4. **Extraire** les metadonnees depuis la page couverture `.docx`
   - Structure des tableaux SAI : a valider vs referentiels (peu documente)
   - Extraire : numero dossier, IUC, noms participants, date audience
   - Logger un WARNING si des champs attendus sont absents (type le moins documente)
5. **Valider** la coherence des metadonnees extraites vs Excel Work Order

### Workflow 1 -- Reception et Transcription

6. **Localiser** le fichier audio dans la structure profonde
   - Pattern : `MC0-xxxxx/DAUDIO/YYYY-MM-DD/_HHMM/MC0-xxxxx/xxxx.a00`
   - Matching STRICT par 4 derniers chiffres (`startswith()`, jamais `in`)
   - Si aucun match : `FileNotFoundError` (pas de fallback silencieux)
7. **Renommer** le fichier `.a00` en `.mp3` pour compatibilite API
8. **Transcrire** via AssemblyAI API REST (pas le SDK -- incompatible Python 3.14)
   - `language_code: 'fr'`
   - `speaker_labels: True` (diarization CRITIQUE pour multi-locuteurs)
   - Endpoint upload : `POST https://api.assemblyai.com/v2/upload`
   - Endpoint transcription : `POST https://api.assemblyai.com/v2/transcript`
   - Polling : `GET https://api.assemblyai.com/v2/transcript/{id}`
9. **Sauvegarder** la transcription brute en JSON et TXT

### Workflow 2 -- Post-traitement

10. **Transcrire l'AUDIENCE COMPLETE** (comme SAR -- multi-locuteurs)
    - NE PAS extraire seulement les MOTIFS (ca c'est SPR uniquement)
    - L'audio complet (60-180 min) doit etre transcrit integralement
11. **Mapping locuteurs SAI** -- Identifier et nommer chaque participant :
    - **COMMISSAIRE** : Preside l'audience, pose les questions
    - **APPELANT** : La personne qui fait appel (PAS "demandeur d'asile")
    - **CONSEIL DE L'APPELANT** : Avocat representant l'appelant
    - **REPRESENTANT DU MINISTRE** : Represente le gouvernement
    - **INTERPRETE** : Si applicable
12. **Corrections 6 passes** :
    - Pass 1 : Termes juridiques (articles de loi, references legales)
    - Pass 2 : Noms propres et accents
    - Pass 3 : Accords grammaticaux
    - Pass 4 : Mots mal reconnus (dictionnaire AssemblyAI)
    - Pass 5 : Cross-validation metadonnees (nom commissaire vs liste officielle CISR)
    - Pass 6 : QA finale et scoring
13. **Generer le document Word CISR** avec format SAI :
    - Marges : a valider vs referentiels SAI (par defaut utiliser SAR : 1.00" L/R)
    - Police : Arial 11pt
    - Titre : a confirmer (probablement "Transcription complete..." comme SAR)
    - Tableaux metadonnees : structure a valider vs referentiels SAI
    - En-tete : numero dossier, IUC
    - Marqueur "FIN DE LA TRANSCRIPTION" en fin de document
14. **Executer** la grille QA 20 criteres CISR sur le document genere

### Workflow 3 -- Certification et Depot

15. **Ajouter** le bloc de certification finale (signature transcripteur)
16. **Appliquer** la nomenclature de fichier SAI :
    - Pattern a confirmer : `MC0-xxxxx_transcription_YYYYMMDD.docx`
17. **Nettoyer** les metadonnees Word (auteur, commentaires, revisions)
18. **Archiver** le dossier complet (audio, transcription brute, document final, rapport QA)

---

## Specificites SAI CRITIQUES

### Type de dossier

- **Section** : Section d'Appel de l'Immigration (SAI)
- **Acronyme anglais** : IAD (Immigration Appeal Division)
- **Contexte** : Appels en matiere d'**immigration** (PAS refugies -- different de SAR)
- **Numeros dossier** : `MC0-xxxxx`

### Audience et locuteurs

- **Audience COMPLETE** transcrite (comme SAR, contrairement a SPR)
- **Multi-locuteurs** : 4-6 participants typiques
- **Diarization** : CRITIQUE -- necessaire pour identifier chaque intervenant
- **Participants specifiques** : L'appelant n'est PAS un "demandeur d'asile" mais une personne faisant appel d'une decision d'immigration

### Format document

- **Format similaire a SAR** mais a confirmer avec referentiels SAI
- **Marges** : A definir (utiliser SAR 1.00" L/R par defaut en attendant)
- **Tableaux metadonnees** : Structure a valider (SAI est le type le moins documente)
- **Titre** : A confirmer (probablement "Transcription complete..." comme SAR)
- **Page couverture** : Fournie en `.docx` (pas generee comme SI)

### Statut d'implementation

- **Type le MOINS frequent** et le MOINS documente des 4 types CISR
- Marges et tableaux a valider des que referentiel SAI disponible
- Executer `/validation-qualite` des le premier WO SAI traite pour calibrer

---

## References

- @docs/CONTRAINTES.md -- Contraintes techniques du pipeline
- @docs/TYPES_DOCUMENTS.md -- Comparatif SPR/SAR/SI/SAI et participants
- @docs/CONVENTIONS_TRANSCRIPTION.md -- Regles de transcription et grille QA
- @docs/ARCHITECTURE.md -- Architecture 4 workflows du pipeline

---

## Outputs

| Fichier | Description |
|---------|-------------|
| `MC0-xxxxx_transcription_YYYYMMDD.docx` | Document Word final conforme CISR |
| `transcription_brute.txt` | Transcription brute AssemblyAI |
| `transcription_brute.json` | Transcription brute avec metadonnees |
| `rapport_corrections.json` | Detail des 6 passes de correction |
| `rapport_qa.json` | Resultat grille QA 20 criteres |
| `metadata_work_order.json` | Metadonnees enrichies du Work Order |

---

## Avertissement

> **Type le moins documente.** Les referentiels SAI (marges, tableaux, titre) ne sont pas encore confirmes. Des le premier Work Order SAI traite, executer `/validation-qualite` pour comparer le resultat avec un document de reference SAI et ajuster les parametres de formatage en consequence. Documenter toute decouverte dans `docs/TYPES_DOCUMENTS.md` et dans le CLAUDE.md du projet.
