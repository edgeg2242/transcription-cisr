# Skill : Pipeline SPR (Section de la Protection des Refugies)

## Description

Pipeline complet de transcription SPR (RPD en anglais) : de la reception du Work Order jusqu'au document Word final conforme aux normes CISR. Ce pipeline execute les 4 workflows sequentiellement (Preparation, Reception, Post-traitement, Certification) avec toutes les specificites propres au type SPR.

**Particularite fondamentale SPR** : Seule la section **MOTIFS** de la decision du commissaire est transcrite (15-30 min), PAS l'audience complete (90-120 min). Voir Contrainte #11.

---

## Declenchement

- Commande `/pipeline-spr <chemin_dossier_wo>` apres confirmation du type SPR par `analyse-work-assignment`
- Le dossier Work Order doit contenir les fichiers prepares par le skill `analyse-work-assignment`
- Peut etre lance pour un seul Work Order ou en boucle sur tous les WO d'un Work Assignment

---

## Prerequis

- Skill `analyse-work-assignment` execute avec succes
- Fichier `metadata_work_order.json` existant dans le dossier du Work Order
- Type confirme = SPR (numeros MC1, MC2, MC3 ou MC4)
- Page couverture `.docx` presente et accessible
- Fichier audio `.a00` localise
- Cle API AssemblyAI configuree dans `.env` (`ASSEMBLYAI_API_KEY`)
- Python 3.x avec dependances : `requests`, `python-docx`, `openpyxl`
- FFmpeg disponible pour conversion audio

---

## Actions

### Workflow 0 -- Preparation

#### 1. Lire metadata_work_order.json

Charger les metadonnees generees par `analyse-work-assignment` :
```json
{
  "numero_dossier": "MC3-16722",
  "type": "SPR",
  "page_couverture": "chemin/vers/fichier.docx",
  "audio_file": "chemin/vers/6722.a00",
  "excel_work_order": "chemin/vers/Work Order.xlsx"
}
```

#### 2. Valider le type = SPR

