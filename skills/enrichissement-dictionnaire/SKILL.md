# Skill : Enrichissement du Dictionnaire de Corrections

## Description

Enrichit progressivement le dictionnaire de corrections (`data/dictionaries/corrections_v2.1.json`) apres le traitement de chaque Work Order. Ce skill compare la transcription brute AssemblyAI avec un document de reference humain (gold standard) ou le document final corrige, detecte les erreurs residuelles non couvertes par le dictionnaire actuel, les classifie par pass (1-4), filtre les faux positifs, et propose de nouvelles entrees pour validation humaine.

Ce skill est au coeur du systeme d'**apprentissage continu** : a chaque Work Order traite, le dictionnaire s'ameliore, ce qui augmente la qualite des futures transcriptions.

---

## Declenchement

- Commande explicite `/enrichissement-dictionnaire` apres le traitement de chaque Work Order
- Manuellement quand de nouveaux patterns d'erreurs sont identifies lors de revisions humaines
- Automatiquement par le skill `/learning-loop` quand des erreurs dictionnaire sont detectees

---

## Prerequis

- **Transcription brute** : Fichier JSON ou TXT issu d'AssemblyAI (sortie du Workflow 1)
- **Document reference humain** (gold standard) dans `referentiels/` OU document final corrige (sortie du Workflow 2)
- **Dictionnaire existant** : `data/dictionaries/corrections_v2.1.json` present et valide
- Python 3.x avec `difflib` (bibliotheque standard)
- `python-docx` si le document de reference est au format `.docx`

---

## Actions

### 1. Charger la transcription brute AssemblyAI

Lire le fichier de transcription brute produit par le Workflow 1 :
- Format JSON : extraire le champ `text` ou les `utterances` selon la structure
- Format TXT : lire le contenu textuel complet
- Normaliser le texte (minuscules pour comparaison, conserver original pour contexte)

### 2. Charger le document reference humain

Lire le gold standard ou le document corrige final :
- Si `.docx` : extraire le texte de tous les paragraphes avec `python-docx`
- Si `.txt` : lecture directe
- Normaliser de la meme maniere que la transcription brute

### 3. Comparer mot-a-mot avec algorithme de similarite

Utiliser `difflib.SequenceMatcher` pour identifier les differences :

```python
import difflib

matcher = difflib.SequenceMatcher(None, mots_bruts, mots_reference)
differences = []

for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == 'replace':
        for k in range(min(i2 - i1, j2 - j1)):
            mot_incorrect = mots_bruts[i1 + k]
            mot_correct = mots_reference[j1 + k]
            differences.append((mot_incorrect, mot_correct))
```

### 4. Detecter les erreurs residuelles

Pour chaque difference detectee :
- Verifier si la paire (incorrect, correct) existe deja dans le dictionnaire actuel
- Si elle n'existe PAS : c'est une erreur residuelle, candidate a l'enrichissement
- Calculer le ratio de similarite entre les deux mots (`SequenceMatcher.ratio()`)

### 5. Classifier chaque erreur par pass

Appliquer la classification automatique dans cet ordre :

| Pass | Type | Criteres de detection |
|------|------|----------------------|
| **Pass 1** | Termes juridiques | Mot contient : "article", "paragraphe", "loi", "convention", "alinea", "statut", "protection", "refugie" |
| **Pass 2** | Noms propres et accents | Difference UNIQUEMENT sur les accents (ex: "regie" vs "regie") ou majuscules |
| **Pass 3** | Accords grammaticaux | Difference de genre/nombre (terminaisons -e/-es/-s, -eur/-euse, -if/-ive) |
| **Pass 4** | Mots mal reconnus | Toutes les autres erreurs (defaut) |

```python
def classifier_erreur(mot_incorrect, mot_correct):
    termes_juridiques = ['article', 'paragraphe', 'loi', 'convention',
                         'alinea', 'statut', 'protection', 'refugie',
                         'requerant', 'commissaire', 'tribunal']

    # Pass 1 : Termes juridiques
    for terme in termes_juridiques:
        if terme in mot_incorrect.lower() or terme in mot_correct.lower():
            return 'pass1_termes_juridiques'

    # Pass 2 : Accents seulement
    if difference_seulement_accents(mot_incorrect, mot_correct):
        return 'pass2_noms_propres_accents'

    # Pass 3 : Accords grammaticaux
    if difference_accord_genre_nombre(mot_incorrect, mot_correct):
        return 'pass3_accords_grammaticaux'

    # Pass 4 : Autres (defaut)
    return 'pass4_mots_mal_reconnus'
```

### 6. Filtrer les faux positifs

