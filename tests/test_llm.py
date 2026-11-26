"""Contrôle « le LLM n'invente aucun chiffre » : tourne sans clé API ni internet."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from faq_assistant.llm import ClaudeRewriter, extract_numbers, numbers_are_grounded
from faq_assistant.types import Match

FAQ = "Le prix est de 4 689 FCFA, soit 136,49 FCFA le kWh. Appelez le 33 867 66 66 ou tapez 801."


def test_extract_joins_thousands_and_decimals():
    assert extract_numbers("4 689 FCFA et 136,49") == {"4689", "136.49"}


def test_extract_ignores_sentence_final_dot():
    assert extract_numbers("Tapez 801.") == {"801"}


def test_same_numbers_written_differently_are_grounded():
    assert numbers_are_grounded("Ça coûte 4689 FCFA, tapez 801.", FAQ)
    assert numbers_are_grounded("Le kWh est à 136.49 FCFA.", FAQ)
    assert numbers_are_grounded("Appelez le 33 867 66 66.", FAQ)


def test_no_number_is_grounded():
    assert numbers_are_grounded("Rendez-vous en agence Senelec.", FAQ)


def test_invented_number_is_rejected():
    assert not numbers_are_grounded("Tapez 810.", FAQ)
    assert not numbers_are_grounded("Ça coûte 5 000 FCFA.", FAQ)


def test_wrong_phone_number_is_rejected():
    assert not numbers_are_grounded("Appelez le 33 867 66 67.", FAQ)


# ---- ClaudeRewriter avec un faux client (aucun appel réseau) -----------------
MATCH = Match("Q05", "Comment connaître le crédit ?", "Tapez 801.", 0.95)


class FakeClient:
    def __init__(self, text="Il suffit de taper 801.", stop_reason="end_turn"):
        self.text, self.stop_reason, self.calls = text, stop_reason, []

    def with_options(self, **opts):
        self.options = opts
        return self

    @property
    def messages(self):
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        block = SimpleNamespace(type="text", text=self.text)
        return SimpleNamespace(content=[block], stop_reason=self.stop_reason)


def test_rewrite_returns_text_without_thinking_and_with_timeout():
    client = FakeClient()
    text = ClaudeRewriter(client).rewrite("combien il me reste", MATCH, timeout_s=2.5)
    assert text == "Il suffit de taper 801."
    assert client.options == {"timeout": 2.5, "max_retries": 0}
    assert client.calls[0]["thinking"] == {"type": "disabled"}


@pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal"])
def test_truncated_or_refused_rewrite_raises(stop_reason):
    with pytest.raises(RuntimeError):
        ClaudeRewriter(FakeClient(stop_reason=stop_reason)).rewrite("q", MATCH, timeout_s=2.5)
