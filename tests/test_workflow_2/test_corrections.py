"""Tests pour le pipeline de corrections intelligentes."""

import pytest
from src.workflow_2_post_traitement.corrections import (
    pass1_termes_juridiques,
    pass4_mots_mal_reconnus,
    pass6_qa_finale,
    pipeline_corrections_intelligentes,
)


class TestPass1TermesJuridiques:
    """Tests Pass 1 : Termes juridiques."""

    def test_correction_article(self, sample_dictionnaire):
        """Doit corriger les articles de loi."""
        texte = "Selon article 87 de la LIPR"
        result, corrections = pass1_termes_juridiques(texte, sample_dictionnaire)
        assert "article 96" in result
        assert len(corrections) == 1

    def test_correction_expression(self, sample_dictionnaire):
        """Doit corriger les expressions juridiques."""
        texte = "en virtu de la loi"
        result, corrections = pass1_termes_juridiques(texte, sample_dictionnaire)
        assert "en vertu" in result

    def test_pas_de_correction_si_dict_vide(self):
        """Ne doit pas crasher avec dictionnaire vide."""
        texte = "article 87"
        result, corrections = pass1_termes_juridiques(texte, {})
        assert result == texte
        assert corrections == []


class TestPass4MotsMalReconnus:
    """Tests Pass 4 : Mots mal reconnus."""

    def test_remplacement_exact(self, sample_dictionnaire):
        """Doit faire un remplacement exact (case-sensitive)."""
        texte = "Le diagnostic montre affairement"
        result, corrections = pass4_mots_mal_reconnus(texte, sample_dictionnaire)
        assert "avortement" in result


class TestPass6QAFinale:
    """Tests Pass 6 : QA finale."""

    def test_score_sans_corrections(self):
        """Score 100 sans corrections."""
        rapport = pass6_qa_finale("texte", "texte", [])
        assert rapport['qualite']['score'] == 100
        assert rapport['qualite']['niveau'] == 'EXCELLENT'

    def test_score_avec_corrections_critiques(self):
        """Score diminue avec corrections critiques (pass 1 + 4)."""
        corrections = [
            {'pass': 1, 'type': 'terme_juridique'},
            {'pass': 4, 'type': 'mot_mal_reconnu'},
        ]
        rapport = pass6_qa_finale("texte corrigé", "texte original", corrections)
        assert rapport['qualite']['score'] == 96  # 100 - (2 * 2)


class TestPipeline:
    """Tests du pipeline complet."""

    def test_pipeline_retourne_tuple(self, sample_dictionnaire, sample_metadata):
        """Le pipeline doit retourner (texte, rapport)."""
        texte, rapport = pipeline_corrections_intelligentes(
            "Texte de test", sample_metadata, sample_dictionnaire
        )
        assert isinstance(texte, str)
        assert isinstance(rapport, dict)
        assert 'qualite' in rapport
