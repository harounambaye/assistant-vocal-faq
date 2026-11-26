"""Recherche de la question la plus proche. PROPRIÉTAIRE : Fatou.

Contrat : FaqRetriever(path).search(query, k) -> Match | None (voir types.Retriever).

Fonctionnement :
1. Chaque entrée de la FAQ est indexée par sa question ET ses exemples_oraux ;
   le score d'une entrée est le meilleur score parmi ses variantes.
2. Embeddings multilingues (SETTINGS.embed_model, e5 avec les préfixes « query: » et
   « passage: ») : la FAQ est encodée une seule fois, puis mise en cache .npy ;
   à chaque requête, un seul encodage.
3. Recherche hybride : score = alpha * cosinus + (1 - alpha) * BM25 normalisé.
   L'embedding comprend la paraphrase, BM25 rattrape les mots-clés (« bip », « TVA »).
   BM25 est divisé par le score maximal possible pour cette requête (et non par le meilleur
   score obtenu) : une question hors sujet garde un BM25 faible au lieu d'être gonflée à 1.
4. La requête est normalisée : minuscules, hésitations retirées (« euh », « bon »),
   graphies fréquentes de l'ASR corrigées (« woyo fall » -> « woyofal »).
5. Match.alternatives contient les k-1 entrées suivantes (démo, analyse d'erreurs).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import numpy as np

from .config import ROOT, SETTINGS
from .types import Match

# Une fonction qui transforme une liste de textes en vecteurs normalisés (une ligne par texte).
Encodeur = Callable[[list[str]], np.ndarray]

HESITATIONS = {"euh", "heu", "hum", "hmm", "bon", "ben", "bah", "hein", "voilà", "voila"}

# Graphies que l'ASR produit souvent pour les mots du métier.
CORRECTIONS = [
    (r"\bwoyo\s*fall?\b", "woyofal"),
    (r"\bwoyo\s*fal\b", "woyofal"),
    (r"\bs[ée]n[ée]lec\b", "senelec"),
    (r"\bkilo\s*watts?\b", "kilowatt"),
    (r"\bt\s*v\s*a\b", "tva"),
]

# Mots trop fréquents pour aider BM25 : on ne les compte pas.
MOTS_VIDES = {
    "le", "la", "les", "l", "de", "du", "des", "d", "un", "une", "et", "ou", "a", "au", "aux",
    "en", "je", "j", "me", "m", "mon", "ma", "mes", "il", "y", "on", "ce", "c", "ca", "est",
    "que", "qu", "qui", "pour", "dans", "sur", "pas", "ne", "n", "se", "s", "vous", "votre",
}


def normaliser_requete(texte: str) -> str:
    """Minuscules, apostrophes unifiées, corrections ASR, hésitations retirées."""
    texte = unicodedata.normalize("NFC", texte.lower()).replace("’", "'")
    for motif, remplacement in CORRECTIONS:
        texte = re.sub(motif, remplacement, texte)
    mots = [m for m in re.split(r"\s+", texte) if m.strip(",.;:!?") not in HESITATIONS]
    return " ".join(mots).strip(" ,.;:!?")


def mots_cles(texte: str) -> list[str]:
    """Mots pour BM25 : sans accents, sans ponctuation, sans mots vides."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFKD", texte.lower())
                           if not unicodedata.combining(c))
    return [m for m in re.findall(r"[a-z0-9]+", sans_accents) if m not in MOTS_VIDES]


