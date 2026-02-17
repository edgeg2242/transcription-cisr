# Historique des Bonnes Pratiques et Decisions

---

## Bonnes Pratiques Identifiees

### BP #1 -- Extraction Dossier Temporaire Racine (2026-01-01)
Extraire les ZIP dans le dossier racine du projet (`os.getcwd()`) plutot que dans le dossier source evite les chemins trop longs sous Windows (MAX_PATH 260 caracteres).

### BP #2 -- Formatage Word CISR Marges Asymetriques (2026-01-01)
Documents CISR utilisent des marges asymetriques specifiques : Haut 1.25", Bas 0.63", Gauche 0.50", Droite 0.50" (pour SPR). Conformite 98%+ avec documents manuels.

### BP #3 -- Tableaux Metadonnees Bilingues FR/EN (2026-01-01)
Les documents CISR contiennent 2 tableaux bilingues : Tableau 1 (17L x 3C : FR | Valeur | EN) + Tableau 2 (separateur). Placement juste AVANT "FIN DES MOTIFS".

### BP #4 -- Script de Test E2E Automatise (2026-01-02)
Un test end-to-end automatise reduit le temps de validation de 120s a ~1s. Detecte les regressions apres chaque changement.

### BP #5 -- Tableaux CISR avec Lignes Vides Intercalaires (2026-01-06)
Les tableaux professionnels CISR utilisent 17 lignes (9 donnees + 8 vides) au lieu de 9 lignes compactes. Ameliore la lisibilite et la conformite visuelle.

### BP #6 -- Support Multi-Work Orders via Excel Source-of-Truth (2026-01-06)
L'Excel a la racine du ZIP est la source de verite pour detecter tous les Work Orders. Lire toutes les lignes apres les headers. Permet le traitement automatique de 6+ WO en une execution.

### BP #7 -- Systeme d'Apprentissage Continu Automatique (2026-01-06)
Compare transcription brute vs referentiel humain, detecte erreurs residuelles, classifie par pass (1-4), propose ajouts au dictionnaire. Dictionnaire passe de 113 a 142 entrees (+26%) apres un seul batch.

---

## Decisions Structurelles

### 2026-02-17 -- Abandon Framework "ii" vers Chef d'Orchestre / Vibe Kanban
Le framework Information/Implementation (instruction/*.md + implementation/*.py) etait trop lourd et causait une double maintenance. Remplace par : CLAUDE.md concis (~150 lignes) + docs/ + skills/ comme interface principale.

### 2026-02-17 -- Creation de 8 Skills Projet CISR
Skills comme point d'entree principal du pipeline : analyse-work-assignment, pipeline-spr, pipeline-sar, pipeline-si, pipeline-sai, validation-qualite, enrichissement-dictionnaire, learning-loop.

### 2026-01-07 -- Abandon CloudConvert
Decouverte que .a00 = MP2 dictaphone renommable en .mp3. CloudConvert inutile. FFmpeg conserve pour decoupage audio uniquement.

### 2025-12-30 -- API REST AssemblyAI vs SDK
SDK incompatible Python 3.14 (Pydantic v1). Utilisation API REST directe.

---

## Chronologie des Contraintes

| Date | # | Description | Resolu |
|------|---|-------------|--------|
| 2025-12-30 | -- | Incompatibilite Python 3.14 / AssemblyAI SDK | Contourne (API REST) |
| 2025-12-30 | -- | Encodage UTF-8 Windows | Resolu |
| 2025-12-30 | -- | Format .a00 = MP2 dictaphone | Resolu |
| 2026-01-01 | #1 | Pages couvertures SAR simplifiees | Resolu |
| 2026-01-01 | #2 | Lignes vides intercalaires tableaux Word | Resolu |
| 2026-01-01 | #3 | Detection type via chemin complet | Resolu |
| 2026-01-01 | #4 | Numeros MC dans nom fichier | Resolu |
| 2026-01-02 | -- | Ambiguite "RAD" dans detection SPR/SAR | Resolu |
| 2026-01-06 | #5 | Matching audio strict (BUG CRITIQUE) | Resolu |
| 2026-01-06 | #5a | Validation nom commissaire | A implementer |
| 2026-01-06 | #6 | Scoring contre-intuitif | Documente |
| 2026-01-06 | #7 | Faux positifs dictionnaire | Resolu (V2.1) |
| 2026-01-06 | #8 | ZIP multi-Work Orders | Implemente |
| 2026-01-06 | #9 | Audio pre-decoupe | DECOUVERTE |
| 2026-01-07 | #10 | CloudConvert abandonne | Resolu |
| 2026-01-07 | #11 | SPR = MOTIFS seulement | CRITIQUE |
| 2026-01-07 | #12 | 4 types documents differents | CRITIQUE |
| 2026-01-08 | #14 | WA vs WO nomenclature | Documente |
