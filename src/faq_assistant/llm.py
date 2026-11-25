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

import os

from .config import SETTINGS
from .types import Match

SYSTEM = (
    "Tu es l'assistant vocal du service client Senelec pour le compteur Woyofal. "
    "On te donne la question d'un client (transcrite, parfois mêlée de wolof) et la réponse "
    "officielle de la FAQ. Reformule la réponse officielle en une à trois phrases courtes, "
    "en français simple, à l'oral, en t'adressant au client par « vous ». "
    "N'ajoute AUCUNE information absente de la réponse officielle : ni chiffre, ni démarche, "
    "ni numéro. Pas de liste, pas de markdown, pas de formule de politesse."
)


class ClaudeRewriter:
    def __init__(self):
        import anthropic  # import tardif : l'app tourne sans la dépendance si USE_LLM=0
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=0)

    def rewrite(self, question: str, match: Match, timeout_s: float) -> str:
        msg = self.client.messages.create(
            model=SETTINGS.llm_model,
            max_tokens=SETTINGS.llm_max_tokens,
            system=SYSTEM,
            messages=[{"role": "user", "content":
                       f"Question du client : {question}\nRéponse officielle : {match.answer}"}],
            timeout=timeout_s,
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
