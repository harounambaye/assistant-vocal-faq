"""Tests du contrat avec des faux modules : tournent sans GPU, sans internet, en < 1 s."""
from __future__ import annotations

from faq_assistant.config import MSG_NO_SPEECH, MSG_UNKNOWN, MSG_URGENT
from faq_assistant.pipeline import Pipeline
from faq_assistant.types import Match, Transcript


class FakeASR:
    def __init__(self, t: Transcript):
        self.t = t

    def transcribe(self, audio_path):
        return self.t


class FakeRetriever:
    def __init__(self, score):
        self.score = score

    def search(self, query, k=3):
        return Match("Q05", "Comment connaître le crédit ?", "Tapez 801.", self.score)


class FakeTTS:
    def synthesize_stream(self, text):
        yield "phrase1.mp3"


class BrokenRewriter:
    def rewrite(self, question, match, timeout_s):
        raise TimeoutError("API lente")


def run(transcript, score=0.95, rewriter=None):
    p = Pipeline(FakeASR(transcript), FakeRetriever(score), FakeTTS(), rewriter)
    *_, (_, reply) = list(p.run_stream("x.wav"))
    return reply


def speech(text):
    return Transcript(text=text, duration_s=2.0)


def test_ok():
    r = run(speech("ñaata kilowatt moo ma des"))
    assert r.status == "ok" and r.text == "Tapez 801."
    assert r.timings.total_ms >= r.timings.asr_ms


def test_silence():
    assert run(Transcript(text="", duration_s=0.0)).text == MSG_NO_SPEECH


def test_low_similarity_says_unknown():
    assert run(speech("quel temps fait-il à Thiès"), score=0.2).text == MSG_UNKNOWN


def test_urgent_bypasses_search():
    assert run(speech("il y a un fil électrique tombé devant chez moi")).text == MSG_URGENT


def test_llm_failure_falls_back_to_faq():
    r = run(speech("combien il me reste"), rewriter=BrokenRewriter())
    assert r.status == "ok" and r.text == "Tapez 801."


class FixedRewriter:
    def __init__(self, text):
        self.text = text

    def rewrite(self, question, match, timeout_s):
        return self.text


def test_good_rewrite_is_spoken():
    r = run(speech("combien il me reste"), rewriter=FixedRewriter("Il suffit de taper 801."))
    assert r.status == "ok" and r.text == "Il suffit de taper 801."


def test_invented_number_falls_back_to_faq():
    r = run(speech("combien il me reste"), rewriter=FixedRewriter("Tapez 810."))
    assert r.status == "ok" and r.text == "Tapez 801."


def run_text(text, score=0.95):
    p = Pipeline(FakeASR(Transcript(text="ne doit pas servir")), FakeRetriever(score), FakeTTS())
    *_, (_, reply) = list(p.run_text_stream(text))
    return reply


def test_typed_question_skips_asr():
    r = run_text("  comment voir mon crédit  ")
    assert r.status == "ok" and r.transcript.text == "comment voir mon crédit"


def test_empty_typed_question_is_not_heard():
    assert run_text("   ").text == MSG_NO_SPEECH


def test_typed_emergency():
    assert run_text("il y a des étincelles sur le compteur").text == MSG_URGENT
