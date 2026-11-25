"""Détection des cas particuliers avant la recherche. PROPRIÉTAIRE : Fatou.

TODO Fatou :
- compléter URGENT_PATTERNS (français + wolof) à partir des essais oraux ;
- ajouter is_greeting() / is_out_of_domain() si les tests le justifient ;
- chaque motif ajouté = un test dans tests/test_guardrails.py.
"""
from __future__ import annotations

import re
import unicodedata

URGENT_PATTERNS = [
    r"\bfils?\b.{0,20}\b(tomb|par terre|arrach|dénud)",
    r"\b(étincelles?|etincelles?|courts?[- ]circuits?|fum[ée]es?|incendies?|feu)\b",
    r"\b(électrocut|electrocut|choc électrique|choc electrique)",
    r"\b(safara|lakk)\b",  # wolof : feu / brûler
]
_URGENT_RE = re.compile("|".join(URGENT_PATTERNS), re.IGNORECASE)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def is_urgent(text: str) -> bool:
    return bool(_URGENT_RE.search(normalize(text)))
