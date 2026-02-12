#!/usr/bin/env python3
"""
Installation automatique de FFmpeg portable pour Windows
Télécharge et extrait FFmpeg dans le dossier ffmpeg_portable/
"""
import sys
import os
import hashlib
import urllib.request
import zipfile
from pathlib import Path

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# URL FFmpeg Windows build (version stable)
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_DIR = Path("ffmpeg_portable")
FFMPEG_ZIP = FFMPEG_DIR / "ffmpeg.zip"

print("=" * 80)
print("INSTALLATION FFMPEG PORTABLE")
print("=" * 80)
print()

# Créer dossier
FFMPEG_DIR.mkdir(exist_ok=True)

# Télécharger FFmpeg
if not FFMPEG_ZIP.exists():
    print(f"Téléchargement FFmpeg depuis {FFMPEG_URL}")
    print("Cela peut prendre 2-5 minutes (environ 80 MB)...")
    print()

    try:
        urllib.request.urlretrieve(FFMPEG_URL, FFMPEG_ZIP)
        size_mb = FFMPEG_ZIP.stat().st_size / (1024 * 1024)
        print(f"Téléchargement terminé : {size_mb:.2f} MB")
        print()
    except Exception as e:
        print(f"ERREUR téléchargement : {e}")
        sys.exit(1)

    # Vérification SHA256 du fichier téléchargé
    # TODO: Remplacer par le hash SHA256 connu de la version FFmpeg attendue
    # pour garantir l'intégrité du binaire téléchargé.
    # WARNING: Sans hash connu, le binaire n'est PAS vérifié cryptographiquement.
    EXPECTED_SHA256 = None  # Ex: "a1b2c3d4..." — à remplir avec le hash officiel
    downloaded_hash = hashlib.sha256(open(FFMPEG_ZIP, 'rb').read()).hexdigest()
    print(f"SHA256 du fichier téléchargé : {downloaded_hash}")
    if EXPECTED_SHA256 is not None:
        if downloaded_hash != EXPECTED_SHA256:
            print(f"ERREUR : Hash SHA256 invalide !")
            print(f"  Attendu : {EXPECTED_SHA256}")
            print(f"  Obtenu  : {downloaded_hash}")
            FFMPEG_ZIP.unlink()
            sys.exit(1)
        print("SHA256 vérifié avec succès")
    else:
        print("WARNING: Aucun hash SHA256 de référence configuré — vérification manuelle requise")
    print()
else:
    print(f"Archive déjà téléchargée : {FFMPEG_ZIP}")
    print()

# Extraire ZIP (avec protection Zip Slip)
print("Extraction FFmpeg...")
try:
    with zipfile.ZipFile(FFMPEG_ZIP, 'r') as zip_ref:
        target = FFMPEG_DIR.resolve()
        for member in zip_ref.namelist():
            member_path = (target / member).resolve()
            if not str(member_path).startswith(str(target)):
                raise ValueError(f"Zip Slip détecté : chemin suspect '{member}'")
        zip_ref.extractall(FFMPEG_DIR)
    print("Extraction terminée")
    print()
except Exception as e:
    print(f"ERREUR extraction : {e}")
    sys.exit(1)

# Trouver ffmpeg.exe
ffmpeg_exe = None
for root, dirs, files in os.walk(FFMPEG_DIR):
    if 'ffmpeg.exe' in files:
        ffmpeg_exe = Path(root) / 'ffmpeg.exe'
        break

if not ffmpeg_exe:
    print("ERREUR : ffmpeg.exe non trouvé après extraction")
    sys.exit(1)

print(f"FFmpeg installé : {ffmpeg_exe}")
print()

# Tester FFmpeg
print("Test FFmpeg...")
import subprocess
result = subprocess.run([str(ffmpeg_exe), '-version'],
                       capture_output=True,
                       text=True,
                       timeout=10)

if result.returncode == 0:
    version_line = result.stdout.split('\n')[0]
    print(f"FFmpeg fonctionne : {version_line}")
    print()
else:
    print("ERREUR : FFmpeg ne fonctionne pas correctement")
    sys.exit(1)

# Ajouter au PATH (temporaire pour cette session)
ffmpeg_bin_dir = ffmpeg_exe.parent
os.environ['PATH'] = str(ffmpeg_bin_dir) + os.pathsep + os.environ['PATH']
print(f"FFmpeg ajouté au PATH : {ffmpeg_bin_dir}")
print()

print("=" * 80)
print("INSTALLATION RÉUSSIE")
print("=" * 80)
print()
print("Pour utiliser FFmpeg de manière permanente, ajoutez au PATH système :")
print(f"  {ffmpeg_bin_dir.absolute()}")
print()
print("Ou utilisez directement :")
print(f"  {ffmpeg_exe.absolute()}")
print()
