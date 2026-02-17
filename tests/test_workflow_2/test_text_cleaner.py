"""Tests pour le nettoyage de texte du workflow 2."""

import pytest
from src.workflow_2_post_traitement.text_cleaner import (
    extraire_texte_integral,
    extraire_interventions_par_locuteur,
    nettoyer_texte,
    extraire_section_motifs,
)


class TestExtraireTexteIntegral:
    """Tests pour l'extraction du texte intégral."""

    def test_extraction_section_standard(self, sample_transcription_brute):
        """Doit extraire le texte entre les marqueurs."""
        texte = extraire_texte_integral(sample_transcription_brute)
        assert "examiner la demande d'asile" in texte
        assert "LOCUTEUR A" not in texte

    def test_fallback_si_pas_de_marqueurs(self):
        """Doit retourner tout le contenu si marqueurs absents."""
        texte_simple = "Ceci est un texte simple sans marqueurs."
        result = extraire_texte_integral(texte_simple)
        assert result == texte_simple


class TestExtraireInterventions:
    """Tests pour l'extraction des interventions par locuteur."""

    def test_extraction_locuteur(self, sample_transcription_brute):
        """Doit extraire les interventions par locuteur."""
        interventions = extraire_interventions_par_locuteur(sample_transcription_brute)
        assert 'A' in interventions
        assert "examiner la demande" in interventions['A']


class TestNettoyerTexte:
    """Tests pour le nettoyage du texte."""

    def test_supprime_tics(self, sample_dictionnaire):
        """Doit supprimer les tics de langage."""
        texte = "Euh donc il a dit euh que oui"
        result = nettoyer_texte(texte, sample_dictionnaire)
        assert "Euh" not in result
        assert "euh" not in result

    def test_supprime_repetitions(self, sample_dictionnaire):
        """Doit supprimer les répétitions immédiates."""
        texte = "il a a dit que le le problème"
        result = nettoyer_texte(texte, sample_dictionnaire)
        assert "a a" not in result
        assert "le le" not in result

    def test_preserve_contenu(self, sample_dictionnaire):
        """Doit préserver le contenu substantiel."""
        texte = "La demande d'asile est accueillie."
        result = nettoyer_texte(texte, sample_dictionnaire)
        assert "demande d'asile" in result


class TestExtraireMotifs:
    """Tests pour l'extraction de la section MOTIFS."""

    def test_trouve_motifs_avec_pattern(self):
        """Doit trouver le début des MOTIFS avec un pattern standard."""
        texte = (
            "Introduction... "
            "Voici les motifs de ma décision. "
            "Le demandeur est crédible. "
            "L'audience est terminée."
        )
        result = extraire_section_motifs(texte)
        assert result is not None
        assert "motifs de ma décision" in result

    def test_retourne_none_sans_motifs(self):
        """Doit retourner None si aucun pattern MOTIFS trouvé."""
        texte = "Ceci est un texte sans section motifs."
        result = extraire_section_motifs(texte)
        assert result is None
