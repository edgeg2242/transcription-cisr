# Skill : Validation Qualite

## Description

Compare le document Word produit par le pipeline de transcription contre un **referentiel gold standard** (transcription manuelle de reference). Evalue la qualite sur 3 axes : contenu textuel, conformite de formatage, et grille QA 20 criteres CISR. Produit un rapport detaille avec scores, ecarts localises et recommandations d'amelioration.

---

## Declenchement

```
/validation-qualite <resultat.docx> <type>
```

Utiliser cette skill **apres** l'execution de n'importe quelle skill pipeline (`/pipeline-spr`, `/pipeline-sar`, `/pipeline-si`, `/pipeline-sai`).

Parametres :
- `<resultat.docx>` : Chemin vers le document Word produit par le pipeline
- `<type>` : Type de document (SPR, SAR, SI, SAI) -- optionnel si detecte depuis metadata

---

## Prerequis

- Document Word `.docx` resultat du pipeline (a comparer)
- Referentiel gold standard correspondant dans `referentiels/<type>/` (si disponible)
- Fichier `metadata_work_order.json` dans le dossier du Work Order (pour identification type)
- Module Python `python-docx` installe pour lecture des documents Word
- Module Python `difflib` (standard library) pour comparaison textuelle

---

## Actions

### Etape 1 -- Chargement et identification

1. **Charger** le document Word resultat du pipeline
2. **Identifier** le type (SPR/SAR/SI/SAI) :
   - Source prioritaire : parametre `<type>` fourni par l'utilisateur
   - Source secondaire : `metadata_work_order.json` dans le meme dossier
   - Source tertiaire : detection automatique depuis le contenu du document (titre, numeros dossier)
3. **Logger** le type identifie et le numero de dossier

### Etape 2 -- Localisation du referentiel

4. **Chercher** le referentiel correspondant dans `referentiels/<type>/`
   - Pattern : `referentiels/SPR/MC3-xxxxx_reference.docx`
   - Si aucun referentiel trouve : signaler que seule la validation formatage/QA sera possible
   - La comparaison textuelle requiert un referentiel gold standard

### Etape 3 -- Comparaison textuelle

5. **Extraire** le texte brut des deux documents (pipeline et referentiel)
   - Parcourir tous les paragraphes du document Word
   - Ignorer les en-tetes, pieds de page, tableaux (compares separement)
   - Normaliser : minuscules, suppression espaces multiples, normalisation Unicode
6. **Calculer** la similarite mot-a-mot :
   - Utiliser `difflib.SequenceMatcher` pour ratio de similarite global
   - Identifier les operations : insertions, suppressions, substitutions
   - Cible : **similarite >= 95%**
7. **Generer** la liste des ecarts textuels :
   - Pour chaque difference : position (paragraphe, mot), texte pipeline vs texte reference
   - Classifier chaque ecart : erreur critique (sens altere) vs mineure (formulation)
   - Compter : total differences, critiques, mineures

### Etape 4 -- Comparaison formatage

8. **Verifier les marges** selon le type :

   | Type | Haut | Bas | Gauche | Droite |
   |------|------|-----|--------|--------|
   | SPR | 1.25" | 0.63" | 0.50" | 0.50" |
   | SAR | 1.25" | 0.69" | 1.00" | 1.00" |
   | SI | A definir | A definir | A definir | A definir |
   | SAI | A definir | A definir | A definir | A definir |

   - Tolerance : +/- 0.1 cm (conforme grille QA critere 17)

9. **Verifier la police** :
   - Attendue : Arial 11pt pour le corps du texte
   - Verifier chaque paragraphe (sauf en-tetes et titres)
   - Signaler tout paragraphe non conforme avec son numero de ligne

10. **Verifier la structure des tableaux** selon le type :

    | Type | Tableau 1 | Tableau 2 |
    |------|-----------|-----------|
    | SPR | 17L x 3C (metadonnees avec lignes vides) | 1L x 1C (vide) |
    | SAR | 1L x 2C (numeros dossiers) | 15L x 3C (metadonnees) |
    | SI | A definir | A definir |
    | SAI | A definir | A definir |

11. **Verifier le titre** selon le type :
    - SPR : "TRANSCRIPTION DES Motifs..."
    - SAR : "Transcription complete..."
    - SI : A definir
    - SAI : A definir

### Etape 5 -- Comparaison nomenclature

12. **Verifier** la convention de nommage du fichier selon le type :
    - SPR : `MC[1-4]-xxxxx_transcription_YYYYMMDD.docx`
    - SAR : `MC5-xxxxx_transcription_YYYYMMDD.docx`
    - SI : `0018-Cx-xxxxx_transcription_YYYYMMDD.docx`
    - SAI : `MC0-xxxxx_transcription_YYYYMMDD.docx`
13. **Verifier** que le numero de dossier dans le nom de fichier correspond aux metadonnees

### Etape 6 -- Grille QA 20 criteres CISR