Appliquer les filtres obligatoires (Contrainte #7 -- Faux Positifs V2.1) :

**Blacklist mots courants contextuels** (ne jamais proposer comme corrections) :
```python
BLACKLIST_CONTEXTUELS = {
    "de", "des", "le", "les", "la", "l",
    "vous", "vos", "votre",
    "une", "un", "ne",
    "est", "et", "a", "au", "aux",
    "du", "d", "en", "y",
    "se", "ce", "ses", "ces",
    "ou", "ou", "que", "qui"
}
```

**Seuil de similarite** :
- Similarite >= 85% pour accepter une proposition (PAS 70% -- trop de faux positifs)
- Ignorer les differences de ponctuation seule (virgule, point, tiret)
- Ignorer les differences de casse seule (majuscule/minuscule)

**Longueur minimale** :
- Ignorer les mots de 2 caracteres ou moins

### 7. Proposer les nouvelles entrees (mode proposition)

**REGLE CRITIQUE** : Toujours en mode proposition d'abord, JAMAIS d'ajout automatique non valide.

Generer une liste de propositions structuree :

```
=== PROPOSITIONS D'ENRICHISSEMENT DICTIONNAIRE ===
Transcription brute : MC3-16722_transcription_brute.txt
Reference          : MC3-16722_reference_humaine.docx
Date               : 2026-01-08

--- Pass 1 : Termes juridiques (3 propositions) ---
  [1] "paragraphe 87"  ->  "paragraphe 97(1)"
      Similarite : 88% | Contexte : "...en vertu du paragraphe 87 de la loi..."
  [2] "loi sur l'immigration de la protection"  ->  "loi sur l'immigration et la protection"
      Similarite : 95% | Contexte : "...la loi sur l'immigration de la protection des refugies..."

--- Pass 4 : Mots mal reconnus (2 propositions) ---
  [3] "FESPOLA"  ->  "Hezbollah"
      Similarite : 42% | Contexte : "...membre du FESPOLA au Liban..."

--- Faux positifs filtres : 5 ---
  - "des" -> "de" (blacklist)
  - "vous" -> "vos" (blacklist)
  - "," -> "" (ponctuation seule)

=== TOTAL : 5 propositions, 5 faux positifs filtres ===
```

### 8. Afficher chaque proposition avec contexte

Pour chaque proposition, afficher :
- Le mot incorrect et le mot correct
- Le ratio de similarite
- Le contexte (5 mots avant et apres dans la transcription brute)
- Le pass de classification
- Demander validation : `[A]ccepter / [R]ejeter / [M]odifier`

### 9. Sauvegarder avec backup automatique

**AVANT toute modification** du dictionnaire :

```python
import shutil
from datetime import datetime

dict_path = "data/dictionaries/corrections_v2.1.json"
backup_path = f"{dict_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Backup obligatoire
shutil.copy2(dict_path, backup_path)

# Charger, enrichir, sauvegarder
with open(dict_path, 'r', encoding='utf-8') as f:
    dictionnaire = json.load(f)

for proposition in propositions_acceptees:
    section = proposition['pass']
    dictionnaire[section][proposition['incorrect']] = proposition['correct']

with open(dict_path, 'w', encoding='utf-8') as f:
    json.dump(dictionnaire, f, ensure_ascii=False, indent=2)
```

### 10. Logger les statistiques

Produire un rapport de synthese :

```
=== RAPPORT ENRICHISSEMENT ===
Date            : 2026-01-08
Work Order      : MC3-16722
Dictionnaire    : corrections_v2.1.json
Backup          : corrections_v2.1.json.backup_20260108_143022

Entrees ajoutees :
  Pass 1 (juridiques)    : +3
  Pass 2 (accents)       : +1
  Pass 3 (accords)       : +0
  Pass 4 (mal reconnus)  : +4
  TOTAL                  : +8

Faux positifs filtres    : 5
Taux rejet               : 38%

Dictionnaire avant       : 142 entrees
Dictionnaire apres       : 150 entrees (+5.6%)
```

---

## Contraintes Critiques

### Mode proposition obligatoire
TOUJOURS proposer les entrees pour validation humaine avant de les ajouter au dictionnaire. Jamais d'ajout automatique non supervise -- le risque de faux positifs contextuels est trop eleve (voir Contrainte #7).

### Backup automatique avant modification
Un backup horodate est cree AVANT chaque modification du dictionnaire. Cela permet de revenir en arriere si des faux positifs passent la validation.

### Filtrage faux positifs obligatoire
Les mots courants contextuels (de/des, le/les, est/et, vous/vos) ne doivent JAMAIS etre proposes comme corrections. Le dictionnaire V2.0 contenait 8 faux positifs critiques dont "et" -> "met" qui detruisait le texte (110 occurrences remplacees). Le seuil de similarite est a 85% minimum.

### Scoring contre-intuitif
Le score de qualite (Pass 6) mesure la qualite du texte ORIGINAL, pas du texte corrige. Plus on trouve d'erreurs et plus on corrige, plus le score DIMINUE. Un score de 60/100 signifie "beaucoup d'erreurs trouvees et corrigees" (positif), pas "texte final de mauvaise qualite" (voir Contrainte #6).

---

## Specificites par Type

### SPR
- Vocabulaire concentre sur les MOTIFS de decision (credibilite, risque prospectif, protection de l'Etat)
- Erreurs typiques : termes juridiques SPR (article 96, 97(1), LIPR)
- 1 seul locuteur (Commissaire) -- moins de confusion de mots

### SAR
- Vocabulaire d'appel (motifs d'appel, decision attaquee, erreur de droit)
- Erreurs typiques : termes specifiques SAR (article 110, 111)
- Multi-locuteurs -- plus d'erreurs de reconnaissance vocale

### SI / SAI
- Vocabulaire d'immigration (mesure de renvoi, controle des motifs, danger pour le public)
- Numeros de dossier differents (0018-Cx pour SI, MC0 pour SAI)
- Terminologie distincte a enrichir separement

---

## References

- @docs/CONTRAINTES.md -- Contraintes #6 (Scoring contre-intuitif), #7 (Faux positifs V2.1)
- @docs/CONVENTIONS_TRANSCRIPTION.md -- Conventions de correction par pass
- @docs/CHANGELOG.md -- Historique des enrichissements dictionnaire

---

## Sorties (Outputs)

| Sortie | Format | Description |
|--------|--------|-------------|
| Dictionnaire enrichi | JSON | `data/dictionaries/corrections_v2.1.json` mis a jour |
| Backup | JSON | `corrections_v2.1.json.backup_YYYYMMDD_HHMMSS` |
| Rapport enrichissement | Texte console | Statistiques : entrees par pass, faux positifs filtres, evolution taille |
| Liste propositions | Texte console | Detail de chaque proposition avec contexte pour validation |
