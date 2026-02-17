# Types de Documents CISR -- Comparatif Bilingue FR/EN

## Nomenclature Bilingue

| Francais | Anglais | Acronyme FR | Acronyme EN |
|----------|---------|-------------|-------------|
| Section de la Protection des Refugies | Refugee Protection Division | SPR | RPD |
| Section d'Appel des Refugies | Refugee Appeal Division | SAR | RAD |
| Section de l'Immigration | Immigration Division | SI | ID |
| Section d'Appel de l'Immigration | Immigration Appeal Division | SAI | IAD |

## Comparatif Detaille

| Caracteristique | SPR / RPD | SAR / RAD | SI / ID | SAI / IAD |
|-----------------|-----------|-----------|---------|-----------|
| **Numeros dossier** | MC1, MC2, MC3, MC4 | MC5, MC6 | 0018-Cx-xxxxx | MC0 |
| **Contenu audio** | MOTIFS seulement | Audience COMPLETE | Audience COMPLETE | Audience COMPLETE |
| **Duree audio** | 10-30 min | 60-180 min | Variable | Variable |
| **Locuteurs** | 1 (Commissaire) | 4-6 (Multi-parties) | 4-6 | 4-6 |
| **Diarization** | Non requise | CRITIQUE | CRITIQUE | CRITIQUE |
| **Marges L/R** | 0.50" | 1.00" (DOUBLE) | A definir | A definir |
| **Marges Bas** | 0.63" | 0.69" | A definir | A definir |
| **Tableau 1** | 17L x 3C (metadonnees) | 1L x 2C (numeros) | A definir | A definir |
| **Tableau 2** | 1L x 1C (vide) | 15L x 3C (metadonnees) | A definir | A definir |
| **"Date decision"** | OUI | NON | A verifier | A verifier |
| **Titre** | "TRANSCRIPTION DES Motifs..." | "Transcription complete..." | A definir | A definir |
| **Page couverture** | Fournie (.docx) | Fournie (.docx) | GENEREE (template) | A verifier |
| **Statut implementation** | Implemente | En cours | A faire | A faire |

## Participants par Type

### SPR / RPD
- **COMMISSAIRE** (seul locuteur dans MOTIFS)

### SAR / RAD
- COMMISSAIRE(S) (1-3)
- DEMANDEUR / APPELANT
- CONSEIL du demandeur
- REPRESENTANT DU MINISTRE
- INTERPRETE (si applicable)

### SI / ID
- COMMISSAIRE
- PERSONNE CONCERNEE
- CONSEIL
- REPRESENTANT DU MINISTRE
- INTERPRETE (si applicable)

### SAI / IAD
- COMMISSAIRE
- APPELANT
- CONSEIL de l'appelant
- REPRESENTANT DU MINISTRE
- INTERPRETE (si applicable)

## Convention Nomenclature Fichiers

### SPR
`MC[1-4]-xxxxx SPR.61.01 - Page couverture.docx`
`MC[1-4]-xxxxx_transcription_YYYYMMDD.docx`

### SAR
`MC5-xxxxx Irb 101.41 Page couverture transcription.docx`
`MC5-xxxxx_transcription_YYYYMMDD.docx`

### SI
`0018-Cx-xxxxx - Page couverture.docx` (GENEREE depuis template)

## Bloqueurs Production par Type

### SPR -- PRET
- [x] Marges SPR (0.50" L/R)
- [x] Tableaux metadonnees SPR (17L x 3C)
- [x] Extraction MOTIFS (patterns regex)
- [x] Titre SPR
- [x] Pipeline E2E teste

### SAR -- EN COURS
- [ ] Marges SAR (1.00" L/R)
- [ ] Tableaux metadonnees SAR (structure inversee)
- [ ] Titre SAR ("Transcription complete...")
- [ ] Validation metadonnees SAR (absence "Date decision" = OK)
- [ ] Mapping locuteurs SAR (4-6 locuteurs)
- [ ] Diarization multi-locuteurs
- [ ] Test E2E SAR
- **Estimation** : ~7 heures developpement

### SI -- A FAIRE
- [ ] Generation page couverture depuis template
- [ ] Detection numero 0018-Cx
- [ ] Format specifique SI
- [ ] Test E2E SI

### SAI -- A FAIRE
- [ ] Echantillon document SAI requis
- [ ] Format a determiner
