"""Interface Gradio. PROPRIÉTAIRE : Harouna.

Lancement Colab : !python app.py --share
TODO Harouna :
- brancher WhisperASR, FaqRetriever, EdgeTTS, ClaudeRewriter quand leurs PR sont mergées ;
- afficher : transcription, question FAQ reconnue + score, réponse, tableau des latences ;
- case à cocher « Reformulation LLM » (pour comparer avec/sans en soutenance) ;
- mention visible : « Voix de synthèse générée par IA ».
- préchauffer les modèles au démarrage (1 requête factice) pour éviter la 1re requête lente devant le jury.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from faq_assistant.config import SETTINGS  # noqa: E402
from faq_assistant.types import AssistantReply  # noqa: E402

STATUS_LABELS = {
    "ok": "✅ Réponse de la FAQ",
    "unknown": "🤔 Pas sûr : renvoi vers le service client",
    "no_speech": "🔇 Rien entendu",
    "urgent": "🚨 Urgence : consigne de sécurité, sans recherche",
    "error": "⚠️ Erreur technique",
}


def load_questions(path: Path = SETTINGS.faq_path) -> dict[str, str]:
    """faq_id -> question, pour afficher les alternatives en clair."""
    return {e["id"]: e["question"] for e in json.loads(path.read_text(encoding="utf-8"))["faq"]}


def render_transcript(reply: AssistantReply) -> str:
    text = reply.transcript.text.strip()
    return f"**Compris :** « {text} »" if text else "**Compris :** _(rien)_"


def render_match(reply: AssistantReply, questions: dict[str, str]) -> str:
    lines = [f"**État :** {STATUS_LABELS.get(reply.status, reply.status)}"]
    m = reply.match
    if m is None:
        return "\n\n".join(lines)
    if reply.status == "unknown":
        lines.append(f"Meilleure candidate **{m.faq_id}** ({m.score:.2f}), "
                     f"sous le seuil {SETTINGS.unknown_threshold:.2f} : {m.question}")
    else:
        lines.append(f"**Question reconnue :** {m.faq_id} — {m.question} (score {m.score:.2f})")
    if m.alternatives:
        alt_id, alt_score = m.alternatives[0]
        if reply.status == "ok" and m.score - alt_score < SETTINGS.ambiguity_margin:
            lines.append(f"❓ Vouliez-vous plutôt dire : **{questions.get(alt_id, alt_id)}** ?")
        lines.append("Alternatives : " + ", ".join(f"{i} ({s:.2f})" for i, s in m.alternatives))
    return "\n\n".join(lines)


def render_latencies(reply: AssistantReply) -> str:
    t = reply.timings
    rows = [("ASR", t.asr_ms), ("Recherche", t.retrieval_ms), ("LLM", t.llm_ms),
            ("TTS, 1er son", t.tts_first_audio_ms), ("TTS, total", t.tts_total_ms), ("**Total**", t.total_ms)]
    body = "\n".join(f"| {name} | {f'{ms:.0f} ms' if ms > 0 else '—'} |" for name, ms in rows)
    return "| Étape | Latence |\n|---|---:|\n" + body


def build_demo():
    import gradio as gr

    with gr.Blocks(title="Assistant vocal Woyofal") as demo:
        gr.Markdown("## Assistant vocal Woyofal (Senelec)\n*Voix de synthèse générée par IA.*")
        mic = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Posez votre question")
        out_audio = gr.Audio(label="Réponse", autoplay=True, streaming=True)
        out_text = gr.Markdown()
        mic.stop_recording(lambda p: (None, "TODO : brancher Pipeline.run_stream"),
                           mic, [out_audio, out_text])
    return demo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", action="store_true")
    build_demo().queue().launch(share=ap.parse_args().share)
