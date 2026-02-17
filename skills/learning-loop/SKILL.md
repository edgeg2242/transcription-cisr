# Skill : Boucle d'Apprentissage Continu (Learning Loop)

## Description

Meta-skill d'amelioration systematique et continue du pipeline de transcription CISR. Apres chaque lot (batch) de Work Orders traites, ce skill orchestre un cycle complet d'analyse, detection d'erreurs residuelles, priorisation, proposition de corrections, et validation des ameliorations.

Ce skill est le **moteur d'amelioration** du systeme : il coordonne les autres skills (notamment `/enrichissement-dictionnaire` et `/validation-qualite`) et s'assure que chaque Work Order traite rend le pipeline plus fiable pour les suivants.

Principe fondamental : **ne jamais regresser**. Chaque iteration doit ameliorer ou maintenir la qualite, jamais la degrader.

---

## Declenchement

- Commande explicite `/learning-loop` apres le traitement d'un lot de Work Orders
- Periodiquement pour revue systematique (ex: apres chaque 10 Work Orders)
- Quand un nouveau type de document est rencontre pour la premiere fois (SAR, SI, SAI)
- Apres une mise a jour majeure du pipeline (nouveau workflow, nouvelle API)

---

## Prerequis

- **Resultats des derniers WO traites** :
  - Documents Word finaux (sortie Workflow 2)
  - Rapports QA generes (sortie Pass 6 ou `/validation-qualite`)
  - Logs de corrections appliquees (Pass 1-5)
- **Referentiels gold standard** : Documents de reference humains (si disponibles)
- **Historique des corrections** : `data/dictionaries/corrections_v2.1.json`
- **Documentation existante** : `docs/CHANGELOG.md` pour tracer les ameliorations
- Acces aux fichiers d'implementation du pipeline (`implementation/*.py`)

---

## Actions

### 1. Collecter les resultats des derniers WO traites

Rassembler tous les artefacts produits lors du dernier lot :

```
Pour chaque Work Order traite :
  - Document Word final : Test_Pipeline/Test_Demandes/MC3-xxxxx/transcription_finale.docx
  - Rapport QA : Test_Pipeline/Test_Demandes/MC3-xxxxx/rapport_qa.json
  - Transcription brute : Test_Pipeline/Test_Demandes/MC3-xxxxx/transcription_brute.txt
  - Transcription corrigee : Test_Pipeline/Test_Demandes/MC3-xxxxx/*_PIPELINE_COMPLET.txt
  - Metadata : Test_Pipeline/Test_Demandes/MC3-xxxxx/metadata_work_order.json
  - Logs corrections : Test_Pipeline/Test_Demandes/MC3-xxxxx/rapport_corrections.txt
```

Dresser l'inventaire complet : nombre de WO, types (SPR/SAR/SI/SAI), dates de traitement.

### 2. Comparer chaque WO avec le gold standard

Pour chaque Work Order possedant un referentiel :

- Si `/validation-qualite` n'a pas deja ete execute, le declencher
- Calculer les metriques cles :
  - **Score similarite textuelle** : ratio `difflib.SequenceMatcher` (cible : >= 95%)
  - **Score formatage Word** : conformite marges, polices, tableaux (cible : >= 98%)
  - **Score nomenclature** : conformite noms fichiers, structure dossiers
  - **Score QA global** : moyenne ponderee des 3 scores

Pour les WO sans referentiel : evaluer uniquement les criteres automatisables du QA Checklist (14/20 criteres).

### 3. Identifier et categoriser les erreurs residuelles par SOURCE

Analyser chaque erreur residuelle et l'attribuer a sa source dans le pipeline :

| Source | Type d'erreurs | Fichier concerne |
|--------|---------------|------------------|
| **AssemblyAI** | Mots mal transcrits, homophonies, termes juridiques deformes | `data/dictionaries/corrections_v2.1.json` |
| **Formatage Word** | Marges incorrectes, police non conforme, tableaux mal structures | `implementation/transcription_post_traitement.py` |
| **Mapping locuteurs** | Locuteur mal identifie, confusion commissaire/demandeur | `implementation/transcription_post_traitement.py` |
| **Extraction MOTIFS (SPR)** | Debut/fin MOTIFS mal detectes, contenu hors MOTIFS inclus | `implementation/extract_motifs_section.py` |
| **Metadonnees** | Nom commissaire incorrect, date erronee, numero dossier mal extrait | `implementation/preparation_work_order.py` |
| **Conversion audio** | Qualite audio degradee, artefacts de conversion .a00 -> WAV | `implementation/audio_converter_api.py` |

```python
def categoriser_erreur(erreur):
    if erreur['type'] in ['mot_mal_transcrit', 'homophonie', 'terme_juridique']:
        return 'dictionnaire'
    elif erreur['type'] in ['marge_incorrecte', 'police_non_conforme', 'tableau_incorrect']:
        return 'formatage_word'
    elif erreur['type'] in ['locuteur_incorrect', 'confusion_locuteur']:
        return 'mapping_locuteurs'
    elif erreur['type'] in ['motifs_incomplets', 'contenu_hors_motifs']:
        return 'extraction_motifs'
    elif erreur['type'] in ['nom_commissaire', 'date_erronee', 'numero_dossier']:
        return 'metadonnees'
    else:
        return 'autre'
```

