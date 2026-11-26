"""Détection des cas particuliers avant la recherche. PROPRIÉTAIRE : Fatou.

Une urgence (fil tombé, étincelles, fumée, choc électrique) déclenche la consigne de
sécurité AVANT toute recherche : elle ne doit jamais dépendre d'un score de similarité.
Chaque motif a son test dans tests/test_guardrails.py. Les motifs acceptent les mots
avec ou sans accents, car la transcription n'est pas toujours exacte.
"""
from __future__ import annotations

import re
import unicodedata

URGENT_PATTERNS = [
    # Fil ou câble électrique tombé, arraché ou dénudé (« le fil est tombé », « câble arraché »)
    r"\b(fils?|c[aâ]bles?)\b.{0,25}\b(tomb|par terre|au sol|arrach|d[ée]nud|coup[ée])",
    # Étincelles, court-circuit, fumée, incendie, feu, explosion
    r"\b([ée]tincelles?|courts?[- ]circuits?|fum[ée]es?|fume|incendies?|feu|explos)",
    # Odeur de brûlé ou appareil qui brûle (« ça sent le brûlé », « le compteur brûle »)
    r"\b(odeur de br[uû]l|sent le br[uû]l|[çc]a br[uû]le|compteur.{0,15}br[uû]l)",
    # Choc électrique (« électrocuté », « électrisé », « le courant m'a pris »)
    r"\b([ée]lectrocut|[ée]lectris|chocs? [ée]lectriques?)",
    r"\bcourant\b.{0,10}\bm'a (pris|secou|touch)",
    # Wolof : feu, brûler, fumée, fil tombé, le courant m'a attrapé
    r"\b(safara|lakk|saxaar)\b",
    r"\b(fil|c[aâ]ble)\b.{0,15}\bdaanu\b",
    r"\bcourant bi\b.{0,10}\bj[aà]pp\b",
]
_URGENT_RE = re.compile("|".join(URGENT_PATTERNS), re.IGNORECASE)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower()).replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def is_urgent(text: str) -> bool:
    return bool(_URGENT_RE.search(normalize(text)))
