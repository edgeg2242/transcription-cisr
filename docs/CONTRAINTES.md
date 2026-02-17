# Contraintes Techniques -- Pipeline CISR

Toutes les contraintes identifiees lors du developpement, classees par categorie.

---

## Audio

### Contrainte #5 -- Matching Fichiers Audio Strict
**Date** : 2026-01-07 | **Severite** : CRITIQUE

Le matching des fichiers audio doit etre STRICT. Utiliser `startswith()`, jamais `in`.

**Bug rencontre** : MC3-03924 transcrit avec audio MC3-43157 (fallback silencieux sur audio_files[0]).

**Regle** :
```python
# CORRECT : Matching strict
basename.startswith(dernier_4_chiffres + '.') or basename.startswith(dernier_4_chiffres + '_')

# INCORRECT : Matching permissif
if dernier_4_chiffres in os.path.basename(audio)  # DANGEREUX
```

**Si aucun match** : Lever FileNotFoundError (jamais de fallback silencieux).

### Contrainte #9 -- Audio Pre-Decoupe dans Multi-Work Orders
**Date** : 2026-01-06 | **Severite** : IMPORTANTE

Les fichiers audio dans les ZIP multi-WO sont **deja pre-decoupes par la CISR**. Chaque dossier MC-xxxxx contient 1 fichier audio unique.

**Structure** : `MC3-xxxxx/DAUDIO/YYYY-MM-DD/_HHMM/MC3-xxxxx/xxxx.a00`
**Nommage** : 4 derniers chiffres du numero = nom fichier (MC3-56703 -> `6703.a00`)
**Timestamps _HHMM** : Heure de journee d'enregistrement (informatif seulement)

**Regle** : NE JAMAIS concatener les fichiers audio. NE PAS utiliser Recording Remarks pour decoupage.

### Format .a00 = MP2 Dictaphone
Les fichiers .a00 sont du format dictaphone v4.01, reellement du MP2 audio. Conversion via FFmpeg :
```bash
ffmpeg -i fichier.a00 -ar 16000 -ac 1 fichier.wav
```
Performance : ~0.2 secondes pour 10 minutes audio.

---

## Excel / ZIP

### Contrainte #8 -- ZIP Multi-Work Orders
**Date** : 2026-01-06 | **Severite** : CRITIQUE

Un Work Assignment (ZIP) peut contenir **PLUSIEURS Work Orders** (typiquement 4-10).

**Structure** :
- 1 fichier Excel pour TOUS les WO (source de verite)
- N sous-dossiers MC-xxxxx (1 par WO)
- N pages couvertures a la racine
- N fichiers audio dans sous-dossiers DAUDIO profonds

**Regle** : Toujours detecter le nombre de WO via Excel. NE PAS supposer 1 ZIP = 1 WO.

### Contrainte #14 -- Nomenclature Work Assignment vs Work Order
**Date** : 2026-01-08 | **Severite** : IMPORTANTE

- **Work Assignment** : Fichier ZIP initial (ex: RCE-9878-AA.zip) contenant PLUSIEURS Work Orders
- **Work Order** : Dossier individuel pour UNE transcription (ex: MC3-16722)

### Contrainte #3 -- Detection Type via Chemin Complet
**Date** : 2026-01-01 | **Severite** : MOYENNE

Le type (SPR/SAR) peut etre dans le **nom du dossier parent** extrait du ZIP, pas dans le nom du fichier Excel.

**Regle** : Utiliser `excel_path.upper()` (chemin complet), pas `os.path.basename()`.

---

## Pages Couvertures

### Contrainte #1 -- Structure Simplifiee SAR
**Date** : 2026-01-01 | **Severite** : IMPORTANTE

Pages couvertures SAR = structure **completement differente** de SPR :
- SPR : Tableau detaille 17L x 3C (toutes metadonnees)
- SAR : Tableau minimal 1L x 2C (numeros dossiers seulement)

### Contrainte #2 -- Lignes Vides Intercalaires
**Date** : 2026-01-01 | **Severite** : MOYENNE

Les tableaux Word CISR contiennent des **lignes vides entre chaque ligne de donnees**.

**Regle** : Filtrer les lignes vides AVANT d'extraire les donnees.
```python
lignes_donnees = [row for row in table.rows if row.cells[1].text.strip()]
```

### Contrainte #4 -- Numeros dans Nom Fichier
**Date** : 2026-01-01 | **Severite** : MOYENNE

Les numeros MC se trouvent souvent dans le **nom du fichier** page couverture, pas dans le contenu.

**Regle** : Chercher regex `MC[2-5]-\d+` dans `filename + contenu paragraphes`.

---

## Detection Type

### Contrainte #12 -- 4 Types FONDAMENTALEMENT Differents
**Date** : 2026-01-07 | **Severite** : CRITIQUE