14. **Evaluer les 14 criteres automatisables** :

    _Section 1 -- En-tete/Metadonnees :_
    - [ ] Critere 1 : Presence en-tete complet (numero, IUC, huis clos) **[FAIL IMMEDIAT si absent]**
    - [ ] Critere 2 : Numero dossier format valide
    - [ ] Critere 3 : IUC/UCI present (10 chiffres)
    - [ ] Critere 4 : Titre document correct selon type
    - [ ] Critere 5 : Sous-titre present

    _Section 2 -- Contenu/Formatage :_
    - [ ] Critere 6 : Format dialogue coherent (prefixe locuteur >= 90%)
    - [ ] Critere 7 : Noms propres coherents (0 variation)
    - [ ] Critere 8 : Acronymes corrects (0 erreur connue type FESPOLA) **[FAIL IMMEDIAT si erreur]**
    - [ ] Critere 9 : Incertitudes marquees (ph)
    - [ ] Critere 10 : Paragraphes structures (>= 3 distincts)

    _Section 3 -- Certification :_
    - [ ] Critere 11 : Certification complete **[FAIL IMMEDIAT si absent]**
    - [ ] Critere 12 : Date valide
    - [ ] Critere 13 : Nom transcripteur present
    - [ ] Critere 14 : Nom agence present

15. **Evaluer les 3 criteres semi-automatisables** (avec avertissement) :
    - [ ] Critere 15 : Marqueur "FIN DES MOTIFS" (SPR) ou "FIN DE LA TRANSCRIPTION" (SAR/SI/SAI)
    - [ ] Critere 16 : Styles corrects (Heading 8, Normal, No Spacing)
    - [ ] Critere 17 : Marges conformes (+/- 0.1 cm)

16. **Rappeler les 3 criteres manuels** au transcripteur :
    - [ ] Critere 18 : Police conforme (verification visuelle)
    - [ ] Critere 19 : Metadonnees Word nettoyees (auteur, commentaires)
    - [ ] Critere 20 : Orthographe acceptable (< 10 erreurs)

### Etape 7 -- Generation du rapport

17. **Calculer les scores** :
    - Score similarite textuelle : ratio `difflib.SequenceMatcher` x 100 (%)
    - Score formatage : nombre criteres conformes / total criteres formatage x 100 (%)
    - Score QA : nombre criteres passes / 20
18. **Generer** le rapport detaille avec :
    - Resume executif (PASS / PASS conditionnel / FAIL)
    - Score similarite textuelle avec detail des ecarts
    - Score formatage avec liste des non-conformites
    - Resultat grille QA 20 criteres (passe/echoue par critere)
    - Liste des ecarts localises (paragraphe, position)
    - Recommandations d'amelioration classees par priorite
19. **Sauvegarder** le rapport en deux formats :
    - Texte lisible : `rapport_validation_MC[x]-xxxxx.txt`
    - JSON structure : `rapport_validation_MC[x]-xxxxx.json`

---

## Criteres de succes

| Critere | Seuil | Consequence si non atteint |
|---------|-------|---------------------------|
| Similarite textuelle | >= 95% | Reviser corrections passes 1-4 |
| Formatage | 100% conforme au type | Corriger parametres de generation |
| Grille QA | >= 18/20 | PASS conditionnel -- corriger ecarts |
| Grille QA | 20/20 | PASS -- document pret pour depot |
| Grille QA | < 17/20 | FAIL -- retraitement necessaire |
| Criteres 1, 8, 11 | PASS obligatoire | FAIL IMMEDIAT si echoue |

---

## References

- @docs/CONVENTIONS_TRANSCRIPTION.md -- Regles de transcription et grille QA 20 criteres
- @docs/TYPES_DOCUMENTS.md -- Comparatif formats SPR/SAR/SI/SAI (marges, tableaux, titres)
- @docs/CONTRAINTES.md -- Contraintes techniques identifiees
- @referentiels/README.md -- Index des documents de reference gold standard par type

---

## Outputs

| Fichier | Description |
|---------|-------------|
| `rapport_validation_MC[x]-xxxxx.txt` | Rapport lisible avec scores, ecarts et recommandations |
| `rapport_validation_MC[x]-xxxxx.json` | Rapport structure pour traitement automatise |

### Structure JSON du rapport

```json
{
  "numero_dossier": "MC3-xxxxx",
  "type": "SPR",
  "date_validation": "2026-01-15T14:30:00",
  "verdict": "PASS | PASS_CONDITIONNEL | FAIL",
  "scores": {
    "similarite_textuelle": 96.2,
    "formatage": 100.0,
    "grille_qa": "19/20"
  },
  "ecarts_textuels": [
    {
      "paragraphe": 12,
      "position_mot": 45,
      "texte_pipeline": "paragraphe 87",
      "texte_reference": "paragraphe 97(1)",
      "severite": "critique"
    }
  ],
  "ecarts_formatage": [],
  "grille_qa": {
    "criteres_passes": [1, 2, 3, "..."],
    "criteres_echoues": [16],
    "criteres_manuels": [18, 19, 20]
  },
  "recommandations": [
    {
      "priorite": "haute",
      "description": "Ajouter 'paragraphe 97(1)' au dictionnaire Pass 1",
      "action": "Enrichir CISR_Corrections_Dictionary.json"
    }
  ]
}
```

---

## Notes d'utilisation

- **Avec referentiel** : Comparaison textuelle complete + formatage + QA. Resultat le plus fiable.
- **Sans referentiel** : Seules les validations de formatage et la grille QA sont executees. La similarite textuelle est marquee "N/A -- referentiel absent".
- **Apprentissage continu** : Les ecarts detectes alimentent l'enrichissement du dictionnaire de corrections. Utiliser `/enrichissement-dictionnaire` apres cette skill pour integrer les erreurs residuelles identifiees.
- **Premier WO d'un nouveau type** : Si c'est le premier Work Order SAI ou SI traite, les resultats de cette validation servent a calibrer les parametres de formatage du type. Documenter les decouvertes dans `docs/TYPES_DOCUMENTS.md`.