### 4. Prioriser par frequence x impact

Classer les erreurs selon la formule :

```
priorite = frequence_occurrence x coefficient_impact
```

**Coefficients d'impact** :

| Niveau | Coefficient | Exemples |
|--------|-------------|----------|
| **Critique** | x5 | Sens altere, nom commissaire incorrect, numero dossier errone |
| **Majeur** | x3 | Terme juridique deforme, section MOTIFS mal delimitee |
| **Modere** | x2 | Accent manquant sur nom propre, accord grammatical |
| **Mineur** | x1 | Ponctuation, espacement, casse |

Trier par priorite decroissante. Traiter les erreurs critiques en premier.

### 5. Proposer un rapport d'amelioration avec actions concretes

Generer un rapport structure avec actions specifiques :

```
=== RAPPORT D'AMELIORATION CONTINUE ===
Date             : 2026-01-08
Lot traite       : RCE-9878-AA (6 Work Orders SPR)
Score QA moyen   : 72/100

--- ACTIONS PRIORITAIRES ---

[CRITIQUE] Erreurs dictionnaire (12 occurrences, impact x5 = 60)
  Action : Declencher /enrichissement-dictionnaire
  Nouvelles entrees proposees : 8
  Fichier : data/dictionaries/corrections_v2.1.json

[MAJEUR] Extraction MOTIFS incomplete (3 occurrences, impact x3 = 9)
  Action : Ajouter 2 nouveaux patterns regex debut MOTIFS
  Patterns proposes :
    - r"Les motifs de ma decision sont les suivants"
    - r"Voici donc les raisons de ma decision"
  Fichier : implementation/extract_motifs_section.py

[MODERE] Accents manquants noms propres (7 occurrences, impact x2 = 14)
  Action : Enrichir Pass 2 dictionnaire
  Fichier : data/dictionaries/corrections_v2.1.json

[MINEUR] Espacement double apres points (15 occurrences, impact x1 = 15)
  Action : Ajouter regle nettoyage dans post-traitement
  Fichier : implementation/transcription_post_traitement.py

--- METRIQUES ---
Erreurs critiques : 12
Erreurs majeures  : 3
Erreurs moderees  : 7
Erreurs mineures  : 15
TOTAL             : 37

--- NOUVEAUX CAS DE TEST SUGGERES ---
  1. Test extraction MOTIFS avec pattern "Les motifs de ma decision..."
  2. Test correction "FESPOLA" -> "Hezbollah" dans contexte libanais
```

### 6. Appliquer les corrections apres validation humaine

Apres approbation du rapport par l'utilisateur :

- **Erreurs dictionnaire** : Declencher `/enrichissement-dictionnaire` avec les propositions
- **Erreurs de code** : Modifier directement les fichiers d'implementation concernes
- **Nouveaux patterns** : Ajouter les regex proposes dans les fichiers de configuration
- **Nouveaux seuils** : Ajuster les seuils de similarite, scoring, filtrage

**REGLE** : Chaque modification doit etre tracable -- noter le Work Order source, la date, et la justification.

### 7. Valider par re-execution des cas de test

Apres application des corrections :

- Re-executer le pipeline sur les WO du lot concerne
- Comparer les metriques AVANT et APRES :

```
=== VALIDATION AMELIORATIONS ===

Work Order MC3-16722 :
  Score QA avant  : 67/100
  Score QA apres  : 85/100  (+18 points)
  Regression      : AUCUNE

Work Order MC3-03924 :
  Score QA avant  : 60/100
  Score QA apres  : 78/100  (+18 points)
  Regression      : AUCUNE

=== BILAN ===
Amelioration moyenne : +18 points
Regressions          : 0/6 Work Orders
Statut               : VALIDATION REUSSIE
```

Si regression detectee sur un WO :
- ANNULER la modification concernee
- Analyser la cause de la regression
- Proposer une correction alternative qui ne casse pas les cas existants

### 8. Documenter les ameliorations dans le CHANGELOG

Ajouter une entree dans `docs/CHANGELOG.md` :

```markdown
## [2026-01-08] Enrichissement post-RCE-9878-AA

### Dictionnaire
- Ajout 8 entrees Pass 1 (termes juridiques LIPR)
- Ajout 4 entrees Pass 4 (mots mal reconnus AssemblyAI)
- Suppression 2 faux positifs identifies

### Extraction MOTIFS
- Ajout 2 patterns regex debut MOTIFS (couverture +12%)

### Metriques
- Score QA moyen : 72/100 -> 82/100 (+10 points)
- Dictionnaire : 142 -> 154 entrees (+8.5%)
- Couverture patterns MOTIFS : 8 -> 10 patterns
```