Les 4 types (SPR/SAR/SI/SAI) ont des structures, formats et contenus FONDAMENTALEMENT DIFFERENTS. Voir [TYPES_DOCUMENTS.md](TYPES_DOCUMENTS.md) pour tableau comparatif complet.

**Regle** : TOUJOURS verifier le type AVANT d'appliquer tout formatage. NE JAMAIS supposer SPR = SAR.

### Ambiguite "RAD" dans Detection SPR vs SAR
**Date** : 2026-01-02

L'acronyme "RAD" (Refugee Appeal Division = SAR) se retrouve aussi dans "Refugies Protection Division" (RPD = SPR).

**Regle** :
1. Verifier SPR/RPD en PRIORITE (cas le plus frequent)
2. Exclure "PROTECTION" si "RAD" detecte
```python
if "SPR" in fullpath or "RPD FILE" in fullpath:
    return TypeTranscription.SPR
elif "SAR" in fullpath or ("RAD" in fullpath and "PROTECTION" not in fullpath.upper()):
    return TypeTranscription.SAR
```

---

## Contenu Transcription

### Contrainte #11 -- SPR = MOTIFS Seulement
**Date** : 2026-01-07 | **Severite** : CRITIQUE

Les documents SPR contiennent **SEULEMENT la section MOTIFS** de la decision, PAS l'audience complete.

**Audience complete SPR** (~90 min) :
1. Formalites ouverture (5 min)
2. Interrogatoire commissaire (45-90 min)
3. Plaidoyers avocat (15-30 min)
4. **MOTIFS de la decision (15-30 min) -- SEULE PARTIE A TRANSCRIRE**

**Patterns debut MOTIFS** :
- "Donc, j'ai eu aujourd'hui a examiner..."
- "Voici les motifs de ma decision..."
- "Ma decision aujourd'hui, c'est que..."

**Patterns fin MOTIFS** :
- "Merci pour votre temoignage"
- "L'audience est terminee/levee/ajournee"

---

## Qualite

### Contrainte #6 -- Scoring Contre-Intuitif
**Date** : 2026-01-06 | **Severite** : INFORMATIVE

Le score QA mesure la qualite du texte ORIGINAL (avant corrections), pas la qualite finale.
- Plus d'erreurs trouvees -> Plus de corrections -> Score DIMINUE
- Score = 100 - (critiques x 2) - (moderees x 1)

**Interpretation** : Score bas = texte initial mauvais MAIS beaucoup ameliore.

### Contrainte #7 -- Faux Positifs Dictionnaire
**Date** : 2026-01-06 | **Severite** : IMPORTANTE | **Resolu V2.1**

L'apprentissage continu peut generer des faux positifs (ex: "et"->"met" detruisant le texte).

**Regle** : Blacklister mots courants ("de", "des", "le", "les", "vous", "vos", "est", "et", "une").
Toujours executer en mode "proposition" d'abord. Relever seuil similarite a 85%.

### Contrainte #5a -- Validation Nom Commissaire
**Date** : 2026-01-06 | **Severite** : IMPORTANTE

Noms de commissaires doivent etre EXACTEMENT conformes a la liste officielle CISR.
**Source** : https://www.irb-cisr.gc.ca/fr/commissaires/Pages/list-of-members-liste-des-membres.aspx

---

## Document Word

### Marges Asymetriques par Type
| Type | Haut | Bas | Gauche | Droite |
|------|------|-----|--------|--------|
| SPR | 1.25" | 0.63" | 0.50" | 0.50" |
| SAR | 1.25" | 0.69" | 1.00" | 1.00" |

### Tableaux Metadonnees Bilingues
- SPR : Tableau 1 = 17L x 3C (donnees + lignes vides intercalaires), Tableau 2 = 1L x 1C (vide)
- SAR : Tableau 1 = 1L x 2C (numeros dossiers), Tableau 2 = 15L x 3C (metadonnees)

### Contrainte #10 -- Conversion Audio Cloud Abandonnee
**Date** : 2026-01-07

CloudConvert API initialement prevu pour deploiement serveur distant. La conversion directe via FFmpeg
reste la solution retenue. FFmpeg est utilise pour conversion `.a00` -> WAV et decoupage audio si necessaire.

---

## Environnement

### Python 3.14 + AssemblyAI SDK Incompatibilite
Le SDK AssemblyAI (v0.17.0) est incompatible avec Python 3.14 (dependance Pydantic v1).

**Solution** : Utiliser l'API REST AssemblyAI directement via `requests`.

```python
# Upload audio
POST https://api.assemblyai.com/v2/upload

# Request transcription
POST https://api.assemblyai.com/v2/transcript

# Poll for completion
GET https://api.assemblyai.com/v2/transcript/{transcript_id}
```

### Encodage UTF-8 Windows
La console Windows utilise CP1252 par defaut, causant des erreurs avec les emojis.

**Solution** : Ajouter au debut de TOUS les scripts Python :
```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```
