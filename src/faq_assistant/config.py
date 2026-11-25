"""Configuration centrale. PROPRIÉTAIRE : Harouna.

Tous les seuils réglables sont ici, pour qu'aucun module ne code de valeur en dur.
Les valeurs se règlent sur le jeu de DÉVELOPPEMENT uniquement, jamais sur le jeu de test.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    faq_path: Path = ROOT / "data" / "faq_senelec_woyofal.json"

    # ASR (Papa)
    whisper_model: str = os.getenv("WHISPER_MODEL", "large-v3-turbo")
    whisper_compute: str = os.getenv("WHISPER_COMPUTE", "float16")  # "int8" sur CPU
    max_audio_s: float = 30.0          # au-delà : on coupe et on prévient
    min_speech_s: float = 0.4          # en dessous : "je n'ai pas entendu"
    no_speech_threshold: float = 0.6

    # Recherche (Fatou)
    embed_model: str = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-small")
    unknown_threshold: float = float(os.getenv("UNKNOWN_THRESHOLD", "0.80"))  # à régler sur dev
    ambiguity_margin: float = 0.02     # top1 - top2 < marge => demander de préciser

    # LLM (Harouna) — optionnel, jamais bloquant
    use_llm: bool = os.getenv("USE_LLM", "1") == "1"
    llm_model: str = os.getenv("LLM_MODEL", "claude-haiku-5-5")
    llm_timeout_s: float = 2.5
    llm_max_tokens: int = 160

    # TTS (Papa)
    tts_voice: str = os.getenv("TTS_VOICE", "fr-FR-DeniseNeural")
    tts_rate: str = os.getenv("TTS_RATE", "+5%")


SETTINGS = Settings()

MSG_UNKNOWN = ("Je ne suis pas sûr d'avoir la bonne réponse. "
               "Pour être aidé, appelez le service client Senelec au 33 867 66 66.")
MSG_NO_SPEECH = "Je n'ai pas bien entendu. Pouvez-vous reposer votre question ?"
MSG_ERROR = ("Désolé, un problème technique m'empêche de répondre. "
             "Appelez le service client Senelec au 33 867 66 66.")
MSG_URGENT = ("Si vous voyez un fil électrique tombé, des étincelles ou de la fumée, "
              "éloignez-vous et appelez immédiatement Senelec au 33 867 66 66.")
