"""Contrôle « le LLM n'invente aucun chiffre » : tourne sans clé API ni internet."""
from __future__ import annotations

from faq_assistant.llm import extract_numbers, numbers_are_grounded

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
