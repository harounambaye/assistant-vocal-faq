"""Orchestration micro -> ASR -> recherche -> (LLM) -> TTS. PROPRIÉTAIRE : Harouna.

Règle d'or : AUCUNE étape optionnelle ne peut faire échouer la réponse.
- LLM en panne / trop lent  -> on lit la réponse de la FAQ telle quelle.
- Similarité trop faible    -> « je ne sais pas » + numéro du service client.
- Silence / bruit           -> « je n'ai pas entendu ».
- Mot d'urgence             -> consigne de sécurité, avant toute recherche.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator

from . import guardrails
from .config import MSG_ERROR, MSG_NO_SPEECH, MSG_UNKNOWN, MSG_URGENT, SETTINGS
from .llm import numbers_are_grounded
from .types import ASR, TTS, AssistantReply, Match, Retriever, Rewriter, StageTimings, Transcript

log = logging.getLogger(__name__)


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000


class Pipeline:
    def __init__(self, asr: ASR, retriever: Retriever, tts: TTS, rewriter: Rewriter | None = None):
        self.asr, self.retriever, self.tts, self.rewriter = asr, retriever, tts, rewriter

    # --- étape texte (testable sans audio) ---------------------------------
    def answer_text(self, transcript: Transcript, timings: StageTimings) -> tuple[str, str, Match | None]:
        text = transcript.text.strip()
        if (not text or transcript.duration_s < SETTINGS.min_speech_s
                or transcript.no_speech_prob > SETTINGS.no_speech_threshold):
            return MSG_NO_SPEECH, "no_speech", None

        if guardrails.is_urgent(text):
            return MSG_URGENT, "urgent", None

        t0 = time.perf_counter()
        match = self.retriever.search(text, k=3)
        timings.retrieval_ms = _ms(t0)
        if match is None or match.score < SETTINGS.unknown_threshold:
            return MSG_UNKNOWN, "unknown", match

        reply = match.answer
        if SETTINGS.use_llm and self.rewriter is not None:
            t0 = time.perf_counter()
            try:
                reply = self.rewriter.rewrite(text, match, timeout_s=SETTINGS.llm_timeout_s) or match.answer
            except Exception as exc:  # réseau, quota, timeout : on retombe sur la FAQ
                log.warning("LLM indisponible, réponse FAQ brute : %s", exc)
                reply = match.answer
            if not numbers_are_grounded(reply, match.answer):
                log.warning("LLM a inventé un nombre, réponse FAQ brute : %r", reply)
                reply = match.answer
            timings.llm_ms = _ms(t0)
        return reply, "ok", match

    # --- bout en bout, en flux (Gradio joue chaque phrase dès qu'elle est prête)
    def run_stream(self, audio_path: str) -> Iterator[tuple[str | None, AssistantReply]]:
        return self._run(lambda: self.asr.transcribe(audio_path))

    def run_text_stream(self, text: str) -> Iterator[tuple[str | None, AssistantReply]]:
        """Question tapée au clavier : même chemin que l'audio, sans ASR (démo, plan B micro)."""
        # Durée fictive = durée minimale : une question tapée n'est jamais du « silence ».
        return self._run(lambda: Transcript(text=text.strip(), duration_s=SETTINGS.min_speech_s))

    def _run(self, transcribe: Callable[[], Transcript]) -> Iterator[tuple[str | None, AssistantReply]]:
        timings = StageTimings()
        t_start = time.perf_counter()
        transcript = Transcript(text="")
        try:
            t0 = time.perf_counter()
            transcript = transcribe()
            timings.asr_ms = _ms(t0)
            text, status, match = self.answer_text(transcript, timings)
        except Exception:
            log.exception("Échec du pipeline")
            text, status, match = MSG_ERROR, "error", None

        reply = AssistantReply(transcript, match, text, status, timings)
        t0 = time.perf_counter()
        first = True
        try:
            for chunk in self.tts.synthesize_stream(text):
                if first:
                    timings.tts_first_audio_ms = _ms(t0)
                    first = False
                timings.total_ms = _ms(t_start)
                yield chunk, reply
        except Exception:
            log.exception("TTS indisponible : réponse affichée en texte seulement")
            yield None, reply
        timings.tts_total_ms = _ms(t0)
        timings.total_ms = _ms(t_start)
        yield None, reply
