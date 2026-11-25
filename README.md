# Assistant vocal FAQ — Senelec Woyofal (P3)

Un client pose sa question à voix haute, en français mêlé de wolof : « sama compteur dafa bip, qu'est-ce que je fais ? ».
L'assistant reconnaît la question, retrouve la bonne réponse parmi les 30 questions de la FAQ officielle Woyofal et la lit à voix haute.
Quand il n'est pas sûr, il le dit et donne le numéro du service client.

> Voix de synthèse générée par IA. Les réponses proviennent de sources publiques Senelec et CRSE (voir `data/faq_senelec_woyofal.json`).

## Pipeline

```
Micro ─▶ ASR faster-whisper + VAD ─▶ garde-fous (silence, urgence)
      ─▶ recherche hybride embeddings + BM25 ─▶ seuil « je ne sais pas »
      ─▶ (option) reformulation Claude Haiku, timeout 2,5 s, repli FAQ
      ─▶ normalisation des nombres ─▶ Edge TTS phrase par phrase (repli gTTS)
```

## Installation (Google Colab, GPU T4)

```bash
!git clone https://github.com/<org>/assistant-vocal-faq.git && cd assistant-vocal-faq
!pip install -q -r requirements.txt
# Secret Colab : ANTHROPIC_API_KEY (facultatif : sans clé, USE_LLM=0)
!python app.py --share
```

## Équipe et propriété du code

| Membre | Rôle | Fichiers |
|---|---|---|
| Harouna | LeadTech : intégration, app, LLM, merges | `types.py`, `config.py`, `pipeline.py`, `llm.py`, `app.py` |
| Fatou | Données, recherche, évaluation | `retrieval.py`, `guardrails.py`, `eval/evaluate.py`, `data/` |
| Papa | Voix : ASR, TTS, normalisation | `asr.py`, `tts.py`, `text_norm.py`, `eval/bench_asr.py` |

## Règles Git (obligatoires)

1. Après le clone : `sh scripts/install-hooks.sh` (retire toute ligne Co-authored-by Claude).
2. Branches : `feat/<prenom>-<sujet>`, `fix/<prenom>-<sujet>`. Jamais de push sur `main`.
3. Avant la PR : `git pull --rebase origin main`, puis `pytest -q`.
4. Une PR = une fonctionnalité, relue et mergée par le LeadTech (squash merge).
5. La CI refuse toute PR contenant une attribution Claude.

## Mesures

À remplir par Fatou et Papa : taux de bonnes réponses sur 30 questions orales posées par des personnes extérieures, latence médiane et p90 par étape.

## Sources des données

Voir le champ `sources` de `data/faq_senelec_woyofal.json` (FAQ Woyofal officielle de Senelec, grille tarifaire CRSE 2026, communiqués Senelec).
