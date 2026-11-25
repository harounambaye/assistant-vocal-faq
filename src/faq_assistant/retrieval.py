"""Recherche de la question la plus proche. PROPRIÉTAIRE : Fatou.

Contrat : FaqRetriever(path).search(query, k) -> Match | None (voir types.Retriever).

Cahier des charges :
1. Charger la FAQ JSON ; indexer pour chaque entrée la question ET ses exemples_oraux
   (score d'une FAQ = max sur ses variantes).
2. Embeddings multilingues (SETTINGS.embed_model). Avec e5 : préfixes "query: " / "passage: ".
   Encoder la FAQ UNE fois au démarrage (et mettre en cache .npy) ; à la requête, 1 seul encode.
3. Recherche hybride : score = a * cosinus + (1 - a) * BM25 normalisé (rank_bm25),
   pour rattraper les mots-clés (« 804 », « bip », « TVA ») que l'embedding rate.
4. Normaliser la requête : minuscules, retirer les hésitations (« euh », « bon », « donc »),
   corriger les graphies fréquentes de l'ASR (« woyo fall » -> « woyofal », « sénélec » -> « senelec »).
5. Remplir Match.alternatives avec les k-1 suivants (utile pour la démo et l'analyse d'erreurs).
6. Objectif de latence : < 30 ms par requête sur GPU T4.
"""
from __future__ import annotations

import json
from pathlib import Path

from .types import Match


class FaqRetriever:
    def __init__(self, faq_path: str | Path):
        self.entries = json.loads(Path(faq_path).read_text(encoding="utf-8"))["faq"]
        # TODO Fatou : charger le modèle d'embeddings, encoder, construire BM25.

    def search(self, query: str, k: int = 3) -> Match | None:
        raise NotImplementedError("Fatou — feat/fatou-retrieval")
