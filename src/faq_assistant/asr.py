"""Reconnaissance vocale. PROPRIÉTAIRE : Papa.

Contrat : WhisperASR().transcribe(audio_path) -> Transcript (voir types.ASR).

Cahier des charges :
1. faster-whisper, modèle chargé UNE fois (singleton), device="cuda" si dispo sinon CPU int8.
2. vad_filter=True (Silero) : sans VAD, Whisper invente du texte sur le silence.
3. language="fr" forcé (gain de latence), beam_size=1 à comparer avec 5.
4. initial_prompt avec le vocabulaire métier pour aider sur les noms et le wolof :
   « Senelec, Woyofal, compteur, clavier, kilowattheure, code 804, 801, Wave, Orange Money,
     dafa, sama, naka, courant bi, ñaata ».
5. Remplir avg_logprob, no_speech_prob, duration_s (après VAD) — le pipeline s'en sert.
6. Audio > SETTINGS.max_audio_s : tronquer. Fichier vide / illisible : Transcript(text="").
7. Benchmark à livrer (eval/bench_asr.py) : small, medium, large-v3-turbo -> temps + WER
   sur 10 enregistrements de DEV.
"""
from __future__ import annotations

from .types import Transcript


class WhisperASR:
    def __init__(self, model_name: str | None = None):
        # TODO Papa : charger faster_whisper.WhisperModel une seule fois.
        self.model_name = model_name

    def transcribe(self, audio_path: str) -> Transcript:
        raise NotImplementedError("Papa — feat/papa-asr")
