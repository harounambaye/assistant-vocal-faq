"""Contrats partagés entre les modules. PROPRIÉTAIRE : Harouna (LeadTech).

Ce fichier est le « contrat » de l'équipe : chacun code son module contre ces
types. Toute modification passe par une PR dédiée validée par le LeadTech,
jamais au milieu d'une PR de fonctionnalité (c'est la source n°1 de conflits).
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Transcript:
    text: str                      # texte reconnu, déjà nettoyé (strip)
    language: str = "fr"           # langue détectée
    avg_logprob: float = 0.0       # confiance moyenne Whisper
    no_speech_prob: float = 0.0    # probabilité « pas de parole »
    duration_s: float = 0.0        # durée de l'audio utile (après VAD)


@dataclass
class Match:
    faq_id: str                    # ex. "Q04"
    question: str
    answer: str
    score: float                   # similarité finale dans [0, 1]
    alternatives: list[tuple[str, float]] = field(default_factory=list)  # (faq_id, score) suivants


@dataclass
class StageTimings:
    asr_ms: float = 0.0
    retrieval_ms: float = 0.0
    llm_ms: float = 0.0
    tts_first_audio_ms: float = 0.0   # temps jusqu'au 1er morceau audio (latence perçue)
    tts_total_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class AssistantReply:
    transcript: Transcript
    match: Match | None
    text: str                      # texte effectivement prononcé
    status: str                    # "ok" | "unknown" | "no_speech" | "urgent" | "error"
    timings: StageTimings
    audio_path: str | None = None


# ---- Interfaces que chaque module DOIT respecter ---------------------------

class ASR(Protocol):               # Papa — src/faq_assistant/asr.py
    def transcribe(self, audio_path: str) -> Transcript: ...


class Retriever(Protocol):         # Fatou — src/faq_assistant/retrieval.py
    def search(self, query: str, k: int = 3) -> Match | None: ...


class Rewriter(Protocol):          # Harouna — src/faq_assistant/llm.py
    def rewrite(self, question: str, match: Match, timeout_s: float) -> str: ...


class TTS(Protocol):               # Papa — src/faq_assistant/tts.py
    def synthesize_stream(self, text: str) -> Iterator[str]:
        """Produit un chemin de fichier audio par phrase, dès qu'il est prêt."""
        ...
