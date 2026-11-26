"""Reformulation courte de la réponse par Claude. PROPRIÉTAIRE : Harouna.

Le LLM ne fait QUE reformuler la réponse de la FAQ pour coller à la question posée.
Il n'invente aucune information : s'il n'y a rien à adapter, il renvoie la réponse telle quelle.

- Modèle : claude-haiku-5-5 (le moins cher et le plus rapide ; une requête coûte une
  fraction de centime, donc les 100 $ suffisent largement — fixer quand même une limite de
  dépense dans la console).
- Clé : variable d'environnement ANTHROPIC_API_KEY (secret Colab). JAMAIS dans le dépôt.
- Timeout strict + aucune nouvelle tentative : en cas d'échec, le pipeline lit la FAQ brute.
"""
from __future__ import annotations

import re

from .config import SETTINGS
from .types import Match

# Espaces (normal, insécable, fine insécable) entre deux chiffres : « 4 689 » -> « 4689 »
_DIGIT_GAP = re.compile(r"(?<=\d)[   ](?=\d)")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def extract_numbers(text: str) -> set[str]:
    """Nombres écrits en chiffres, sous une forme comparable (« 136,49 » == « 136.49 »)."""
    return {n.replace(",", ".") for n in _NUMBER.findall(_DIGIT_GAP.sub("", text))}


def numbers_are_grounded(rewritten: str, faq_answer: str) -> bool:
    """Vrai si chaque nombre de la reformulation figure déjà dans la réponse FAQ."""
    return extract_numbers(rewritten) <= extract_numbers(faq_answer)

SYSTEM = (
    "Tu es l'assistant vocal du service client Senelec pour le compteur Woyofal. "
    "On te donne la question d'un client (transcrite, parfois mêlée de wolof) et la réponse "
    "officielle de la FAQ. Reformule la réponse officielle en une à trois phrases courtes, "
    "en français simple, à l'oral, en t'adressant au client par « vous ». "
    "N'ajoute AUCUNE information absente de la réponse officielle : ni chiffre, ni démarche, "
    "ni numéro. Pas de liste, pas de markdown, pas de formule de politesse."
)


class ClaudeRewriter:
    def __init__(self, client=None):
        if client is None:
            import anthropic  # import tardif : l'app tourne sans la dépendance si USE_LLM=0
            client = anthropic.Anthropic(max_retries=0)  # lit ANTHROPIC_API_KEY (secret Colab)
        self.client = client

    def rewrite(self, question: str, match: Match, timeout_s: float) -> str:
        msg = self.client.with_options(timeout=timeout_s, max_retries=0).messages.create(
            model=SETTINGS.llm_model,
            max_tokens=SETTINGS.llm_max_tokens,
            # Haiku 5.5 réfléchit par défaut : la réflexion mangerait les 160 tokens et la latence.
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=SYSTEM,
            messages=[{"role": "user", "content":
                       f"Question du client : {question}\nRéponse officielle : {match.answer}"}],
        )
        # Phrase coupée ou refus : le pipeline attrape l'erreur et lit la FAQ brute.
        if msg.stop_reason != "end_turn":
            raise RuntimeError(f"reformulation inutilisable (stop_reason={msg.stop_reason})")
        return "".join(b.text for b in msg.content if b.type == "text").strip()
