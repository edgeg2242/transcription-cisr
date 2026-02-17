# Skill : Analyse d'un Work Assignment

## Description

Analyse adaptative initiale d'un nouveau fichier ZIP (Work Assignment) recu du client CISR. Ce skill decompose le contenu du ZIP, identifie le type de transcription, compte les Work Orders, localise tous les fichiers associes (Excel, pages couvertures, audio), valide la coherence de la structure et produit un rapport d'analyse structure.

Ce skill est la **premiere etape obligatoire** de tout pipeline de transcription. Il ne modifie aucun fichier -- il observe, analyse et rapporte.

---

## Declenchement

- Reception d'un nouveau fichier ZIP du client
- Commande explicite `/analyse-work-assignment <chemin_zip>`
- Avant tout lancement de pipeline (pipeline-spr, pipeline-sar, pipeline-si, pipeline-sai)

---

## Prerequis

- Fichier ZIP accessible en lecture sur le systeme de fichiers
- Espace disque suffisant pour decompression (~2x taille ZIP)
- Python 3.x avec `openpyxl` pour lecture Excel
- `python-docx` pour inspection des pages couvertures (optionnel)

---

## Actions

### 1. Decompresser le ZIP

Extraire le contenu dans `extracted_temp/` a la racine du projet (PAS dans le dossier parent du ZIP -- voir Bonne Pratique #1 pour eviter les chemins trop longs sous Windows).

```
extracted_temp/
  RCE-XXXX-XX .../
    Work Order RCE-XXXX-XX.xlsx
    MC3-xxxxx/
    MC3-yyyyy/
    ...
```

### 2. Scanner la structure physique

Lister tous les elements a la racine du ZIP decompresse :
- Sous-dossiers nommes par numero de dossier (pattern `MC[0-6]-\d+` ou `0018-C\w-\d+`)
- Fichiers Excel Work Order (`.xlsx`)
- Pages couvertures (`.docx` contenant "Page couverture" ou "couverture" dans le nom)
- Tout autre fichier inattendu (signaler comme anomalie)

### 3. Localiser le fichier Excel Work Order

Recherche recursive du fichier Excel (source de verite) :
```
**/Work Order*.xlsx
```
Il doit y en avoir **exactement un** par Work Assignment. Si 0 ou 2+ trouves : signaler comme anomalie critique.

### 4. Detecter le type de transcription (SPR/SAR/SI/SAI)

Appliquer les regles de detection **dans cet ordre de priorite** (SPR en premier pour eviter les faux positifs "RAD") :

| Priorite | Type | Indices dans chemins/noms | Numeros dossier |
|----------|------|---------------------------|-----------------|
| 1 | **SPR** | "SPR", "RPD", "RPD FILE", "Bench" | MC1, MC2, MC3, MC4 |
| 2 | **SAR** | "SAR", "RAD" (SAUF si "PROTECTION" present) | MC5, MC6 |
| 3 | **SI** | "SI", "ID" (contexte immigration) | 0018-Cx-xxxxx |
| 4 | **SAI** | "SAI", "IAD" | MC0 |

Sources de detection (combiner toutes) :
- Nom du fichier ZIP original
- Nom du dossier racine extrait
- Chemin complet du fichier Excel (Contrainte #3)
- Prefixes des numeros de dossier dans les sous-dossiers
- Contenu des lignes Excel (si necessaire)

**ATTENTION** : Verifier SPR **AVANT** SAR pour eviter que "RAD" dans "Refugee Protection Division" soit detecte comme SAR (voir Contrainte "Ambiguite RAD").

```python
fullpath = chemin_complet.upper()
if "SPR" in fullpath or "RPD FILE" in fullpath or "BENCH" in fullpath:
    type_detecte = "SPR"
elif "SAR" in fullpath or ("RAD" in fullpath and "PROTECTION" not in fullpath):
    type_detecte = "SAR"
elif "SI" in fullpath or "ID" in fullpath:
    type_detecte = "SI"
elif "SAI" in fullpath or "IAD" in fullpath:
    type_detecte = "SAI"
else:
    type_detecte = "INCONNU"  # Signaler comme anomalie
```

### 5. Compter les Work Orders via Excel

Lire le fichier Excel pour determiner le nombre exact de Work Orders :
- Trouver la ligne d'en-tetes (chercher "File Number" ou "Numero de dossier")
- Lire toutes les lignes de donnees apres les en-tetes
- Arreter a la premiere ligne vide
- Chaque ligne avec un numero de dossier = 1 Work Order

Le nombre de lignes Excel est la **source de verite** pour le nombre de Work Orders (Contrainte #8).

### 6. Pour chaque Work Order : localiser les fichiers associes

Pour chaque numero de dossier detecte dans Excel :

**Page couverture (.docx)** :
- Chercher a la racine du ZIP decompresse : `{numero}*Page couverture*.docx` ou `{numero}*couverture*.docx`
- SPR/SAR/SAI : Page couverture FOURNIE avec metadonnees pre-remplies
- SI : Page couverture peut etre ABSENTE ou VIDE (sera generee depuis template)

**Fichier audio (.a00)** :
- Chercher dans l'arborescence profonde : `{numero}/DAUDIO/**/*.a00`
- Structure typique : `MC3-xxxxx/DAUDIO/YYYY-MM-DD/_HHMM/MC3-xxxxx/xxxx.a00`
- Nom fichier = 4 derniers chiffres du numero (MC3-56703 -> `6703.a00`)
- Matching STRICT avec `startswith()` (Contrainte #5)

### 7. Verifier la coherence

Valider que les 3 compteurs sont egaux :
```
nombre_sous-dossiers_MC == nombre_lignes_Excel == nombre_pages_couvertures
```

Si inegalite : signaler chaque ecart individuellement :
- Dossier MC present mais absent de Excel
- Ligne Excel presente mais dossier MC manquant
- Page couverture manquante pour un dossier
- Fichier audio manquant pour un dossier

### 8. Signaler les anomalies

Classifier les anomalies detectees par severite :

| Severite | Exemples |
|----------|----------|
| **CRITIQUE** | Excel manquant, type non detecte, audio manquant |
| **IMPORTANTE** | Page couverture manquante, incoherence compteurs |
| **INFO** | Structure atypique, fichiers supplementaires non attendus, nommage inhabituel |

Les clients changent parfois la structure des ZIP. Ce skill doit **s'adapter et signaler** les differences par rapport a la structure attendue, sans echouer silencieusement.

### 9. Generer le rapport d'analyse

Produire un rapport structure en deux formats :

**Format JSON** (`rapport_analyse_work_assignment.json`) :
```json
{
  "work_assignment": "RCE-XXXX-XX",
  "type_detecte": "SPR",
  "confiance_detection": "HAUTE",
  "nombre_work_orders": 6,
  "excel_path": "extracted_temp/.../Work Order RCE-XXXX-XX.xlsx",
  "work_orders": [
    {
      "numero_dossier": "MC3-16722",
      "page_couverture": "chemin/vers/MC3-16722 SPR.61.01 - Page couverture.docx",
      "audio_file": "chemin/vers/6722.a00",
      "audio_taille_mo": 12.5,
      "statut": "COMPLET"
    }
  ],
  "anomalies": [],
  "coherence": {
    "sous_dossiers": 6,
    "lignes_excel": 6,
    "pages_couvertures": 6,
    "fichiers_audio": 6,
    "coherent": true
  }
}
```

**Format texte** (affichage console) : Resume lisible avec nombre de WO, type detecte, anomalies, et recommandation de pipeline a utiliser.

---

## Specificites par Type

### SPR
- 1 seul locuteur (Commissaire) dans l'audio MOTIFS
- Page couverture detaillee (tableau 17L x 3C)
- Duree audio courte (10-30 min)
- Numeros MC1/MC2/MC3/MC4

### SAR
- 4-6 locuteurs (audience complete)
- Page couverture simplifiee (tableau 1L x 2C)
- Duree audio longue (60-180 min)
- Numeros MC5/MC6

### SI
- 4-6 locuteurs (audience complete)
- Page couverture NON fournie (a generer depuis template)
- Numeros 0018-Cx-xxxxx

### SAI
- 4-6 locuteurs (audience complete)
- Numeros MC0
- Format a confirmer (echantillon requis)

---

## References

- @docs/CONTRAINTES.md -- Contraintes #3, #5, #8, #9, #14 et ambiguite "RAD"
- @docs/TYPES_DOCUMENTS.md -- Comparatif detaille des 4 types CISR
- @docs/ARCHITECTURE.md -- Architecture pipeline 4 workflows

---

## Sorties (Outputs)

| Sortie | Format | Description |
|--------|--------|-------------|
| `rapport_analyse_work_assignment.json` | JSON | Rapport structure complet |
| Affichage console | Texte | Resume lisible avec recommandations |
| `extracted_temp/` | Dossier | Contenu ZIP decompresse |

**Sortie critique** : Le type detecte (SPR/SAR/SI/SAI) determine quel pipeline utiliser ensuite :
- SPR -> `/pipeline-spr`
- SAR -> `/pipeline-sar`
- SI -> `/pipeline-si`
- SAI -> `/pipeline-sai`
