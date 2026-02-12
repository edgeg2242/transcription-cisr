# INSTRUCTION PRIORITAIRE : LANGUE

**TOUJOURS communiquer en français** dans ce projet. Toutes les réponses, explications, et communications doivent être en français, sauf pour :
- Le code source (les commentaires peuvent être en français)
- Les noms de variables/fonctions (convention anglaise acceptée)
- Les messages d'erreur système (si générés par des bibliothèques tierces)

---

## ⚠️ CONTRAINTE #12: Types de Documents CISR - Structures et Formats DIFFÉRENTS

**Règle Identifiée** : 2026-01-07 13:00

Les 4 types de documents CISR (SPR, SAR, SI, SAI) ont des **structures, formats et contenus FONDAMENTALEMENT DIFFÉRENTS**. Il est CRITIQUE de ne PAS appliquer les mêmes règles de formatage à tous les types.

**Source de vérité** : Les documents manuels de référence pour CHAQUE type sont l'autorité finale sur le format correct.

### DIFFÉRENCES CRITIQUES SPR vs SAR

| Caractéristique | SPR | SAR |
|-----------------|-----|-----|
| **Contenu audio** | MOTIFS oraux (post-audience) | AUDIENCE COMPLÈTE |
| **Durée audio** | 10-30 min | 60-180 min |
| **Locuteurs** | 1 (Commissaire) | 4-6 (Multi-parties) |
| **Marges L/R** | **0.50"** | **1.00"** (DOUBLE) |
| **Marges Bas** | 0.63" | 0.69" |
| **Tableau 1** | 17L × 3C (métadonnées) | **1L × 2C** (numéros dossiers) |
| **Tableau 2** | 1L × 1C (vide) | **15L × 3C** (métadonnées) |
| **"Date décision"** | ✅ OUI | ❌ NON |
| **Titre** | "TRANSCRIPTION DES Motifs..." | "Transcription complète..." |

### RÈGLES IMPÉRATIVES

1. **TOUJOURS vérifier le type** (SPR/SAR/SI/SAI) AVANT d'appliquer TOUT formatage
2. **NE JAMAIS supposer** que SPR et SAR ont le même format
3. **Utiliser documents manuels de référence** comme source de vérité pour CHAQUE type
4. **Créer fonctions séparées** si nécessaire (`generer_document_spr()` vs `generer_document_sar()`)
5. **Valider** que le type détecté correspond au format appliqué

### BLOQUEURS PRODUCTION SAR

**À implémenter AVANT le premier Work Order SAR** :

- [ ] Marges SAR (1.00" L/R au lieu de 0.50")
- [ ] Fonction `generer_tableaux_metadata_sar()` (structure inversée)
- [ ] Titre principal SAR ("Transcription complète..." au lieu de "MOTIFS...")
- [ ] Validation métadonnées SAR (absence "Date décision" = OK)
- [ ] Mapping locuteurs SAR (4-6 locuteurs au lieu de 1)

**Documentation complète** : [`Documentation/SYNTHESE_RAPIDE_DIFFERENCES_TYPES_CISR.md`](Documentation/SYNTHESE_RAPIDE_DIFFERENCES_TYPES_CISR.md)

---

## ⚠️ CONTRAINTE #11: Documents SPR - Seuls les MOTIFS dans la Transcription Finale

**Règle Identifiée** : 2026-01-07 12:30

Les documents de transcription finale pour les cas **SPR (Section de la Protection des Réfugiés)** doivent contenir **SEULEMENT la section MOTIFS** de la décision du commissaire, PAS l'audience complète.

**Distinction critique** :
- ❌ **Audience complète** (1h30-2h) : Interrogatoire + témoignage demandeur + plaidoyers avocat + décision orale
- ✅ **Document transcription SPR** : SEULEMENT les MOTIFS de la décision (15-30 min)

**Structure audience complète SPR typique** :
```
1. Formalités ouverture (5 min)
   - Présentation commissaire, avocat, interprète
   - Vérification documents au dossier
   - Serment du demandeur

2. Interrogatoire commissaire (45-90 min)
   - Questions sur identité, parcours, pays d'origine
   - Questions sur craintes si retour au pays
   - Questions sur possibilité refuge intérieur

3. Plaidoyers avocat (15-30 min)
   - Résumé des faits
   - Arguments juridiques
   - Références au cartable national documentation

4. MOTIFS de la décision (15-30 min) ← SEULEMENT CETTE PARTIE
   - Analyse identité et crédibilité
   - Analyse risque prospectif
   - Analyse protection de l'État
   - Analyse possibilité refuge intérieur
   - Décision finale (acceptée/refusée)
```

**Impact sur les workflows** :

**Workflow 1 (Transcription)** :
- AssemblyAI transcrit l'audience COMPLÈTE (normal)
- Fichier `transcription_brute.txt` contient tout l'audio (1h30-2h)

**Workflow 2 (Post-Traitement)** :
- **CRITIQUE** : Doit extraire SEULEMENT la section MOTIFS
- Utiliser patterns regex pour détecter début MOTIFS :
  - "Donc, j'ai eu aujourd'hui à examiner..."
  - "Voici les motifs de ma décision..."
  - "Ma décision aujourd'hui, c'est que..."
- Ignorer tout ce qui précède (interrogatoire + plaidoyers)

**Workflow 3 (Comparaison Qualité)** :
- Comparer MOTIFS extraits vs document manuel référence
- Document manuel contient aussi seulement MOTIFS (pas audience complète)

**Patterns d'extraction MOTIFS** :
```python
# Début section MOTIFS (8 patterns existants)
debut_patterns = [
    r"Donc,?\s*j'ai eu aujourd'hui à examiner",
    r"Voici les? motifs? de (ma|la) décision",
    r"Ma décision aujourd'hui,?\s*c'est que",
    r"Je vais (maintenant|directement) vous donner (ma|les) décision",
    # ... (voir extract_motifs_section.py)
]

# Fin section MOTIFS
fin_patterns = [
    r"Merci pour votre témoignage",
    r"L'audience est (terminée|levée|ajournée)",
    r"Je vous remercie pour votre travail"
]
```

**Exemple concret (MC3-03924 Victoria)** :
```
Transcription brute complète : 8,274 mots (111 min)
  - Formalités : ~500 mots
  - Interrogatoire : ~4,000 mots
  - Plaidoyers avocat : ~1,700 mots
  - MOTIFS commissaire : ~2,086 mots ← SEULEMENT CETTE PARTIE

Document transcription finale : 2,086 mots (MOTIFS seulement)
```

**Prévention** :
- Ne JAMAIS comparer audience complète vs document manuel MOTIFS
- Toujours extraire section MOTIFS AVANT comparaison qualité
- Vérifier que document généré contient seulement MOTIFS (pas interrogatoire)
- Logger nombre de mots extrait pour validation (~1,500-3,000 mots typique pour MOTIFS)