class BM25:
    """BM25 « Okapi » : score de pertinence par mots-clés (k1 = 1,5 ; b = 0,75)."""

    def __init__(self, documents: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.documents, self.k1, self.b = documents, k1, b
        self.longueur_moyenne = sum(map(len, documents)) / max(len(documents), 1)
        self.frequences = [Counter(doc) for doc in documents]
        nb_docs_avec = Counter(mot for doc in documents for mot in set(doc))
        n = len(documents)
        self.idf = {mot: math.log(1 + (n - df + 0.5) / (df + 0.5)) for mot, df in nb_docs_avec.items()}
        self.idf_inconnu = math.log(1 + (n + 0.5) / 0.5)   # mot absent de la FAQ : le plus rare possible

    def scores(self, requete: list[str]) -> list[float]:
        resultats = []
        for doc, freq in zip(self.documents, self.frequences, strict=True):
            norme = self.k1 * (1 - self.b + self.b * len(doc) / self.longueur_moyenne)
            resultats.append(sum(
                self.idf[mot] * freq[mot] * (self.k1 + 1) / (freq[mot] + norme)
                for mot in requete if mot in freq
            ))
        return resultats

    def score_maximal(self, requete: list[str]) -> float:
        """Score qu'obtiendrait un document contenant tous les mots de la requête.

        Les mots absents de la FAQ (« météo », « Thiès ») comptent au dénominateur :
        une question hors sujet obtient donc un BM25 normalisé proche de 0.
        """
        return sum(self.idf.get(mot, self.idf_inconnu) * (self.k1 + 1) for mot in set(requete))


def encodeur_e5(nom_modele: str) -> Encodeur:
    """Charge le modèle d'embeddings une seule fois (import ici : inutile pour les tests)."""
    from sentence_transformers import SentenceTransformer

    modele = SentenceTransformer(nom_modele)
    return lambda textes: modele.encode(textes, normalize_embeddings=True, convert_to_numpy=True)


class FaqRetriever:
    def __init__(self, faq_path: str | Path, encodeur: Encodeur | None = None,
                 alpha: float = 0.7, dossier_cache: str | Path | None = None):
        self.entries = json.loads(Path(faq_path).read_text(encoding="utf-8"))["faq"]
        self.alpha = alpha
        # Une ligne par variante (question ou exemple oral) et l'entrée à laquelle elle appartient.
        self.variantes: list[str] = []
        self.entree_de: list[int] = []
        for i, entree in enumerate(self.entries):
            for texte in [entree["question"], *entree.get("exemples_oraux", [])]:
                self.variantes.append(normaliser_requete(texte))
                self.entree_de.append(i)
        self.bm25 = BM25([mots_cles(v) for v in self.variantes])
        self.encodeur = encodeur or encodeur_e5(SETTINGS.embed_model)
        self.vecteurs = self._vecteurs_faq(Path(dossier_cache or ROOT / ".cache"),
                                           cache=encodeur is None)

    def _vecteurs_faq(self, dossier: Path, cache: bool) -> np.ndarray:
        """Encode les variantes une fois ; avec le vrai modèle, réutilise le cache .npy."""
        passages = [f"passage: {v}" for v in self.variantes]
        if not cache:
            return self.encodeur(passages)
        cle = hashlib.sha1("\n".join([SETTINGS.embed_model, *passages]).encode("utf-8")).hexdigest()
        fichier = dossier / f"faq_embeddings_{cle[:12]}.npy"
        if fichier.exists():
            return np.load(fichier)
        vecteurs = self.encodeur(passages)
        dossier.mkdir(parents=True, exist_ok=True)
        np.save(fichier, vecteurs)
        return vecteurs

    def search(self, query: str, k: int = 3) -> Match | None:
        requete = normaliser_requete(query)
        if not requete:
            return None
        cosinus = np.clip(self.vecteurs @ self.encodeur([f"query: {requete}"])[0], 0.0, 1.0)
        mots = mots_cles(requete)
        maximum = self.bm25.score_maximal(mots)
        bm25 = np.array(self.bm25.scores(mots)) / maximum if maximum > 0 else np.zeros(len(self.variantes))
        hybride = self.alpha * cosinus + (1 - self.alpha) * bm25

        meilleur: dict[int, float] = {}            # entrée -> meilleur score de ses variantes
        for ligne, score in enumerate(hybride):
            i = self.entree_de[ligne]
            meilleur[i] = max(meilleur.get(i, 0.0), float(score))
        classement = sorted(meilleur.items(), key=lambda item: item[1], reverse=True)[:k]

        i, score = classement[0]
        entree = self.entries[i]
        return Match(
            faq_id=entree["id"], question=entree["question"], answer=entree["reponse"],
            score=round(score, 4),
            alternatives=[(self.entries[j]["id"], round(s, 4)) for j, s in classement[1:]],
        )
