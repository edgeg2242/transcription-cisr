# Referentiels Gold Standard -- Transcription CISR

## Objectif

Ce dossier contient des transcriptions humaines validees (gold standard) pour chaque type de document CISR. Ces referentiels servent a :

- Comparer les resultats du pipeline automatise vs transcriptions humaines
- Enrichir le dictionnaire de corrections par analyse des ecarts
- Valider le formatage Word (marges, tableaux, polices) par type
- Mesurer l'evolution de la qualite du pipeline au fil du temps

## Structure

```
referentiels/
├── README.md          (ce fichier)
├── spr/               SPR (Section Protection des Refugies / RPD)
│   └── MC3-xxxxx/     Chaque sous-dossier contient:
│       ├── audio/     Fichier(s) audio source (.a00 ou .mp3)
│       └── final/     Transcription humaine finale (.docx)
├── sar/               SAR (Section d'Appel des Refugies / RAD)
│   └── MC5-xxxxx/
│       ├── audio/
│       └── final/
└── si/                SI (Section de l'Immigration / ID)
    └── 0018-Cx-xxxxx/
        ├── audio/
        └── final/
```

## Selection des Referentiels

### Criteres de selection

- Transcription humaine validee et livree au client
- Audio source disponible et de qualite correcte
- Representativite: variete de commissaires, durees, complexites
- Couvrir les cas typiques ET les cas limites

### Source

Les referentiels proviennent du dossier principal:
`C:\Users\felix\OneDrive\Documents\.Work\Traduction\Referentiels`
(832 fichiers, 502 transcriptions DOCX, 155 audio .a00, 65 Work Assignments)

### Selection recommandee

| Type | Dossier | Justification |
|------|---------|---------------|
| SPR | MC3-03924 (Victoria) | Premier cas teste, reference pipeline |
| SPR | MC3-16722 | Multi-WO teste, variete commissaire |
| SPR | MC2-29598 | Numero MC2, variete format |
| SAR | MC5-40476 | Audience complete multi-locuteurs |
| SAR | MC5-40324 | Variete structure SAR |
| SI | 0018-C5-00248-02 | Type le moins implemente |

## Utilisation

### Avec /validation-qualite

```
/validation-qualite mon_resultat.docx SPR
```

Le skill cherchera automatiquement le referentiel correspondant dans ce dossier.

### Avec /enrichissement-dictionnaire

```
/enrichissement-dictionnaire transcription_brute.txt referentiels/spr/MC3-03924/final/transcription.docx
```

### Avec /learning-loop

Le skill analyse automatiquement tous les referentiels disponibles pour mesurer la progression globale.

## Convention de nommage

Chaque referentiel doit contenir au minimum:

- **audio/** : Le fichier audio source original (format .a00 ou .mp3)
- **final/** : La transcription humaine finale au format .docx

Les fichiers audio volumineux (.a00, .mp3) ne doivent PAS etre versionnes dans git.
Ajouter au .gitignore: `referentiels/**/*.a00`, `referentiels/**/*.mp3`

## Ajout d'un nouveau referentiel

1. Creer le sous-dossier: `referentiels/<type>/<numero_dossier>/`
2. Copier l'audio source dans `audio/`
3. Copier la transcription finale validee dans `final/`
4. Mettre a jour ce README avec la justification du choix
5. Executer `/validation-qualite` pour verifier que le pipeline produit un resultat comparable