Mettre a jour les instructions du framework "ii" si necessaire :
- Nouvelle `CONTRAINTE` si un piege a ete decouvert
- Nouvelle `BONNE PRATIQUE` si une amelioration significative est confirmee

---

## Boucle de Retroaction

```
Traiter WO ──> Comparer vs referentiel ──> Detecter erreurs residuelles
     ^                                              |
     |                                              v
     |                                     Categoriser par source
     |                                              |
     |                                              v
     |                                     Prioriser (frequence x impact)
     |                                              |
     |                                              v
Re-tester <── Appliquer corrections <── Proposer ameliorations
     |
     v
Documenter dans CHANGELOG + Contraintes/Bonnes Pratiques
```

Chaque iteration de cette boucle rend le pipeline plus fiable. L'objectif est d'atteindre et maintenir un score QA moyen >= 95% sur tous les types de documents.

---

## Metriques Suivies

| Metrique | Calcul | Cible |
|----------|--------|-------|
| Score similarite moyen par type | `difflib.SequenceMatcher.ratio()` moyen | >= 95% |
| Erreurs residuelles par pass | Comptage erreurs non corrigees (Pass 1-4) | Tendance decroissante |
| Taux faux positifs dictionnaire | Faux positifs / total propositions | < 10% |
| Evolution score QA | Score moyen par lot de WO | Tendance croissante |
| Couverture referentiels | Types avec gold standard / 4 types | 100% |
| Taille dictionnaire | Nombre total d'entrees | Croissance controlee |
| Taux de regression | WO degrades apres modification / total WO | 0% |

### Suivi temporel

Maintenir un historique des metriques par lot :

```
Lot RCE-9878-AA (6 WO SPR) : Score 72 -> 82 | Dict 142 -> 154
Lot RCE-9439-DD (3 WO SAR) : Score 65 -> 78 | Dict 154 -> 167
Lot RCE-XXXX-XX (2 WO SI)  : Score 58 -> 71 | Dict 167 -> 180
```

---

## Integration avec Autres Skills

| Skill | Interaction | Declenchement |
|-------|------------|---------------|
| `/enrichissement-dictionnaire` | Declenche automatiquement si erreurs dictionnaire detectees a l'etape 3 | Apres categorisation |
| `/validation-qualite` | Utilise pour comparaisons vs referentiels a l'etape 2 | Si pas deja execute |
| `/pipeline-spr` | Met a jour les parametres si ameliorations workflow SPR identifiees | Apres validation etape 7 |
| `/pipeline-sar` | Idem pour workflow SAR | Apres validation etape 7 |
| `/pipeline-si` | Idem pour workflow SI | Apres validation etape 7 |
| `/pipeline-sai` | Idem pour workflow SAI | Apres validation etape 7 |
| `/analyse-work-assignment` | Fournit les metadonnees du lot pour le rapport | Lecture seule |

---

## Specificites par Type

### SPR
- Extraction MOTIFS critique : verifier que les patterns regex couvrent tous les cas rencontres
- 1 locuteur : moins d'erreurs de diarization, focus sur termes juridiques
- Score cible plus eleve (>= 95%) car audio plus propre et plus court

### SAR
- Multi-locuteurs : erreurs de diarization frequentes, enrichir mapping locuteurs
- Audience complete : plus de contenu, plus d'erreurs potentielles
- Vocabulaire d'appel specifique a enrichir separement

### SI
- Pages couvertures generees (pas fournies) : valider la generation vs template
- Numeros de dossier format different (0018-Cx-xxxxx) : verifier le matching
- Terminologie immigration distincte

### SAI
- Format a confirmer (echantillons limites) : chaque nouveau WO SAI est une opportunite d'apprentissage majeure
- Documenter abondamment les specificites decouvertes

---

## References

- @docs/CONTRAINTES.md -- Toutes les contraintes (#1 a #14), en particulier #6 (Scoring), #7 (Faux positifs), #11 (MOTIFS SPR)
- @docs/CONVENTIONS_TRANSCRIPTION.md -- Conventions de correction et de formatage
- @docs/CHANGELOG.md -- Historique des ameliorations a maintenir
- @docs/ARCHITECTURE.md -- Architecture pipeline 4 workflows

---

## Sorties (Outputs)

| Sortie | Format | Description |
|--------|--------|-------------|
| Rapport d'amelioration | Texte console | Actions prioritaires, metriques, cas de test suggeres |
| Rapport de validation | Texte console | Comparaison avant/apres, detection regressions |
| `docs/CHANGELOG.md` | Markdown | Entree datee avec ameliorations et metriques |
| Dictionnaire enrichi | JSON | Via `/enrichissement-dictionnaire` si declenche |
| Fichiers implementation modifies | Python | Si corrections de code appliquees |
| Nouvelles contraintes/bonnes pratiques | Markdown | Mises a jour `CLAUDE.md` si decouvertes significatives |
