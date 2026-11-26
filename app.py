"""Interface Gradio. PROPRIÉTAIRE : Harouna.

Lancement Colab (GPU T4), la clé est copiée des secrets AVANT de lancer l'app :
    import os; from google.colab import userdata
    os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")   # facultatif
    !python app.py --share

Ce que fait l'app :
- question au micro, par fichier (note vocale WhatsApp) ou tapée (plan B si le micro lâche) ;
- affiche ce qui a été compris, la question FAQ reconnue + score + alternatives, la réponse,
  le tableau des latences par étape ; mention « Voix de synthèse générée par IA » ;
- case « Reformulation LLM » : deux pipelines partagent les mêmes modèles (comparaison en soutenance) ;
- préchauffe les modèles au démarrage ; aucun module en panne n'empêche l'app de démarrer.

TODO Harouna : quand l'ASR et le TTS de Papa sont mergés, vérifier sur Colab le son en flux
(1re phrase < 500 ms) et la conversion des notes vocales ogg.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from faq_assistant.config import SETTINGS  # noqa: E402
from faq_assistant.pipeline import Pipeline  # noqa: E402
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


def build_pipelines() -> tuple[dict[bool, Pipeline], bool]:
    """Charge chaque modèle UNE fois ; deux pipelines les partagent (avec / sans LLM).

    Renvoie ({use_llm: pipeline}, llm_disponible).
    """
    from faq_assistant.asr import WhisperASR
    from faq_assistant.llm import make_rewriter
    from faq_assistant.retrieval import FaqRetriever
    from faq_assistant.tts import EdgeTTS

    asr, retriever, tts = WhisperASR(), FaqRetriever(SETTINGS.faq_path), EdgeTTS()
    rewriter = make_rewriter()
    pipelines = {False: Pipeline(asr, retriever, tts, None),
                 True: Pipeline(asr, retriever, tts, rewriter)}
    return pipelines, rewriter is not None


def _quiet_wav(seconds: float = 1.0, rate: int = 16000) -> str:
    """Fichier WAV presque silencieux (bruit très faible) pour réveiller Whisper et le VAD."""
    import random
    import struct
    import tempfile
    import wave

    path = Path(tempfile.gettempdir()) / "woyofal_warmup.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = (struct.pack("<h", random.randint(-30, 30)) for _ in range(int(seconds * rate)))
        w.writeframes(b"".join(frames))
    return str(path)


def warm_up(pipelines: dict[bool, Pipeline], llm_ok: bool) -> dict[str, str]:
    """Requêtes factices au démarrage : la 1re vraie question n'attend pas le chargement des modèles.

    Ne lève jamais d'exception : un module absent ou en panne n'empêche pas l'app de démarrer.
    """
    import time

    report = {}
    for name, run in [("texte (recherche, LLM, TTS)",
                       lambda: pipelines[llm_ok].run_text_stream("comment recharger mon compteur woyofal")),
                      ("audio (ASR)", lambda: pipelines[False].run_stream(_quiet_wav()))]:
        t0 = time.perf_counter()
        try:
            *_, (_, reply) = list(run())
            report[name] = f"{reply.status} en {time.perf_counter() - t0:.1f} s"
        except Exception as exc:  # le pipeline attrape déjà presque tout ; ceinture et bretelles
            report[name] = f"échec : {exc}"
    return report


def answer_events(stream: Iterable[tuple[str | None, AssistantReply]], questions: dict[str, str]):
    """(morceau audio, réponse) du pipeline -> (audio, compris, question, réponse, latences) pour Gradio."""
    for chunk, reply in stream:
        yield (chunk, render_transcript(reply), render_match(reply, questions),
               f"**Réponse :** {reply.text}", render_latencies(reply))


def build_demo(pipelines: dict[bool, Pipeline], llm_ok: bool, questions: dict[str, str]):
    import gradio as gr

    def stream_to_screen(stream):
        for audio, *texts in answer_events(stream, questions):
            # None = pas de nouveau morceau : on ne touche pas au lecteur audio en flux.
            yield (gr.skip() if audio is None else audio, *texts)

    def on_audio(path, use_llm):
        if path:  # micro arrêté sans enregistrement : rien à faire
            yield from stream_to_screen(pipelines[use_llm].run_stream(path))

    def on_text(text, use_llm):
        yield from stream_to_screen(pipelines[use_llm].run_text_stream(text or ""))

    with gr.Blocks(title="Assistant vocal Woyofal") as demo:
        gr.Markdown("## Assistant vocal Woyofal (Senelec)\n\n"
                    "**Voix de synthèse générée par IA.** Les réponses viennent de la FAQ officielle "
                    "Woyofal (sources Senelec et CRSE). En cas de doute : service client au 33 867 66 66.")
        with gr.Row():
            with gr.Column():
                mic = gr.Audio(sources=["microphone", "upload"], type="filepath",
                               label="Posez votre question (micro ou note vocale)")
                text = gr.Textbox(label="… ou tapez-la", placeholder="sama compteur dafa bip, que faire ?")
                send = gr.Button("Envoyer la question tapée")
                use_llm = gr.Checkbox(
                    value=llm_ok, interactive=llm_ok, label="Reformulation LLM (Claude Haiku 5.5)",
                    info=None if llm_ok else "Indisponible : pas de clé ANTHROPIC_API_KEY ou USE_LLM=0")
            with gr.Column():
                out_audio = gr.Audio(label="Réponse parlée", autoplay=True, streaming=True)
                heard, match, answer, latencies = gr.Markdown(), gr.Markdown(), gr.Markdown(), gr.Markdown()

        outputs = [out_audio, heard, match, answer, latencies]
        mic.stop_recording(on_audio, [mic, use_llm], outputs)
        mic.upload(on_audio, [mic, use_llm], outputs)
        send.click(on_text, [text, use_llm], outputs)
        text.submit(on_text, [text, use_llm], outputs)
    return demo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", action="store_true", help="lien public Gradio (Colab)")
    args = ap.parse_args()
    pipelines, llm_ok = build_pipelines()
    print("LLM :", "actif" if llm_ok else "inactif (réponses FAQ brutes)")
    for step, result in warm_up(pipelines, llm_ok).items():
        print(f"Préchauffage {step} : {result}")
    build_demo(pipelines, llm_ok, load_questions()).queue().launch(share=args.share)


if __name__ == "__main__":
    main()
