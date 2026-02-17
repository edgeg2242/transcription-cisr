"""Tests pour le parser Excel du workflow 0."""

import pytest
from unittest.mock import patch, MagicMock
from src.workflow_0_preparation.excel_parser import parser_excel_work_order


class TestExcelParser:
    """Tests du parser Excel."""

    def test_parser_returns_dict(self):
        """Le parser doit retourner un dictionnaire."""
        # Ce test vérifie la signature. Un vrai test nécessite un fichier Excel.
        # Placeholder pour quand les fixtures Excel seront disponibles.
        pass

    def test_parser_raises_on_missing_file(self):
        """Le parser doit lever une erreur si le fichier n'existe pas."""
        with pytest.raises(Exception):
            parser_excel_work_order("/chemin/inexistant.xlsx")
