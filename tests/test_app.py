"""Affichage de l'app : fonctions pures, testées sans Gradio ni modèle."""
from __future__ import annotations

import sys
from pathlib import Path

# app.py est à la racine du dépôt, hors de src/ : on ajoute la racine au chemin.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import (  # noqa: E402
    answer_events,
    load_questions,
    render_latencies,
    render_match,
    render_transcript,
    warm_up,
)
from faq_assistant.types import AssistantReply, Match, StageTimings, Transcript  # noqa: E402

QUESTIONS = {"Q05": "Comment connaître le crédit ?", "Q06": "Comment lire la consommation ?"}


def reply(status="ok", score=0.91, alternatives=(("Q06", 0.70),), text="sama crédit"):
    match = Match("Q05", QUESTIONS["Q05"], "Tapez 801.", score, list(alternatives))
    return AssistantReply(Transcript(text=text), match, "Tapez 801.", status,
                          StageTimings(asr_ms=420, retrieval_ms=12.4, total_ms=900))


def test_load_questions_covers_the_faq():
    assert len(load_questions()) == 30


def test_transcript():
    assert "« sama crédit »" in render_transcript(reply())
    assert "(rien)" in render_transcript(reply(text="  "))


def test_match_shows_id_score_and_alternatives():
    md = render_match(reply(), QUESTIONS)
    assert "Q05" in md and "0.91" in md and "Q06 (0.70)" in md
    assert "Vouliez-vous" not in md


def test_close_alternative_is_offered():
    md = render_match(reply(score=0.91, alternatives=[("Q06", 0.90)]), QUESTIONS)
    assert "Vouliez-vous plutôt dire : **Comment lire la consommation ?**" in md


def test_unknown_shows_candidate_under_threshold():
    assert "sous le seuil" in render_match(reply(status="unknown", score=0.40), QUESTIONS)


def test_urgent_without_match():
    r = AssistantReply(Transcript(text="fil tombé"), None, "…", "urgent", StageTimings())
    assert "Urgence" in render_match(r, QUESTIONS)


def test_latency_table():
    md = render_latencies(reply())
    assert "| ASR | 420 ms |" in md and "| Recherche | 12 ms |" in md
    assert "| LLM | — |" in md  # étape non exécutée


def test_answer_events_turns_each_chunk_into_screen_updates():
    r = reply()
    events = list(answer_events([("p1.mp3", r), (None, r)], QUESTIONS))
    assert [e[0] for e in events] == ["p1.mp3", None]
    audio, heard, match, answer, latencies = events[-1]
    assert "sama crédit" in heard and "Q05" in match
    assert answer == "**Réponse :** Tapez 801." and "| Étape |" in latencies


class _BrokenASR:
    def transcribe(self, audio_path):
        raise NotImplementedError("ASR pas encore mergé")


class _FakeTTS:
    def synthesize_stream(self, text):
        yield "p1.mp3"


class _FakeRetriever:
    def search(self, query, k=3):
        return Match("Q05", QUESTIONS["Q05"], "Tapez 801.", 0.95)


def test_warm_up_never_blocks_startup():
    from faq_assistant.pipeline import Pipeline

    p = Pipeline(_BrokenASR(), _FakeRetriever(), _FakeTTS())
    report = warm_up({False: p, True: p}, llm_ok=False)
    assert report["texte (recherche, LLM, TTS)"].startswith("ok")
    assert report["audio (ASR)"].startswith("error")  # signalé, sans plantage