**Cas particuliers** :
- **SAR (Section d'Appel)** : Peut contenir décision + motifs d'appel (différent de SPR)
- **Audiences très courtes** (<30 min) : Peuvent être MOTIFS purs sans interrogatoire
- **Décisions écrites** : Reçues en Word, déjà formatées (pas besoin extraction)

**Code** : Voir `extract_motifs_section.py` et `compare_batch_quality_motifs.py`

**Bénéfice** : Comparaisons qualité justes et précises (comparer pommes avec pommes)

---

## ⚠️ CONTRAINTE #14: Nomenclature - Work Assignment vs Work Order

**Règle Identifiée** : 2026-01-08

### TERMINOLOGIE OFFICIELLE

**Distinction critique** :
- **Work Assignment** : Fichier ZIP initial fourni par le client contenant PLUSIEURS work orders
- **Work Order** : Dossier individuel pour UNE transcription (MC3-xxxxx, MC5-xxxxx)

**Structure typique d'un Work Assignment** :
```
RCE-9878-AA.zip (Work Assignment)
├── Work Order RCE-9878-AA.xlsx (UNIQUE pour TOUS les dossiers)
├── MC3-03924/ (Work Order 1)
├── MC3-16722/ (Work Order 2)
├── MC3-43157/ (Work Order 3)
├── MC3-56703/ (Work Order 4)
├── MC3-58211/ (Work Order 5)
└── MC3-66060/ (Work Order 6)
```

### RÈGLES CRITIQUES

1. **UN Work Assignment peut contenir PLUSIEURS Work Orders** (typiquement 4-10)
2. **NE PAS supposer** 1 ZIP = 1 Work Order (erreur courante)
3. **Détecter automatiquement** le nombre de Work Orders via Excel (lignes après ligne 14)
4. **Traiter CHAQUE Work Order** séparément (boucle sur tous les dossiers détectés)

### IMPACT WORKFLOW 0

**Détection automatique** :
```python
# Lire Excel COMPLET (toutes lignes après en-têtes)
work_orders_data = lire_excel_tous_work_orders(excel_path)

# Boucler sur CHAQUE Work Order détecté
for wo_data in work_orders_data:
    numero_dossier = wo_data['numero_dossier']  # Ex: MC3-16722

    # Localiser fichiers associés
    page_couverture = trouver_page_couverture(numero_dossier)
    audio_file = localiser_fichier_audio(numero_dossier)

    # Extraire métadonnées et générer JSON
    metadata = extraire_metadonnees(page_couverture)
    generer_metadata_json(numero_dossier, metadata)
```

**Génération outputs** :
- 1 fichier `metadata_work_order.json` PAR Work Order
- Structure : `Test_Pipeline/Test_Demandes/MC3-xxxxx/metadata_work_order.json`

### RÈGLES PAGES COUVERTURES PAR TYPE

**SPR / SAR / SAI** :
- ✅ Page couverture `.docx` FOURNIE avec métadonnées pré-remplies
- ✅ Système EXTRAIT métadonnées depuis `.docx` existant
- **Fichier typique** : `MC3-16722 SPR.61.01 - Page couverture.docx`

**SI (Section de l'Immigration)** :
- ❌ Page couverture `.docx` NON fournie (ou fournie VIDE sans métadonnées)
- ✅ Système doit GÉNÉRER page couverture depuis template
- **Template** : `Documentation/Templates/(SI) Cover Page Template.docx`
- **Sources métadonnées** : Excel Work Order + nom fichiers + transcription audio

### RÈGLES CONTENU TRANSCRIPTION PAR TYPE

**SPR (Section Protection des Réfugiés)** :
- ✅ Transcrire SEULEMENT la section **MOTIFS** (10-30 min audio)
- ❌ NE PAS transcrire l'audience complète (90-120 min)
- **Détection** : Patterns regex début MOTIFS (voir Contrainte #11)

**SAR / SAI / SI** :
- ✅ Transcrire l'audio **AU COMPLET** (60-180 min)
- ✅ Diarization CRITIQUE (identifier 4-6 locuteurs)

### DOCUMENTATION COMPLÈTE

- `Documentation/SOP_MASTER_DOCUMENT_TYPES.md` : Caractéristiques SPR/SAR/SI/SAI
- `Documentation/SOP_PAGES_COUVERTURES.md` : Traitement pages couvertures par type
- `instruction/preparation_work_order.md` : Workflow 0 détaillé
- `implementation/preparation_work_order.py` : Fonction `detecter_work_orders_multiples()`

**Code** : `implementation/preparation_work_order.py` lignes 293-593, 1274-1413

**Prévention** :
- Toujours logger nombre de Work Orders détectés dans ZIP
- Vérifier que nombre pages couvertures = nombre sous-dossiers
- Ne jamais supposer qu'un ZIP contient 1 seul Work Order

---

## ⚠️ CONTRAINTE #5: Workflow 0 - Matching Fichiers Audio Strict

**Problème Identifié** : 2026-01-07 06:15

Le matching des fichiers audio par "4 derniers chiffres" avec `if dernier_4_chiffres in os.path.basename(audio)` était **trop permissif** et causait des erreurs critiques.

**Cas d'erreur rencontré** :
```
Dossier Victoria-SPR-03924 (derniers 4 chiffres: "3924")
Fichiers présents:
- 3157.a00 (38M) ❌ Audio de Diana (MC3-43157)
- 3924.a00 (26M) ✅ Audio correct pour Victoria

Pattern bugué: if "3924" in "3157.a00"  → False
Pattern bugué: if "3924" in "3924.a00"  → True

MAIS si aucun match trouvé, code retournait audio_files[0] → "3157.a00" (ordre alphabétique)
```

**Résultat** : MC3-03924 transcrit avec audio MC3-43157 (Diana au lieu de Victoria)

**Solution appliquée** :
- Matching STRICT avec `basename.startswith(dernier_4_chiffres + '.')` au lieu de `in`
- Si aucun match exact : **ERREUR CRITIQUE** (FileNotFoundError) au lieu de fallback silencieux
- Logging détaillé des fichiers trouvés vs attendus

**Code** : `implementation/preparation_work_order.py` lignes 327-364

```python
# AVANT (bugué - fallback dangereux)
for audio in audio_files:
    if dernier_4_chiffres in os.path.basename(audio):
        return audio

# Si aucun match, retourner premier trouvé (DANGEREUX)
logger.warning(f"Nom audio ne correspond pas")
return audio_files[0]  # ❌ BUG: ordre alphabétique

# APRÈS (strict - erreur explicite)
fichiers_correspondants = []
for audio in audio_files:
    basename = os.path.basename(audio)
    if basename.startswith(dernier_4_chiffres + '.') or basename.startswith(dernier_4_chiffres + '_'):
        fichiers_correspondants.append(audio)

if fichiers_correspondants:
    return fichiers_correspondants[0]

# Si aucun match exact, ERREUR CRITIQUE (pas de fallback silencieux)
raise FileNotFoundError(
    f"Aucun fichier audio correspondant à {numero_dossier} (attendu: {dernier_4_chiffres}.a00). "
    f"Fichiers présents: {[os.path.basename(f) for f in audio_files]}"
)
```

**Prévention** :
- Toujours utiliser matching strict (`startswith()`) pour identifiants critiques
- Jamais de fallback silencieux sur opérations critiques (fichier audio, métadonnées)
- Logging détaillé AVANT erreur pour diagnostic rapide
- Tester avec dossiers contenant fichiers multiples similaires

**Tests requis** :
- Dossier avec 2+ fichiers audio dont noms se chevauchent (ex: "3157.a00" + "3924.a00")
- Dossier sans fichier audio correspondant (doit échouer avec erreur explicite)
- Dossier avec fichier correct (doit réussir normalement)

**Impact** : BUG CRITIQUE invalidant 1/6 Work Orders dans batch RCE-9878-AA

---

# Le Framework "ii" - Guide pour Assistants IA

Ce projet utilise le **framework Information/Implémentation (ii)** pour construire des systèmes d'automatisation agentiques.

## Principes Fondamentaux

### 1. Architecture à Deux Fichiers
Chaque workflow possède exactement DEUX fichiers :
- **`instruction/[workflow].md`** - Le "quoi" et le "pourquoi"
  - Documentation API et points de terminaison
  - Logique du workflow étape par étape
  - Contraintes et exigences métier
  - Apprentissages historiques (échecs et réussites)
  - Entrées et sorties attendues

- **`implementation/[workflow].py`** - Le "comment"
  - Script Python exécutable
  - Gestion complète des erreurs
  - Opérations de base de données
  - Notifications et journalisation
  - Arguments CLI pour la flexibilité

### 2. La Boucle de Recuit (Annealing Loop)

```
LIRE instruction → CODER implémentation → EXÉCUTER → RECUIRE
```

**En cas d'Échec :**
1. Corriger le code dans `implementation/[workflow].py`
2. METTRE À JOUR `instruction/[workflow].md` avec :
   ```markdown
   ⚠️ CONTRAINTE : [Ce qui a échoué et pourquoi]
   - Cause racine : [raison technique]
   - Solution appliquée : [description de la correction]
   - Prévention : [comment éviter cela]
   ```

**En cas de Réussite :**
1. METTRE À JOUR `instruction/[workflow].md` avec :
   ```markdown
   ✅ BONNE PRATIQUE : [Ce qui a fonctionné]
   - Contexte : [quand cela s'applique]
   - Implémentation : [comment c'était fait]
   - Bénéfices : [pourquoi c'est optimal]
   ```

### 3. Ne Jamais Régresser

**RÈGLE CRITIQUE :** Avant d'écrire TOUT code, TOUJOURS :
1. Lire le fichier `instruction/[workflow].md` complet
2. Vérifier toutes les entrées `⚠️ CONTRAINTE`
3. Examiner toutes les entrées `✅ BONNE PRATIQUE`
4. S'assurer que votre implémentation respecte les apprentissages passés

## Workflow pour Assistants IA

Lorsqu'on vous demande de travailler sur un workflow :

### Phase 1 : Instruction (Couche d'Information)
1. Lire le `instruction/[workflow].md` existant s'il existe
2. Si création d'un nouveau workflow :
   - Définir l'objectif et la portée clairement
   - Documenter tous les points de terminaison API avec exemples
   - Lister la logique du workflow étape par étape
   - Spécifier les entrées, sorties et schémas de données
   - Inclure les exigences d'authentification
   - Ajouter le schéma de base de données si nécessaire

### Phase 2 : Implémentation (Couche d'Exécution)
1. Lire le fichier d'instruction EN PREMIER
2. Créer/mettre à jour `implementation/[workflow].py` avec :
   - Importer toutes les dépendances requises
   - Charger les variables d'environnement
   - Implémenter chaque étape depuis l'instruction
   - Ajouter une gestion complète des erreurs
   - Inclure la journalisation aux points clés
   - Ajouter l'analyse des arguments CLI
   - Implémenter les opérations de base de données
   - Ajouter les notifications de succès/échec

### Phase 3 : Exécution
1. Tester l'implémentation de bout en bout
2. Vérifier tous les chemins d'erreur
3. Vérifier les opérations de base de données
4. Valider les notifications

### Phase 4 : Recuit
1. Documenter ce qui a fonctionné (✅ BONNE PRATIQUE)
2. Documenter ce qui a échoué (⚠️ CONTRAINTE)
3. Mettre à jour le fichier d'instruction avec les apprentissages
4. Ne jamais supprimer les apprentissages historiques - seulement ajouter

## Bonnes Pratiques

1. **Commencer par l'Instruction** - Ne jamais coder avant de documenter
2. **Lire Avant d'Écrire** - Toujours vérifier le fichier d'instruction pour les contraintes
3. **Recuire Après Chaque Exécution** - Documenter les apprentissages immédiatement
4. **Conserver l'Historique** - Ne jamais supprimer les contraintes/pratiques passées
5. **Responsabilité Unique** - Un workflow = un objectif
6. **Échouer Bruyamment** - Mieux vaut crasher que échouer silencieusement
7. **Tout Journaliser** - Le futur vous en débogage vous remerciera

## À Retenir

Ce framework construit une **connaissance institutionnelle au fil du temps**. Chaque contrainte et bonne pratique rend le système plus intelligent et plus fiable.

---

# Contraintes Techniques Spécifiques au Projet

## ⚠️ Python 3.14 + AssemblyAI SDK Incompatibilité

**Problème Identifié** : 2025-12-30

Le SDK AssemblyAI (version 0.17.0) est **incompatible avec Python 3.14** en raison d'une dépendance à Pydantic v1.

**Erreur rencontrée** :
```
AttributeError: 'Settings' object has no attribute 'api_key'
```

**Solution de contournement** :
- Utiliser l'API REST AssemblyAI directement via `requests`
- Ne PAS utiliser le SDK `assemblyai` pour l'instant
- Voir script : `test_transcription_simple.py` pour implémentation de référence

**Endpoints API REST** :
```python
# Upload audio
POST https://api.assemblyai.com/v2/upload
Headers: {'authorization': API_KEY}
Body: binary audio data

# Request transcription
POST https://api.assemblyai.com/v2/transcript
Headers: {'authorization': API_KEY, 'content-type': 'application/json'}
Body: {'audio_url': upload_url, 'language_code': 'fr', 'speaker_labels': True, ...}

# Poll for completion
GET https://api.assemblyai.com/v2/transcript/{transcript_id}
Headers: {'authorization': API_KEY}
```

**Alternative future** : Downgrader Python vers 3.11 ou attendre mise à jour SDK vers Pydantic v2.

---

## ⚠️ CONTRAINTE #10: Conversion Audio - API Cloud (Serveur Distant)

**Problème Identifié** : 2026-01-07

Le projet sera déployé sur un **serveur distant** à l'avenir. Utiliser FFmpeg local/portable n'est **pas viable** pour une architecture serveur.

**Erreur initiale** :
- FFmpeg portable installé localement (~101 MB)
- Nécessite installation manuelle sur chaque serveur
- Problèmes de permissions et PATH sur serveurs Linux

**Solution appliquée** :
- Utiliser **CloudConvert API** pour conversion audio
- API cloud compatible avec déploiement serveur
- Pas de dépendances binaires locales

**Implémentation** :
- Fichier : `implementation/audio_converter_api.py`
- Classe : `AudioConverterAPI`
- API : https://cloudconvert.com/api/v2
- Plan gratuit : 25 conversions/jour

**Configuration** :
```python
# .env
CLOUDCONVERT_API_KEY=your_key_here
```

**Usage** :
```python
from implementation.audio_converter_api import AudioConverterAPI

converter = AudioConverterAPI()
wav_file = converter.convert_audio(
    'fichier.a00',
    output_format='wav',
    sample_rate=16000,
    channels=1
)
```

**Bénéfices** :
- Compatible serveur distant (aucune dépendance binaire)
- Conversion cloud (pas de CPU serveur utilisé)
- Scalable (API gère la charge)
- Multi-format (a00, mp3, flac, etc. → wav)

**Coût** :
- Plan gratuit : 25 conversions/jour
- Plan payant : À partir de $9/mois pour 500 conversions

**Fichier** : `implementation/audio_converter_api.py` (créé 2026-01-07)

---

## ⚠️ Détection Type SPR vs SAR (Ambiguïté "RAD")

**Problème Identifié** : 2026-01-02

La détection automatique du type de transcription (SPR vs SAR) peut échouer si le pattern de détection est trop générique.

**Erreur rencontrée** :
```
Fichier SPR "Demo/demo SPR (Section de la Protection des Réfugiés) - RPD (Refugies Protection Division)/..."
détecté comme SAR car le chemin contient "RAD" dans "Refugies Protection Division"
```

**Cause racine** :
- L'acronyme "RAD" (Refugee Appeal Division) pour SAR se trouve aussi dans "Refugies Protection Division" (RPD)
- Ordre de détection incorrect : vérifier SAR avant SPR cause faux positifs

**Solution appliquée** :
```python
# AVANT (incorrect)
if "SAR" in fullpath or "RAD" in fullpath:
    return TypeTranscription.SAR
elif "SPR" in fullpath or "RPD" in fullpath:
    return TypeTranscription.SPR

# APRÈS (correct)
# Priorité 1: SPR/RPD (doit être vérifié AVANT SAR/RAD)
if "SPR" in fullpath or "RPD FILE" in fullpath or "BENCH" in fullpath:
    return TypeTranscription.SPR
# Priorité 2: SAR/RAD avec exclusion "PROTECTION"
elif "SAR" in fullpath or ("RAD" in fullpath and "PROTECTION" not in fullpath.upper()):
    return TypeTranscription.SAR
```

**Prévention** :
- Toujours vérifier SPR en priorité (cas le plus fréquent et le moins ambigu)
- Ajouter des exclusions pour patterns ambigus ("RAD" sans "PROTECTION")
- Utiliser patterns plus spécifiques ("RPD FILE" au lieu de juste "RPD")

---

## ⚠️ Encodage UTF-8 Windows

**Problème Identifié** : 2025-12-30

La console Windows utilise par défaut l'encodage CP1252, causant des erreurs avec les emojis et caractères spéciaux.

**Erreur rencontrée** :
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f3a4' in position X
```

**Solution** :
```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

Ajouter ce code au début de **tous** les scripts Python qui affichent du texte dans la console.

---

## ✅ Format Audio .a00 (Dictaphone)

**Découverte** : 2025-12-30

Les fichiers `.a00` reçus sont au format propriétaire **dictaphone v4.01**, qui est en réalité du **MP2 audio**.

**Identification** :
```bash
xxd -l 256 fichier.a00
# Révèle headers "dic" et "v4.01"
```

**Conversion requise** :
```bash
ffmpeg -i fichier.a00 -ar 16000 -ac 1 fichier.wav
```

**Performance** : Conversion très rapide (~0.2 secondes pour 10 minutes audio)

**Intégration** : FFmpeg doit être disponible dans le workflow de réception (workflow 1).

---

## ⚠️ CONTRAINTE #1: Pages Couvertures SAR - Structure Simplifiée

**Problème Identifié** : 2026-01-01

Les pages couvertures SAR ont une structure **complètement différente** de SPR :
- **SPR**: Tableau détaillé 9 lignes × 3 colonnes avec toutes les métadonnées (demandeur, commissaire, dates, etc.)
- **SAR**: Tableau minimal 1 ligne × 2 colonnes avec SEULEMENT numéros de dossiers (MC5-xxxxx, MC2/3-xxxxx) et IUC

**Erreur rencontrée** :
```
WARNING: Tableau trop court dans MC5-34977 Page couverture.docx
```

**Solution** :
- Extraction simplifiée pour SAR : extraire seulement numéros MC et IUC
- Ne pas s'attendre aux métadonnées complètes (demandeur, commissaire) dans pages couvertures SAR
- Les métadonnées SAR complètes seront dans le document final transcrit

**Code** : Voir `extraire_metadonnees_sar()` dans `implementation/preparation_work_order.py` lignes 259-430

---

## ⚠️ CONTRAINTE #2: Tableaux Word avec Lignes Vides Intercalaires

**Problème Identifié** : 2026-01-01

Les tableaux dans les pages couvertures CISR contiennent des **lignes vides entre chaque ligne de données**.

**Structure réelle** :
```
Ligne 0: Demandeur | Ibrahim HAMMOUD | Claimant
Ligne 1: [VIDE]    | [VIDE]          | [VIDE]
Ligne 2: Date      | 23 octobre 2025 | Date of hearing
Ligne 3: [VIDE]    | [VIDE]          | [VIDE]
...
```

**Erreur rencontrée** :
```
WorkOrderError: Champ obligatoire manquant: date_audience
```

**Solution** :
- Filtrer les lignes vides AVANT d'extraire les données
- Créer liste `lignes_donnees` en excluant lignes où `cells[1].text.strip()` est vide
- Utiliser indices sur `lignes_donnees` au lieu de `table.rows`

**Code** :
```python
lignes_donnees = []
for row in table.rows:
    if row.cells[1].text.strip():  # Ignorer lignes vides
        lignes_donnees.append(row)

# Ensuite utiliser lignes_donnees[0], lignes_donnees[1], etc.
```

---

## ⚠️ CONTRAINTE #3: Détection Type SAR via Chemin Complet

**Problème Identifié** : 2026-01-01

Les fichiers Excel work order SAR ne contiennent pas toujours "SAR" dans le nom du fichier lui-même, mais dans le **nom du dossier parent** extrait du ZIP.

**Exemple** :
```
extracted_temp/RCE-9439-DD - Regdeck - FR - SAR - Full - 10TAT - 10.17h/Work Order RCE-9439-DD.xlsx
                                            ^^^
                                  SAR est dans le nom du dossier parent
```

**Erreur rencontrée** :
```
Type non détecté depuis nom fichier 'WORK ORDER RCE-9439-DD.XLSX', défaut à SPR
```

**Solution** :
- Utiliser `excel_path.upper()` (chemin complet) au lieu de `os.path.basename(excel_path)` pour détecter "SAR"
- Chercher mot-clé dans chemin complet permet de détecter SAR/RAD dans nom dossier parent

**Code** :
```python
fullpath = excel_path.upper()  # Chemin complet, pas juste nom fichier
if "SAR" in fullpath or "RAD" in fullpath:
    return TypeTranscription.SAR
```

---

## ⚠️ CONTRAINTE #4: Numéros SAR/SPR dans Nom Fichier

**Problème Identifié** : 2026-01-01

Les numéros de dossiers SAR (MC5-xxxxx) et SPR (MC2/3-xxxxx) se trouvent souvent dans le **nom du fichier** page couverture, pas dans le contenu du document.

**Exemple** :
```
MC5-34977 Irb 101.41 Page couverture transcription - 20251022T190002790.docx
^^^^^^^^^
Numéro SAR dans nom fichier
```

**Erreur rencontrée** :
```
WARNING: Numéro SAR non trouvé dans MC5-34977 Page couverture.docx, ignoré
```

**Solution** :
- Chercher regex `MC5-\d+` dans `filename + para_0 + para_1` (nom fichier ET contenu)
- Même approche pour numéros SPR (MC2/3-xxxxx)

**Code** :
```python
filename = os.path.basename(docx_file)
para_0 = doc.paragraphs[0].text
match_sar = re.search(r'MC5-\d+', filename + para_0 + para_1)
```

---

## ✅ BONNE PRATIQUE #1: Extraction Dossier Temporaire Racine

**Contexte** : 2026-01-01

Extraire les ZIP work order dans le dossier du projet (racine) plutôt que dans le dossier Demo évite les chemins trop longs sous Windows.

**Problème évité** :
```
Erreur décompression ZIP: [Errno 2] No such file or directory:
"Demo\\demo SAR (Section d'Appel des Réfugiés)\\extracted_temp\\RCE-9439-DD\\MC5-34977 Irb..."
                                                                      ^^^^^ Chemin trop long
```

**Implémentation** :
```python
temp_dir = os.path.join(os.getcwd(), 'extracted_temp')  # Racine projet
# Au lieu de:
# temp_dir = os.path.join(os.path.dirname(zip_path), 'extracted_temp')
```

**Bénéfice** : Chemins plus courts, compatible Windows MAX_PATH (260 caractères)

---

## ✅ BONNE PRATIQUE #2: Formatage Word CISR - Marges Asymétriques

**Contexte** : 2026-01-01

Les documents CISR officiels utilisent des **marges asymétriques** spécifiques, pas les marges standard de 1 pouce.

**Marges CISR** :
- Haut: 1.25 pouces
- Bas: 0.63 pouces
- Gauche: 0.50 pouces
- Droite: 0.50 pouces

**Implémentation** :
```python
section = doc.sections[0]
section.top_margin = Inches(1.25)
section.bottom_margin = Inches(0.63)
section.left_margin = Inches(0.50)
section.right_margin = Inches(0.50)
```

**Bénéfice** : Conformité 98%+ avec documents CISR manuels

---

## ✅ BONNE PRATIQUE #3: Tableaux Métadonnées Bilingues FR/EN

**Contexte** : 2026-01-01

Les documents CISR doivent contenir **2 tableaux de métadonnées bilingues** pour conformité :
- **Tableau 1** : Informations dossier (9 lignes × 3 colonnes) avec labels FR | Valeur | EN
- **Tableau 2** : Séparateur blanc (1 ligne × 1 colonne)

**Implémentation** :
- Charger métadonnées depuis `metadata_work_order.json` généré par workflow 0
- Appeler `doc.add_table(rows=9, cols=3)` et remplir avec données bilingues
- Appliquer Arial 11pt à toutes les cellules

**Emplacement** : Juste AVANT le marqueur "FIN DES MOTIFS"

**Bénéfice** : Document final conforme CISR, prêt pour dépôt sans modification manuelle

---

## ✅ BONNE PRATIQUE #4: Script de Test End-to-End Automatisé

**Contexte** : 2026-01-02

Un script de test E2E automatisé permet de valider rapidement que le pipeline complet fonctionne après modifications.

**Implémentation** :
- Script Python `tests/run_e2e_test.py` qui automatise :
  1. Nettoyage dossiers de test
  2. Workflow 0 : Extraction work order SPR
  3. Création fichier transcription JSON simulé
  4. Chargement métadonnées depuis `metadata_work_order.json`
  5. Workflow 2 : Génération document Word avec tableaux CISR
  6. Validation document final généré

**Avantages** :
- Détection rapide de régressions (bugs réintroduits)
- Validation automatique après chaque changement de code
- Documentation vivante du workflow complet
- Réduction temps de test manuel (120s → 1s)

**Exécution** :
```bash
python tests/run_e2e_test.py
```

**Bénéfice** : Garantit que le pipeline complet SPR fonctionne de bout en bout avant chaque commit

---

## ✅ BONNE PRATIQUE #5: Tableaux CISR avec Lignes Vides Intercalaires

**Contexte** : 2026-01-06

Les tableaux de métadonnées CISR professionnels utilisent des **lignes vides intercalaires** entre chaque ligne de données pour améliorer la lisibilité.

**Problème initial** :
- Document généré : 9 lignes compactes
- Document manuel professionnel : 17 lignes (9 données + 8 vides)
- Écart visuel significatif par rapport aux standards CISR

**Implémentation** :
```python
# Créer tableau avec 17 lignes (au lieu de 9)
table = doc.add_table(rows=17, cols=3)

# Remplir avec pattern: données, vide, données, vide...
row_idx = 0
for i, (fr, value, en) in enumerate(rows_data):
    # Ligne de données
    table.rows[row_idx].cells[0].text = fr
    table.rows[row_idx].cells[1].text = str(value)
    table.rows[row_idx].cells[2].text = en
    row_idx += 1

    # Ligne vide (sauf après dernière ligne)
    if i < len(rows_data) - 1:
        row_idx += 1  # Sauter ligne vide
```

**Résultat** :
- 100% conforme au format professionnel CISR
- Espacement visuel identique aux documents manuels
- Amélioration lisibilité du tableau

**Fichier** : `implementation/transcription_post_traitement.py` lignes 574-612

**Bénéfice** : Documents générés visuellement identiques aux standards professionnels CISR

---

## ⚠️ CONTRAINTE #8: ZIP Multi-Work Orders - Structure Hiérarchique

**Problème Identifié** : 2026-01-06

Les clients peuvent envoyer un **fichier ZIP contenant PLUSIEURS Work Orders** au lieu d'un seul.

**Exemple réel** : `RCE-9878-AA -Regdeck- FR - SPR - Bench -5TAT- 1.41h.zip`

**Structure typique** :
```
extracted_SPR/
├── RCE-9878-AA -Regdeck- FR - SPR - Bench -5TAT- 1.41h/
│   ├── Work Order RCE-9878-AA.xlsx          ← Excel UNIQUE pour TOUS les dossiers
│   │
│   ├── MC3-03924/                           ← Dossier 1
│   │   ├── DAUDIO/2025-12-09/_1046/MC3-03924/3924.a00
│   │   └── [VIQPlayer.exe, etc.]
│   │
│   ├── MC3-16722/                           ← Dossier 2
│   │   ├── DAUDIO/2025-12-09/_1046/MC3-16722/6722.a00
│   │   └── [VIQPlayer.exe, etc.]
│   │
│   ├── MC3-43157/                           ← Dossier 3
│   ├── MC3-56703/                           ← Dossier 4
│   ├── MC3-58211/                           ← Dossier 5
│   └── MC3-66060/                           ← Dossier 6
│   │
│   ├── MC3-03924 SPR.61.01 - Page couverture.docx    ← Page couverture 1
│   ├── MC3-16722 SPR.61.01 - Page couverture.docx    ← Page couverture 2
│   ├── MC3-43157 SPR.61.01 - Page couverture.docx    ← Page couverture 3
│   ├── MC3-56703 SPR.61.01 - Page couverture.docx    ← Page couverture 4
│   ├── MC3-58211 SPR.61.01 - Page couverture.docx    ← Page couverture 5
│   └── MC3-66060 SPR.61.01 - Page couverture.docx    ← Page couverture 6
```

**Caractéristiques** :
1. **UN seul fichier Excel** contenant les informations de TOUS les Work Orders (RCE-9878-AA.xlsx)
2. **Multiple sous-dossiers** nommés par numéro de dossier (MC3-xxxxx)
3. **Fichier audio** dans structure profonde : `DAUDIO/YYYY-MM-DD/_HHMM/MC3-xxxxx/xxxxx.a00`
4. **Pages couvertures** à la racine du ZIP (pas dans sous-dossiers)
5. **Fichiers VIQPlayer** dupliqués dans chaque sous-dossier

**Impact sur Workflow 0** :
- **CRITIQUE** : Ne pas traiter seulement le premier dossier trouvé
- Détecter automatiquement combien de Work Orders sont présents
- Traiter chaque dossier séparément mais extraire metadata Excel UNE SEULE FOIS
- Associer correctement page couverture → audio → metadata Excel

**Solution à implémenter** :
```python
def detecter_work_orders_multiples(extracted_dir):
    """
    Détecter tous les Work Orders dans un ZIP décompressé.

    Returns:
        list[dict]: [
            {
                'numero_dossier': 'MC3-16722',
                'dossier_path': '/path/to/MC3-16722/',
                'page_couverture': '/path/to/MC3-16722 SPR Page couverture.docx',
                'audio_file': '/path/to/6722.a00',
                'excel_work_order': '/path/to/Work Order RCE-9878-AA.xlsx'  # Même pour tous
            },
            ...
        ]
    """
    work_orders = []

    # Trouver Excel work order (1 seul par ZIP)
    excel_files = glob.glob(f"{extracted_dir}/**/Work Order*.xlsx", recursive=True)
    if not excel_files:
        raise ValueError("Aucun fichier Excel Work Order trouvé")
    excel_path = excel_files[0]

    # Détecter sous-dossiers MC3-xxxxx, MC5-xxxxx, etc.
    dossiers_regex = re.compile(r'MC[2-5]-\d{5}')
    for item in os.listdir(extracted_dir):
        if dossiers_regex.match(item) and os.path.isdir(os.path.join(extracted_dir, item)):
            numero = item
            dossier_path = os.path.join(extracted_dir, numero)

            # Trouver page couverture (à la racine, pas dans sous-dossier)
            page_couv = glob.glob(f"{extracted_dir}/{numero}*Page couverture*.docx")[0]

            # Trouver audio dans DAUDIO/...
            audio_files = glob.glob(f"{dossier_path}/**/DAUDIO/**/*.a00", recursive=True)
            audio_path = audio_files[0] if audio_files else None

            work_orders.append({
                'numero_dossier': numero,
                'dossier_path': dossier_path,
                'page_couverture': page_couv,
                'audio_file': audio_path,
                'excel_work_order': excel_path
            })

    return work_orders
```

**Workflow modifié** :
```python
# AVANT (incorrect - traite seulement 1er dossier)
metadata = extraire_metadonnees_work_order(zip_path)

# APRÈS (correct - détecte et traite TOUS les dossiers)
work_orders = detecter_work_orders_multiples(extracted_dir)
for wo in work_orders:
    metadata = extraire_metadonnees_work_order(
        page_couverture=wo['page_couverture'],
        excel_file=wo['excel_work_order'],
        audio_file=wo['audio_file']
    )
    sauvegarder_metadata(wo['numero_dossier'], metadata)
```

**Fichier à modifier** : `implementation/preparation_work_order.py`

**Prévention** :
- Toujours logger combien de Work Orders détectés dans ZIP
- Vérifier que nombre pages couvertures = nombre sous-dossiers
- Générer UN fichier `metadata_work_order.json` PAR dossier (pas global)
- Créer structure de sortie : `Test_Pipeline/Test_Demandes/MC3-xxxxx/metadata_work_order.json`

**Bénéfice** : Pipeline peut traiter lots complets de 5-10 Work Orders automatiquement

---

## ⚠️ CONTRAINTE #9: Fichiers Audio Multi-Work Orders - Structure Pré-Découpée

**Problème Identifié** : 2026-01-06

**DÉCOUVERTE MAJEURE** : Les fichiers audio dans les ZIP multi-Work Orders sont **déjà pré-découpés** par la CISR. Il n'y a **PAS de concaténation requise**.

**Hypothèse initiale (INCORRECTE)** :
- ❌ Une seule audience = plusieurs fichiers audio segmentés (`3924_part1.a00`, `3924_part2.a00`, etc.)
- ❌ Besoin de concaténer avec FFmpeg avant transcription
- ❌ Les Recording Remarks indiquent où découper

**Réalité découverte (CORRECTE)** :
- ✅ Un Work Order multi-dossiers = 6 fichiers audio **complètement séparés**
- ✅ Chaque dossier MC3-xxxxx a **son propre fichier audio unique** déjà découpé
- ✅ Les Recording Remarks ("commence à 1:46") sont **informatives seulement** (la CISR a déjà fait le découpage)

**Structure arborescence audio** :
```
MC3-56703/
└── DAUDIO/
    └── 2025-12-09/              ← Date audience
        └── _0231/               ← Timestamp enregistrement (02h31)
            └── MC3-56703/       ← Numéro dossier (répété)
                └── 6703.a00     ← Fichier audio (4 derniers chiffres)

MC3-43157/
└── DAUDIO/
    └── 2025-12-09/
        └── _0902/               ← Timestamp différent (09h02)
            └── MC3-43157/
                └── 3157.a00     ← Audio distinct
```

**Règle de nommage** :
- Dossier MC3-56703 → Fichier audio `6703.a00` (4 derniers chiffres)
- Dossier MC3-16722 → Fichier audio `6722.a00`

**Exemple réel (RCE-9878-AA)** :
```
Work Order RCE-9878-AA.xlsx (1 fichier Excel pour TOUS)
├── MC3-56703/ → DAUDIO/.../6703.a00  (9 min)
├── MC3-66060/ → DAUDIO/.../6060.a00  (17 min)
├── MC3-16722/ → DAUDIO/.../6722.a00  (11 min)
├── MC3-43157/ → DAUDIO/.../3157.a00  (25 min)
├── MC3-03924/ → DAUDIO/.../3924.a00  (17 min)
└── MC3-58211/ → DAUDIO/.../8211.a00  (6 min)
```

**Impact sur Workflow 1** :
- **SIMPLIFICATION MAJEURE** : Pas de concaténation audio requise
- Conversion directe `.a00 → WAV` pour chaque dossier séparément
- Les Recording Remarks **ne sont pas utilisées** pour découpage FFmpeg (déjà fait par CISR)
- Traitement parallèle possible (6 transcriptions AssemblyAI simultanées)

**Solution de localisation audio** :
```python
def localiser_fichier_audio(dossier_path: str, numero_dossier: str) -> str:
    """
    Localiser fichier .a00 dans arborescence DAUDIO profonde.

    Args:
        dossier_path: Chemin vers dossier MC3-xxxxx/
        numero_dossier: "MC3-56703"

    Returns:
        Chemin absolu vers fichier .a00

    Exemple:
        MC3-56703/ → DAUDIO/2025-12-09/_0231/MC3-56703/6703.a00
    """
    # Recherche récursive
    audio_files = glob.glob(f"{dossier_path}/**/DAUDIO/**/*.a00", recursive=True)

    if not audio_files:
        raise FileNotFoundError(f"Aucun fichier audio trouvé dans {dossier_path}")

    # Vérification cohérence nom fichier
    dernier_4_chiffres = numero_dossier[-4:]  # "56703" → "6703"
    for audio in audio_files:
        if dernier_4_chiffres in os.path.basename(audio):
            return audio

    # Si aucun match par nom, retourner premier trouvé
    return audio_files[0]
```

**Validation cohérence** :
```python
# Vérifier que nombre de dossiers MC3-xxxxx = nombre fichiers .a00
dossiers_mc = [d for d in os.listdir(extracted_dir) if re.match(r'MC[2-5]-\d{5}', d)]
audio_files = glob.glob(f"{extracted_dir}/**/DAUDIO/**/*.a00", recursive=True)

if len(dossiers_mc) != len(audio_files):
    logger.warning(f"INCOHÉRENCE : {len(dossiers_mc)} dossiers vs {len(audio_files)} fichiers audio")
```

**Fichier à modifier** : `implementation/reception_preparation.py`

**Prévention** :
- Ne jamais concaténer fichiers audio dans ZIP multi-Work Orders
- Traiter chaque dossier MC3-xxxxx comme une transcription indépendante
- Utiliser Recording Remarks seulement pour documentation (pas découpage)
- Valider que chaque dossier a exactement 1 fichier .a00

**Documentation complète** : Voir `Documentation/ANALYSE_EXCEL_MULTI_WORK_ORDERS.md`

**Bénéfice** : Simplification majeure du pipeline - pas de manipulation audio complexe requise

## ✅ BONNE PRATIQUE #6: Support Multi-Work Orders via Excel Source-of-Truth

**Contexte** : 2026-01-06

Les fichiers ZIP reçus peuvent contenir **PLUSIEURS Work Orders** (6+) au lieu d'un seul. Le fichier Excel à la racine du ZIP décompressé est la **source de vérité** pour détecter et traiter tous les Work Orders.

**Problème évité** :
- Traiter seulement 1 Work Order alors que le ZIP en contient 6
- Manquer des dossiers car détection basée seulement sur structure physique
- Incohérence entre Excel et fichiers traités

**Implémentation** :

**1. Lire Excel EN PREMIER** (ligne 14+ jusqu'à ligne vide) :
```python
def lire_excel_tous_work_orders(excel_path):
    """Lire toutes les lignes Work Orders depuis Excel."""
    wb = load_workbook(excel_path, data_only=True)
    ws = wb.active

    # Trouver ligne d'en-têtes (chercher "File Number")
    header_row = None
    for row_idx in range(1, 30):
        for col_idx in range(1, 10):
            cell = ws.cell(row=row_idx, column=col_idx).value
            if cell and 'file number' in str(cell).lower():
                header_row = row_idx
                break

    # Lire toutes lignes de données
    work_orders_data = []
    row_idx = header_row + 1
    while row_idx <= ws.max_row:
        file_num = ws.cell(row=row_idx, column=4).value  # Col D
        if not file_num or str(file_num).strip() == "":
            break  # Ligne vide = fin des Work Orders

        work_orders_data.append({
            'numero_dossier': str(file_num).strip(),
            'date_audience': ws.cell(row=row_idx, column=6).value,
            'duree_audio': ws.cell(row=row_idx, column=13).value,
            'recording_remarks': ws.cell(row=row_idx, column=22).value,
            'ligne_excel': row_idx
        })
        row_idx += 1

    return work_orders_data
```

**2. Localiser fichiers audio dans structure profonde DAUDIO** :
```python
def localiser_fichier_audio(dossier_path, numero_dossier):
    """Localiser fichier .a00 dans arborescence DAUDIO profonde."""
    # Structure: MC3-56703/DAUDIO/2025-12-09/_0231/MC3-56703/6703.a00

    audio_files = glob.glob(f"{dossier_path}/**/DAUDIO/**/*.a00", recursive=True)

    if not audio_files:
        raise FileNotFoundError(f"Aucun fichier audio dans {dossier_path}")

    # Validation nom: MC3-56703 → 6703.a00 (4 derniers chiffres)
    dernier_4_chiffres = numero_dossier[-4:]
    for audio in audio_files:
        if dernier_4_chiffres in os.path.basename(audio):
            return audio

    return audio_files[0]  # Fallback
```

**3. Orchestrer détection complète** :
```python
def detecter_work_orders_multiples(extracted_dir, excel_path):
    """Détecter tous les Work Orders via Excel + validation physique."""

    # Étape 1: Lire Excel (source de vérité)
    work_orders_excel = lire_excel_tous_work_orders(excel_path)

    # Étape 2: Scanner structure physique
    dossiers_physiques = []
    for item in os.listdir(extracted_dir):
        if re.match(r'MC[2-5]-\d+', item):
            dossiers_physiques.append(item)

    # Étape 3: Associer Excel → Physique → Audio → Page Couverture
    work_orders_complets = []
    for wo_excel in work_orders_excel:
        numero = wo_excel['numero_dossier']

        # Trouver dossier physique
        dossier_path = next((d for d in dossiers_physiques if numero in d), None)

        # Localiser page couverture (root)
        page_couv = next(
            (f for f in os.listdir(extracted_dir)
             if numero in f and f.endswith('.docx')),
            None
        )

        # Localiser fichier audio (profond)
        audio_file = localiser_fichier_audio(
            os.path.join(extracted_dir, dossier_path),
            numero
        )

        work_orders_complets.append({
            'numero_dossier': numero,
            'dossier_path': os.path.join(extracted_dir, dossier_path),
            'page_couverture': os.path.join(extracted_dir, page_couv),
            'audio_file': audio_file,
            'excel_work_order': excel_path,
            'metadata_excel': wo_excel
        })

    return work_orders_complets
```

**4. Intégration dans main() avec branches** :
```python
# Détecter multi-Work Orders
work_orders_multiples = detecter_work_orders_multiples(extract_dir, excel_path)

if len(work_orders_multiples) > 1:
    # BRANCHE MULTI-WO: Boucler sur chaque Work Order
    for i, wo in enumerate(work_orders_multiples, 1):
        metadonnees = extraire_metadonnees_spr(wo['page_couverture'])
        metadata_excel = parser_excel_work_order(wo['excel_work_order'], wo['numero_dossier'])
        project_dir = creer_structure_projet_spr(output_dir, None, fichiers, metadonnees)
        generer_metadata_json(metadonnees, fichiers, metadata_path, metadata_excel)
        valider_metadonnees_spr(metadonnees)
else:
    # BRANCHE SIMPLE: Mode original (backward compatible)
    # ... code existant inchangé ...
```

**Résultat** :
- ✅ Traitement automatique de 6 Work Orders depuis RCE-9878-AA
- ✅ 100% détection via Excel source-of-truth
- ✅ Localisation audio dans structure profonde DAUDIO/YYYY-MM-DD/_HHMM/MCx-xxxxx/xxxx.a00
- ✅ Validation croisée Excel ↔ Structure physique
- ✅ Backward compatible (mode simple fonctionne toujours)

**Fichiers** :
- `implementation/preparation_work_order.py` lignes 293-593, 1274-1413
- `tests/test_workflow0_multi_wo.py` (test E2E)
- `Documentation/ANALYSE_EXCEL_MULTI_WORK_ORDERS.md` (analyse complète)

**Bénéfices** :
- Économie de temps : 6 Work Orders traités en 1 exécution
- Fiabilité : Excel garantit aucun dossier manqué
- Conformité : Chaque Work Order validé individuellement
- Traçabilité : metadata_work_order.json enrichi pour chaque dossier

---

# Pipeline de Transcription CISR

## Architecture Complète (4 Workflows)

```
┌─────────────────────────────────────────────────────────────┐
│  0. PRÉPARATION WORK ORDER (2026-01-06)                     │
│     ─ Décompression ZIP work order                          │
│     ─ Lecture Excel (source de vérité)                      │
│     ─ Détection Multi-Work Orders (6+ dossiers par ZIP)     │
│     ─ Extraction métadonnées page couverture                │
│     ─ Support SPR (simple, 1 dossier)                       │
│     ─ Support SPR Multi-WO (6+ dossiers, 1 Excel)           │
│     ─ Support SAR (complexe, 3+ dossiers, multi-cases)      │
│     ─ Localisation fichier(s) audio (structure profonde)    │
│     ─ Génération metadata_work_order.json (enrichi Excel)   │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  1. RÉCEPTION & PRÉPARATION                                 │
│     ─ Conversion .a00 → WAV (FFmpeg)                        │
│     ─ Transcription via AssemblyAI (API REST)              │
│     ─ Génération métadonnées JSON                           │
│     ─ Diarization (identification locuteurs)                │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  2. TRANSCRIPTION POST-TRAITEMENT                           │
│     ─ Nettoyage texte (suppressions éléments non substantiels) │
│     ─ Corrections linguistiques (dictionnaire)              │
│     ─ Mapping locuteurs (A→COMMISSAIRE, B→Demandeur)        │
│     ─ Structuration paragraphes                             │
│     ─ Génération document Word FORMATÉ CISR                 │
│     ─ Ajout tableaux métadonnées bilingues FR/EN            │
│     ─ Marges asymétriques (1.25/0.63/0.50/0.50)            │
│     ─ Police Arial 11pt, en-tête RIGHT + gras              │
│     ─ Validation QA (20 critères)                           │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  3. CERTIFICATION & DÉPÔT                                   │
│     ─ Signature finale transcripteur                        │
│     ─ Archive et stockage                                   │
└─────────────────────────────────────────────────────────────┘
```

## Fichiers du Pipeline

| Workflow | Instruction | Implémentation | Statut |
|----------|-------------|----------------|--------|
| 0. Préparation Work Order | `instruction/preparation_work_order.md` | `implementation/preparation_work_order.py` | ✅ Implémenté (2026-01-01) |
| 1. Réception | `instruction/reception_preparation.md` | `implementation/reception_preparation.py` | ✅ Existe |
| 2. Post-Traitement | `instruction/transcription_post_traitement.md` | `implementation/transcription_post_traitement.py` | ✅ Amélioré (2026-01-01) |
| 3. Certification | `instruction/certification_depot.md` | `implementation/certification_depot.py` | ✅ Existe |

---

# Ressources du Projet

## Dictionnaires et Checklists

- **`Documentation/CISR_Corrections_Dictionary.json`** : Dictionnaire des corrections linguistiques connues
  - Erreurs AssemblyAI récurrentes (FESPOLA→Hezbollah, soumis→sunnite)
  - Noms incertains à marquer avec (ph)
  - Éléments à supprimer (salutations, remerciements)

- **`Documentation/CISR_QA_Checklist.md`** : Liste de validation qualité (20 critères)
  - 14 critères automatisables
  - 3 critères semi-automatisables
  - 3 critères manuels

## Templates

- **`Documentation/Templates/signature certification.docx`** : Template certification finale
- **`Documentation/Templates/CISR_SPR_Document_Template.docx`** : Template document SPR (à créer)

## Scripts de Test

- **`test_transcription_simple.py`** : Test transcription via API REST (workaround SDK)
- **`test_transcription_wav.py`** : Test transcription via SDK (Python <3.14)

---

## ⚠️ CONTRAINTE #5: Validation Nom Commissaire - Liste Officielle CISR

**Problème Identifié** : 2026-01-06

Les noms de commissaires doivent être écrits **EXACTEMENT** comme sur la liste officielle CISR. Toute variation dans l'orthographe (accents, traits d'union, prénom/nom) est incorrecte.

**Source officielle** : https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx

**Structure** :
- **4 sections distinctes** correspondant aux 4 types de transcriptions :
  1. Section de la protection des réfugiés (SPR)
  2. Section d'appel des réfugiés (SAR)
  3. Section de l'immigration (SI)
  4. Section d'appel de l'immigration (SAI)

**Règle critique** :
- **TOUJOURS** valider le nom commissaire contre la section appropriée de la liste officielle
- **NE PAS** deviner l'orthographe
- **SI INCERTAIN** : Consulter la liste officielle avant de finaliser le document

**Impact sur le pipeline** :
- **Workflow 1.5 - Pass 5** (Cross-Validation Métadonnées) :
  - Vérifier présence nom commissaire dans texte
  - Générer WARNING si nom non trouvé
  - Inclure URL liste officielle dans rapport pour validation manuelle
  
- **TODO Sprint 3** : Implémenter scraping/cache liste officielle pour validation automatique
  - Parser HTML page officielle CISR
  - Créer dictionnaire {section: [liste_commissaires]}
  - Valider automatiquement nom commissaire vs. liste cachée
  - Suggérer corrections si nom proche mais inexact (Levenshtein distance)

**Exemple** :
```
Nom metadata : "Fides Paulin Nteziryayo"
Type : SPR
Validation : Vérifier dans section "Section de la protection des réfugiés"
Résultat attendu : Nom EXACT trouvé dans liste officielle
```

**Code** : Voir `pass5_cross_validation_metadata()` dans `implementation/transcription_corrections_intelligentes.py` lignes 390-501

**Prévention** :
- Ne jamais accepter un nom commissaire sans validation
- En cas de doute, générer WARNING haute priorité dans rapport
- Toujours inclure URL liste officielle dans rapport final

---

## ⚠️ CONTRAINTE #6: Formule Scoring Pass 6 - Interprétation Contre-Intuitive

**Problème Identifié** : 2026-01-06

La formule de scoring du Pass 6 mesure **la qualité du texte ORIGINAL** (avant corrections), pas la qualité finale.

**Formule actuelle** :
```python
score = 100 - (corrections_critiques × 2) - (corrections_moderees × 1)

corrections_critiques = Pass 1 (juridiques) + Pass 4 (mots mal reconnus)
corrections_moderees = Pass 2 (noms/accents) + Pass 3 (accords)
```

**Comportement contre-intuitif** :
- ✅ **Plus on trouve d'erreurs** → Plus on applique de corrections → **Score DIMINUE**
- ⚠️ Un texte avec 25 erreurs corrigées obtient score **60/100**
- ⚠️ Un texte avec 21 erreurs corrigées obtient score **67/100**

**Exemple concret** (MC3-03924) :
```
Dictionnaire V2.0 (110 entrées) :
  - 21 corrections appliquées
  - Score : 67/100
  
Dictionnaire V2.0 enrichi (113 entrées) :
  - 25 corrections appliquées (+4 erreurs trouvées)
  - Score : 60/100 (-7 points)
```

**Interprétation correcte** :
Le score représente **la qualité INITIALE du texte AssemblyAI**, PAS la qualité après corrections.
- Score élevé (85+) = Texte initial excellent, peu d'erreurs à corriger
- Score moyen (60-70) = Texte initial moyen, beaucoup d'erreurs corrigées
- Score bas (<50) = Texte initial mauvais, énormément d'erreurs

**Impact** :
- ✅ Le scoring actuel est **correct** pour évaluer la qualité de la transcription brute
- ⚠️ Mais il NE mesure PAS la qualité du texte FINAL (qui est meilleure après corrections)
- ⚠️ Les recommandations de révision sont basées sur qualité initiale, pas finale

**Recommandations** :
1. **Option A (Status quo)** : Conserver formule actuelle, clarifier documentation
   - Renommer "score qualité" → "score qualité initiale"
   - Expliquer que score bas = beaucoup d'améliorations appliquées (positif)
   
2. **Option B (Inversion)** : Inverser la formule pour mesurer qualité finale
   - `score = 40 + (corrections_critiques × 2) + (corrections_moderees × 1)`
   - Plus on corrige → Score augmente
   - Nécessite recalibration seuils (85+ devient quoi ?)

3. **Option C (Double métrique)** : Ajouter 2 scores distincts
   - `score_initial` : Qualité avant corrections (formule actuelle)
   - `score_final` : Qualité après corrections (nouvelle formule)
   - Permet de mesurer **l'amélioration apportée**

**Code** : Voir `pass6_qa_finale()` dans `implementation/transcription_corrections_intelligentes.py` lignes 508-590

**Décision** : À discuter avec utilisateur. Pour l'instant, conserver formule actuelle (Option A).

---

## ✅ BONNE PRATIQUE #6: Enrichissement Progressif Dictionnaire par Analyse Erreurs Résiduelles

**Contexte** : 2026-01-06

Pour atteindre 95%+ de similarité, il faut **analyser le fichier corrigé final** pour identifier les erreurs RÉSIDUELLES (non détectées par le dictionnaire actuel), puis enrichir le dictionnaire avec ces erreurs.

**Méthode** :
1. Exécuter pipeline complet sur transcription réelle
2. Lire fichier `*_PIPELINE_COMPLET.txt` généré
3. Comparer visuellement avec document manuel de référence
4. Identifier erreurs NON corrigées (grep patterns dans texte corrigé)
5. Ajouter ces erreurs au dictionnaire approprié (Pass 1-4)
6. Re-tester pipeline, mesurer amélioration
7. Répéter jusqu'à score cible atteint

**Exemple concret (MC3-03924)** :

Analyse du fichier corrigé révèle 3 erreurs résiduelles :
- ❌ "paragraphe **87**" (au lieu de "97(1)") → Ajouté à Pass 1
- ❌ "loi sur l'immigration **de** la protection" → Ajouté à Pass 1
- ❌ "**son fils**, qui est le plus **petit**" → Ajouté à Pass 3

**Résultat** :
- Dictionnaire enrichi : 110 → 113 entrées
- Corrections appliquées : 21 → 25 (+19%)
- Nouvelles erreurs détectées : Pass 1 +3, Pass 3 +1

**Outils utiles** :
```bash
# Chercher patterns dans texte corrigé
grep -i "paragraphe 87\|article 87" transcription_PIPELINE_COMPLET.txt

# Chercher formulations incorrectes
grep -i "son fils\|le plus petit" transcription_PIPELINE_COMPLET.txt
```

**Cycle d'amélioration** :
```
Test → Analyser erreurs résiduelles → Enrichir dict → Re-tester → Répéter
```

**Bénéfice** : Approche systématique pour atteindre 95%+ qualité par itérations successives.

---

---

## ✅ BONNE PRATIQUE #7: Système d'Apprentissage Continu Automatique

**Contexte** : 2026-01-06

Pour améliorer constamment la qualité des corrections, implémenter un système qui **enrichit automatiquement le dictionnaire** après chaque Work Order traité.

**Principe** :
> "À chaque fois que tu travailles sur un nouveau work order et que tu trouves de nouveaux types d'erreurs, tu améliores ton dictionnaire de correction et tout autre endroit pertinent pour que tu sois en amélioration constante."

**Implémentation** : `implementation/apprentissage_continu_dictionnaire.py`

**Processus** :
1. Comparer transcription brute vs document référence manuel
2. Détecter différences mot-à-mot avec algorithme de similarité
3. Classifier chaque erreur automatiquement (Pass 1-4)
4. Proposer ajout au dictionnaire approprié
5. Sauvegarder avec backup automatique

**Méthode** :
```bash
# Après traitement d'un Work Order
python implementation/apprentissage_continu_dictionnaire.py \
    transcription_brute.txt \
    document_reference.docx
```

**Résultat MC3-16722** :
- 17 différences détectées
- 17 nouvelles entrées proposées
- Dictionnaire : 113 → 142 entrées (+26%)
- Backup automatique créé

**Classification intelligente** :
```python
def _classifier_type_erreur(mot_incorrect, mot_correct):
    # Pass 1 : Termes juridiques
    if 'article' in mot or 'paragraphe' in mot or 'loi' in mot:
        return 'pass1_termes_juridiques'
    
    # Pass 2 : Accents seulement
    if difference_seulement_accents(mot_incorrect, mot_correct):
        return 'pass2_noms_propres_accents'
    
    # Pass 3 : Accords grammaticaux
    if difference_accord_genre_nombre(mot_incorrect, mot_correct):
        return 'pass3_accords_grammaticaux'
    
    # Pass 4 : Autres (mots mal reconnus)
    return 'pass4_mots_mal_reconnus'
```

**Limitations connues** :
- ⚠️ Génère quelques faux positifs contextuels (ex: "de" ↔ "des", "vous" ↔ "vos")
- ⚠️ Comparaison simplifiée mot-à-mot (version production devrait utiliser diff ligne par ligne)
- ⚠️ Ne détecte pas erreurs de structure (tableaux, formatage)

**Améliorations futures** :
1. **Filtrage intelligent** : Algorithme ML pour éliminer faux positifs
2. **Validation manuelle** : Interface CLI pour approuver/rejeter propositions avant sauvegarde
3. **Scoring confiance** : Assigner score de confiance à chaque proposition (0-100%)
4. **Apprentissage statistique** : Tracker fréquence erreurs pour prioriser enrichissement

**Bénéfice** : Système auto-apprenant qui s'améliore à chaque utilisation sans intervention manuelle.

---

## ⚠️ CONTRAINTE #9: Fichiers Audio Multi-Work Orders - Structure Pré-Découpée

**Problème Identifié** : 2026-01-06

Dans les Work Orders multi-dossiers (exemple: RCE-9878-AA avec 6 dossiers), les fichiers audio sont **déjà pré-découpés par la CISR** dans des sous-dossiers séparés.

**Structure réelle** :
```
MC3-56703/DAUDIO/2025-12-09/_0231/MC3-56703/6703.a00
MC3-66060/DAUDIO/2025-12-09/_0303/MC3-66060/6060.a00
MC3-16722/DAUDIO/2025-12-09/_1046/MC3-16722/6722.a00
```

**Règle de nommage** :
- Nom fichier = 4 derniers chiffres du numéro de dossier
- MC3-56703 → `6703.a00`
- MC3-43157 → `3157.a00`

**Timestamps dossiers `_HHMM`** :
- Représentent l'**heure de la journée** de l'enregistrement (02h31, 09h02, etc.)
- **NE PAS confondre** avec remarques Excel "commence à X:XX" qui sont informatives seulement

**Solution** :
```python
def localiser_fichier_audio(numero_dossier, extracted_dir):
    """
    Trouve le fichier .a00 pour un dossier donné (déjà pré-découpé).
    Pattern: MC3-xxxxx/DAUDIO/YYYY-MM-DD/_HHMM/MC3-xxxxx/xxxx.a00
    """
    base_path = os.path.join(extracted_dir, numero_dossier)

    # Recherche récursive
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith('.a00'):
                return os.path.join(root, f)

    raise FileNotFoundError(f"Audio .a00 non trouvé pour {numero_dossier}")
```

**Impact Workflow 1** :
- **PAS de découpage audio nécessaire** (contrairement à l'hypothèse initiale)
- Un fichier audio `.a00` par dossier, déjà isolé
- Workflow simplifié : Conversion → Transcription directe

**Prévention** :
- Ne jamais chercher à découper audio via `ffmpeg` dans multi-Work Orders
- Fichier audio toujours situé 5 niveaux sous le numéro de dossier
- Vérifier présence fichier `.a00` lors extraction métadonnées

**Documentation complète** : `Documentation/ANALYSE_EXCEL_MULTI_WORK_ORDERS.md` section 13

---

## ⚠️ CONTRAINTE #7: Faux Positifs Apprentissage Continu (RÉSOLU V2.1)

**Problème Identifié** : 2026-01-06
**Résolu** : 2026-01-07 (Dictionnaire V2.1)

Le système d'apprentissage continu peut générer des **faux positifs** en proposant des corrections contextuelles non généralisables.

**MISE À JOUR 2026-01-07** : Dictionnaire V2.0 contenait 8 faux positifs critiques qui ont été supprimés dans V2.1. Test MC3-16722 confirme amélioration :
- **V2.0** : 11 corrections (incluant 110× "et"→"met" **détruisant le texte**) | Score 81/100 (BON)
- **V2.1** : 9 corrections (propres) | Score **85/100 (EXCELLENT)** ✅

**Exemples détectés** :
```json
{
  "vous": "vos",           // Contextuel (possessif vs pronom)
  "des": "de",             // Contextuel (article partitif)
  "de": "des",             // Contextuel (inverse du précédent!)
  "une": "ne",             // Faux positif (confusion)
  "les": "le",             // Contextuel (nombre)
  "est": "et",             // Faux positif (verbe vs conjonction)
}
```

**Cause racine** :
- Algorithme de comparaison trop simple (diff mot-à-mot)
- Pas de prise en compte du contexte grammatical
- Similarité Levenshtein seule insuffisante (70% seuil trop bas)

**Impact** :
- Pollue le dictionnaire avec entrées non pertinentes
- Risque de sur-corrections dans futurs Work Orders
- Nécessite nettoyage manuel du dictionnaire

**Solution temporaire** :
1. **Révision manuelle** : Examiner nouvelles entrées avant validation
2. **Seuil similarité plus élevé** : Passer de 70% à 85%
3. **Blacklist contextuels** : Exclure mots courants ("de", "des", "le", "les", "vous", "vos")

**Solution long-terme** :
1. **Analyse grammaticale** : Intégrer POS tagging (spaCy, NLTK)
2. **Contexte N-grammes** : Comparer bi-grammes et tri-grammes au lieu de mots isolés
3. **Validation statistique** : Seulement ajouter si erreur apparaît 3+ fois
4. **Interface validation** : CLI interactive pour approuver/rejeter chaque proposition

**Code** : Voir `implementation/apprentissage_continu_dictionnaire.py` lignes 88-120

**Prévention** :
- Toujours exécuter apprentissage continu en mode "proposition" d'abord
- Réviser fichier `.backup` avant de valider changements
- Implémenter validation manuelle dans version production

---