Verifier que le type est bien SPR. Si le type est different, **arreter immediatement** et rediriger vers le pipeline appropriate (SAR, SI, SAI). NE JAMAIS appliquer le formatage SPR a un autre type (Contrainte #12).

#### 3. Verifier la presence de tous les fichiers

- Page couverture `.docx` : doit exister et contenir le tableau de metadonnees (17 lignes avec lignes vides intercalaires)
- Fichier audio `.a00` : doit exister, taille > 0
- Si un fichier manque : erreur critique, pipeline arrete

#### 4. Extraire les metadonnees de la page couverture

Parser le document Word pour extraire :
- Nom du demandeur
- Nom du commissaire (a valider contre liste officielle CISR -- Contrainte #5a)
- Date d'audience
- Date de decision (specifique SPR)
- Numero IUC (10 chiffres)
- Numero de dossier (MC[1-4]-xxxxx)
- Huis clos (Oui/Non)

**Attention** : Les tableaux Word contiennent des lignes vides intercalaires. Filtrer avec `row.cells[1].text.strip()` avant extraction (Contrainte #2).

---

### Workflow 1 -- Reception et Transcription

#### 5. Convertir l'audio .a00 en WAV

Les fichiers `.a00` sont au format dictaphone v4.01 (reellement du MP2 audio). Conversion via FFmpeg :

```bash
ffmpeg -i fichier.a00 -ar 16000 -ac 1 fichier.wav
```

Performance : ~0.2 secondes pour 10 minutes d'audio.

**IMPORTANT** : NE PAS concatener de fichiers audio. Chaque Work Order contient 1 seul fichier `.a00` deja pre-decoupe par la CISR (Contrainte #9).

#### 6. Uploader vers AssemblyAI (API REST)

Utiliser l'API REST directement, **PAS le SDK AssemblyAI** (incompatible Python 3.14 a cause de Pydantic v1) :

```python
# Upload
response = requests.post(
    "https://api.assemblyai.com/v2/upload",
    headers={"authorization": API_KEY},
    data=audio_data
)
upload_url = response.json()["upload_url"]
```

#### 7. Lancer la transcription

```python
# Transcription
response = requests.post(
    "https://api.assemblyai.com/v2/transcript",
    headers={"authorization": API_KEY, "content-type": "application/json"},
    json={
        "audio_url": upload_url,
        "language_code": "fr",
        "speaker_labels": True  # Meme pour SPR (1 seul locuteur)
    }
)
transcript_id = response.json()["id"]
```

Poller `GET /v2/transcript/{transcript_id}` jusqu'a `status == "completed"`.

#### 8. Sauvegarder la transcription brute

Sauvegarder deux fichiers :
- `transcription_brute.json` : Reponse complete AssemblyAI (avec timestamps, speakers, confiance)
- `transcription_brute.txt` : Texte brut pour traitement ulterieur

---

### Workflow 2 -- Post-traitement

#### 9. EXTRAIRE LA SECTION MOTIFS SEULEMENT

**ETAPE LA PLUS CRITIQUE DU PIPELINE SPR** (Contrainte #11).

L'audio SPR contient l'audience complete (~90 min) mais le document final ne doit contenir que les **MOTIFS** de la decision du commissaire (~15-30 min, ~1 500-3 000 mots).

**Patterns de debut des MOTIFS** :
```python
debut_patterns = [
    r"Donc,?\s*j'ai eu aujourd'hui a examiner",
    r"Voici les? motifs? de (ma|la) decision",
    r"Ma decision aujourd'hui,?\s*c'est que",
    r"Je vais (maintenant|directement) vous donner (ma|les) decision",
    r"Apres avoir examine (la preuve|le dossier|les documents)",
    r"J'ai bien (etudie|examine|considere) (le dossier|la preuve)",
    r"Alors,?\s*(ma|la) decision",
    r"La demande d'asile est (acceptee|refusee|rejetee)"
]
```

**Patterns de fin des MOTIFS** :
```python
fin_patterns = [
    r"Merci pour votre temoignage",
    r"L'audience est (terminee|levee|ajournee)",
    r"Je vous remercie pour votre travail"
]
```

**Validation** : Logger le nombre de mots extraits. Fourchette attendue : 1 500 - 3 000 mots. Si hors fourchette, signaler un avertissement.

#### 10. Appliquer les 6 passes de correction

**Pass 1 -- Termes juridiques** :
Corriger les erreurs recurrentes d'AssemblyAI sur le vocabulaire juridique CISR (ex: "paragraphe 87" -> "paragraphe 97(1)", "loi sur l'immigration de la protection" -> "Loi sur l'immigration et la protection des refugies").

**Pass 2 -- Noms propres et accents** :
Corriger les noms propres, accents manquants et majuscules.

**Pass 3 -- Accords grammaticaux** :
Corriger les accords genre/nombre mal transcrits.

**Pass 4 -- Mots mal reconnus** :
Appliquer le dictionnaire de corrections (`Documentation/CISR_Corrections_Dictionary.json`) pour les erreurs specifiques a AssemblyAI (ex: "FESPOLA" -> "Hezbollah", "soumis" -> "sunnite").

**Pass 5 -- Cross-validation metadonnees** :
Verifier que le nom du commissaire apparait dans le texte. Valider la coherence des numeros de dossier.

**Pass 6 -- QA finale** :
Evaluer la qualite selon la grille QA CISR (20 criteres). Generer un score et un rapport.

#### 11. Generer le document Word CISR

Creer le document Word avec le formatage SPECIFIQUE SPR :

**Marges SPR** :
```python
section.top_margin = Inches(1.25)
section.bottom_margin = Inches(0.63)
section.left_margin = Inches(0.50)   # SPR = 0.50" (pas 1.00" comme SAR)
section.right_margin = Inches(0.50)
```

**Tableau 1 -- Metadonnees bilingues** (17 lignes x 3 colonnes) :
- 9 lignes de donnees + 8 lignes vides intercalaires (Bonne Pratique #5)
- Colonnes : Label FR | Valeur | Label EN
- Contenu : Demandeur, Commissaire, Date audience, Date decision, IUC, Numero dossier, Huis clos, etc.
- Police : Arial 11pt

**Tableau 2 -- Separateur** (1 ligne x 1 colonne) :
- Cellule vide (separateur visuel)

**Titre du document** :
"TRANSCRIPTION DES Motifs..." (format SPR specifique, PAS "Transcription complete..." qui est pour SAR)

**Police et style** :
- Arial 11pt pour tout le contenu
- Locuteur en MAJUSCULES GRAS : **COMMISSAIRE :**
- Interligne simple
- Pas de retrait de premiere ligne

**Locuteur unique** :
- SPR = 1 seul locuteur (le Commissaire qui dicte ses motifs)
- Tout le texte est prefixe par **COMMISSAIRE :** au debut, puis paragraphes continus

---

### Workflow 3 -- Certification et Depot

#### 12. Ajouter la signature de certification

Inserer le bloc de certification du transcripteur a la fin du document, avant le marqueur "FIN DES MOTIFS".

Template : `Documentation/Templates/signature certification.docx`

#### 13. Appliquer la nomenclature CISR

Nommer le fichier final selon la convention :
```
MC[1-4]-xxxxx_transcription_YYYYMMDD.docx
```
Exemple : `MC3-16722_transcription_20260107.docx`

#### 14. Depot final

Placer le document dans le dossier de sortie du Work Order :
```
Test_Pipeline/Test_Demandes/MC3-xxxxx/
  metadata_work_order.json
  transcription_brute.json
  transcription_brute.txt
  MC3-xxxxx_transcription_YYYYMMDD.docx   <-- Document final
  rapport_qa.json                          <-- Rapport qualite
```

---

## Specificites SPR CRITIQUES

Ces regles sont **propres au type SPR** et NE s'appliquent PAS aux autres types (Contrainte #12) :

| Specificite | Valeur SPR | Valeur SAR (comparaison) |
|-------------|-----------|--------------------------|
| Contenu transcrit | **MOTIFS seulement** (15-30 min) | Audience COMPLETE (60-180 min) |
| Nombre de locuteurs | **1** (Commissaire) | 4-6 (multi-parties) |
| Diarization | Non requise | CRITIQUE |
| Marges gauche/droite | **0.50"** | 1.00" (DOUBLE) |
| Marge bas | **0.63"** | 0.69" |
| Tableau 1 | **17L x 3C** (metadonnees) | 1L x 2C (numeros dossiers) |
| Tableau 2 | **1L x 1C** (vide) | 15L x 3C (metadonnees) |
| "Date decision" | **OUI** (presente) | NON (absente) |
| Titre document | **"TRANSCRIPTION DES Motifs..."** | "Transcription complete..." |
| Numeros dossier | **MC1, MC2, MC3, MC4** | MC5, MC6 |
| Page couverture | **Fournie** (.docx avec metadonnees) | Fournie (.docx simplifie) |
| Duree audio typique | **10-30 min** | 60-180 min |

---

## References

- @docs/CONTRAINTES.md -- Contraintes #2, #5, #5a, #8, #9, #11, #12, #14 et ambiguite "RAD"
- @docs/CONVENTIONS_TRANSCRIPTION.md -- Regles de transcription, ponctuation, marqueurs, grille QA 20 criteres
- @docs/TYPES_DOCUMENTS.md -- Comparatif detaille SPR vs SAR vs SI vs SAI

---

## Sorties (Outputs)

| Sortie | Format | Description |
|--------|--------|-------------|
| `MC[1-4]-xxxxx_transcription_YYYYMMDD.docx` | Word | Document final conforme CISR |
| `rapport_qa.json` | JSON | Rapport qualite (score, 20 criteres, anomalies) |
| `transcription_brute.json` | JSON | Reponse brute AssemblyAI (archive) |
| `transcription_brute.txt` | Texte | Transcription brute texte (archive) |
| Affichage console | Texte | Progression, warnings, score QA final |

**Critere de succes** : Score QA >= 17/20 (PASS conditionnel minimum). Cible : 20/20.
