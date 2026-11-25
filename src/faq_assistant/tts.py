"""Synthèse vocale phrase par phrase. PROPRIÉTAIRE : Papa.

Contrat : EdgeTTS().synthesize_stream(text) -> Iterator[str] (un fichier audio par phrase).

Cahier des charges :
1. Normaliser le texte avec text_norm.normalize_for_tts AVANT la synthèse.
2. Découper en phrases ; synthétiser la 1re phrase tout de suite et la rendre (yield)
   pendant que les suivantes se préparent -> latence perçue minimale.
3. Edge TTS (voix SETTINGS.tts_voice) ; timeout de 4 s par phrase.
4. Repli hors ligne si Edge TTS échoue (pas d'internet le jour J ?) : gTTS ou Piper/MMS-TTS
   en français. Le repli doit être testé, pas seulement codé.
5. Cache disque : clé = hash(voix + texte). Les 30 réponses + messages système sont
   pré-générés au démarrage -> réponse FAQ brute quasi instantanée.
"""
from __future__ import annotations

from collections.abc import Iterator


class EdgeTTS:
    def synthesize_stream(self, text: str) -> Iterator[str]:
        raise NotImplementedError("Papa — feat/papa-tts")
