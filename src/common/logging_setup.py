"""
Configuration logging et fix encodage UTF-8 Windows.

Appeler fix_utf8_windows() au début de chaque script/module.
Appeler setup_logging() pour configurer le logger avec sortie fichier + console.
"""
import sys
import io
import logging
from pathlib import Path
from datetime import datetime


def fix_utf8_windows():
    """
    Corrige l'encodage de la console Windows (CP1252 → UTF-8).
    Évite UnicodeEncodeError sur les caractères spéciaux et emojis.
    Appeler au début de chaque script.
    """
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )


def setup_logging(
    name: str = __name__,
    log_dir: Path | None = None,
    workflow_name: str = "pipeline",
) -> logging.Logger:
    """
    Configure le logging avec sortie console + fichier optionnel.

    Args:
        name: Nom du logger (typiquement __name__).
        log_dir: Dossier pour le fichier .log. Si None, console seulement.
        workflow_name: Préfixe du fichier log.

    Returns:
        Logger configuré.
    """
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{workflow_name}_{timestamp}.log"
        handlers.append(
            logging.FileHandler(log_file, encoding="utf-8")
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return logging.getLogger(name)
