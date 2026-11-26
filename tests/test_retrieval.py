"""Tests de la recherche, avec un faux encodeur : sans GPU, sans internet, sans modèle."""
from __future__ import annotations

import zlib

import pytest

np = pytest.importorskip("numpy")  # la CI légère n'installe pas numpy : ces tests sont alors sautés

from faq_assistant.config import SETTINGS  # noqa: E402
from faq_assistant.retrieval import BM25, FaqRetriever, mots_cles, normaliser_requete  # noqa: E402


class FauxEncodeur:
    """Sac de mots haché : deux textes qui partagent des mots ont des vecteurs proches."""

    def __init__(self, dimension: int = 512):
        self.dimension, self.appels = dimension, 0

    def __call__(self, textes):
        self.appels += 1
        vecteurs = np.zeros((len(textes), self.dimension))
        for ligne, texte in enumerate(textes):
            for mot in mots_cles(texte.split(": ", 1)[-1]):
                vecteurs[ligne, zlib.crc32(mot.encode()) % self.dimension] += 1.0
        normes = np.linalg.norm(vecteurs, axis=1, keepdims=True)
        return vecteurs / np.where(normes == 0, 1, normes)


@pytest.fixture(scope="module")
def recherche():
    return FaqRetriever(SETTINGS.faq_path, encodeur=FauxEncodeur())


def test_normalisation_retire_hesitations_et_corrige_asr():
    assert normaliser_requete("Euh, bon, mon WOYO FALL de la Sénélec") == "mon woyofal de la senelec"


def test_mots_cles_sans_accents_ni_mots_vides():
    assert mots_cles("Où acheter du crédit Woyofal ?") == ["acheter", "credit", "woyofal"]


def test_bm25_prefere_le_document_qui_contient_le_mot():
    scores = BM25([["compteur", "bip"], ["credit", "acheter"]]).scores(["bip"])
    assert scores[0] > 0 and scores[1] == 0


def test_bm25_hors_sujet_reste_faible():
    bm25 = BM25([["compteur", "bip"], ["credit", "acheter"]])
    mots = ["temps", "demain", "thies"]
    assert max(bm25.scores(mots)) / bm25.score_maximal(mots) == 0


def test_question_exacte(recherche):
    match = recherche.search("Comment connaître le crédit qui me reste ?")
    assert match.faq_id == "Q05" and match.score > 0.75


def test_exemple_wolof(recherche):
    assert recherche.search("sama compteur dafa sonner").faq_id == "Q11"


def test_hesitations_et_graphie_asr(recherche):
    assert recherche.search("euh où est-ce que je peux acheter woyo fall").faq_id == "Q01"


def test_alternatives_triees(recherche):
    match = recherche.search("comment recharger mon compteur avec le code", k=3)
    assert len(match.alternatives) == 2
    scores = [match.score] + [s for _, s in match.alternatives]
    assert scores == sorted(scores, reverse=True)


def test_hors_sujet_score_plus_bas(recherche):
    dans_la_faq = recherche.search("pourquoi mon crédit woyofal finit vite").score
    hors_sujet = recherche.search("quel temps fera-t-il demain à Thiès").score
    assert hors_sujet < dans_la_faq


def test_requete_vide(recherche):
    assert recherche.search("  euh  ") is None
