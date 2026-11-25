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
