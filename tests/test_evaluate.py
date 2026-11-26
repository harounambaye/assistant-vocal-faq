"""Tests de l'évaluation, avec un faux pipeline : sans audio, sans modèle."""
from __future__ import annotations

from eval.evaluate import Resultat, balayage, ecrire_csv, evaluer_une, lire_labels, resume
from faq_assistant.types import AssistantReply, Match, StageTimings, Transcript


class FauxPipeline:
    """Renvoie une réponse préparée à l'avance pour chaque fichier."""

    def __init__(self, reponses):
        self.reponses = reponses

    def run_stream(self, audio_path):
        statut, faq_id, score = self.reponses[audio_path.split("/")[-1].split("\\")[-1]]
        match = Match(faq_id, "q", "r", score) if faq_id else None
        timings = StageTimings(asr_ms=500, retrieval_ms=20, tts_first_audio_ms=300, total_ms=900)
        yield None, AssistantReply(Transcript("texte"), match, "réponse", statut, timings)


def resultat(attendu, statut, faq_proche, score):
    obtenu = {"ok": faq_proche, "unknown": "NONE"}.get(statut, statut.upper())
    return Resultat("f", "L1", attendu, obtenu, statut, faq_proche, score, "t",
                    {"asr_ms": 500, "retrieval_ms": 20, "llm_ms": 0, "tts_first_audio_ms": 300,
                     "total_ms": 900})


def test_lire_labels(tmp_path):
    fichier = tmp_path / "labels.csv"
    fichier.write_text("fichier,locuteur,faq_id_attendu,remarque\nd01.ogg,L1,Q05,wolof\n", encoding="utf-8")
    assert lire_labels(fichier) == [{"fichier": "d01.ogg", "locuteur": "L1",
                                     "faq_id_attendu": "Q05", "remarque": "wolof"}]


def test_evaluer_une_bonne_reponse_et_je_ne_sais_pas(tmp_path):
    pipeline = FauxPipeline({"a.ogg": ("ok", "Q05", 0.8), "b.ogg": ("unknown", "Q12", 0.5)})
    bonne = evaluer_une(pipeline, {"fichier": "a.ogg", "locuteur": "L1", "faq_id_attendu": "Q05"}, tmp_path)
    nsp = evaluer_une(pipeline, {"fichier": "b.ogg", "locuteur": "L1", "faq_id_attendu": "none"}, tmp_path)
    assert bonne.correct and bonne.obtenu == "Q05"
    assert nsp.correct and nsp.obtenu == "NONE" and nsp.faq_proche == "Q12"


def test_urgence_comptee_a_part(tmp_path):
    pipeline = FauxPipeline({"c.ogg": ("urgent", "", 0.0)})
    r = evaluer_une(pipeline, {"fichier": "c.ogg", "locuteur": "L2", "faq_id_attendu": "Q29"}, tmp_path)
    assert r.obtenu == "URGENT" and not r.correct


def test_resume_taux_et_je_ne_sais_pas():
    resultats = [resultat("Q05", "ok", "Q05", 0.8), resultat("Q22", "unknown", "Q22", 0.6),
                 resultat("NONE", "unknown", "Q02", 0.55), resultat("Q11", "ok", "Q26", 0.7)]
    bilan = resume(resultats)
    assert bilan["taux_bonnes_reponses"] == 0.5
    assert bilan["je_ne_sais_pas_corrects"] == "1/1"
    assert bilan["je_ne_sais_pas_a_tort"] == "1/3"
    assert bilan["erreurs"][("Q11", "Q26")] == 1
    assert bilan["latences_mediane_p90_ms"]["asr_ms"] == (500, 500)


def test_balayage_sans_relancer_asr():
    resultats = [resultat("Q05", "ok", "Q05", 0.70), resultat("NONE", "ok", "Q02", 0.62)]
    taux = dict(balayage(resultats, [0.60, 0.65, 0.75]))
    assert taux[0.60] == 0.5     # le hors-sujet passe : faux positif
    assert taux[0.65] == 1.0     # le bon seuil sépare les deux
    assert taux[0.75] == 0.5     # trop strict : la bonne réponse devient « je ne sais pas »


def test_ecrire_csv(tmp_path):
    sortie = tmp_path / "results.csv"
    ecrire_csv([resultat("Q05", "ok", "Q05", 0.8)], sortie)
    lignes = sortie.read_text(encoding="utf-8").splitlines()
    assert lignes[0].startswith("fichier,locuteur,attendu,obtenu,correct")
    assert lignes[1].startswith("f,L1,Q05,Q05,1,ok,Q05,0.8")
