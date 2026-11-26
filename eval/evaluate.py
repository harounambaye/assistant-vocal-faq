"""Évaluation finale. PROPRIÉTAIRE : Fatou (latences : Papa fournit bench_asr.py).

Entrée : data/test_oral/labels.csv  (colonnes : fichier, locuteur, faq_id_attendu)
         faq_id_attendu = "NONE" pour les questions hors FAQ (doivent donner « je ne sais pas »).
Sortie : eval/results.csv + résumé imprimé :
  - taux de bonnes réponses top-1 (sur les 30 questions orales posées par d'AUTRES personnes)
  - taux de « je ne sais pas » corrects / à tort
  - latence médiane et p90 par étape + totale + 1er son
  - matrice des erreurs (attendu -> obtenu) pour la fiche technique

RÈGLE : ce jeu n'est utilisé qu'UNE fois, à la fin, seuils gelés. Tout réglage se fait sur data/dev_oral/.
Usage :
  python -m eval.evaluate --labels data/dev_oral/labels.csv --balayage   # réglage du seuil (DEV)
  python -m eval.evaluate --labels data/test_oral/labels.csv             # mesure finale (TEST)
Les audios sont cherchés dans le dossier de labels.csv (option --audio pour un autre dossier).
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from faq_assistant.config import ROOT, SETTINGS

ETAPES = ["asr_ms", "retrieval_ms", "llm_ms", "tts_first_audio_ms", "total_ms"]


@dataclass
class Resultat:
    fichier: str
    locuteur: str
    attendu: str           # "Q05" ou "NONE"
    obtenu: str            # "Q05", "NONE" (je ne sais pas), "URGENT", "NO_SPEECH" ou "ERROR"
    statut: str            # statut du pipeline : ok, unknown, urgent, no_speech, error
    faq_proche: str        # meilleure entrée trouvée par la recherche, même sous le seuil
    score: float           # son score (0 si pas de recherche)
    transcription: str
    latences: dict[str, float]

    @property
    def correct(self) -> bool:
        return self.attendu == self.obtenu


def lire_labels(chemin: Path) -> list[dict[str, str]]:
    with chemin.open(encoding="utf-8", newline="") as f:
        return [ligne for ligne in csv.DictReader(f) if ligne.get("fichier")]


def etiquette_obtenue(statut: str, faq_id: str) -> str:
    """Traduit la réponse du pipeline en étiquette comparable à faq_id_attendu."""
    return {"ok": faq_id, "unknown": "NONE"}.get(statut, statut.upper())


def evaluer_une(pipeline, ligne: dict[str, str], dossier_audio: Path) -> Resultat:
    """Joue un audio dans le pipeline complet (y compris le TTS, pour mesurer le 1er son)."""
    reponse = None
    for _morceau, etat in pipeline.run_stream(str(dossier_audio / ligne["fichier"])):
        reponse = etat                         # on consomme le flux : la dernière réponse est complète
    match = reponse.match
    faq_proche = match.faq_id if match else ""
    return Resultat(
        fichier=ligne["fichier"], locuteur=ligne.get("locuteur", ""),
        attendu=ligne["faq_id_attendu"].strip().upper(),
        obtenu=etiquette_obtenue(reponse.status, faq_proche),
        statut=reponse.status, faq_proche=faq_proche,
        score=round(match.score, 4) if match else 0.0,
        transcription=reponse.transcript.text,
        latences={e: round(getattr(reponse.timings, e), 1) for e in ETAPES},
    )


def obtenu_avec_seuil(r: Resultat, seuil: float) -> str:
    """Rejoue la décision avec un autre seuil, sans relancer l'ASR (réglage sur DEV)."""
    if r.statut not in ("ok", "unknown") or not r.faq_proche:
        return r.obtenu
    return r.faq_proche if r.score >= seuil else "NONE"


def balayage(resultats: list[Resultat], seuils: list[float]) -> list[tuple[float, float]]:
    """Taux de bonnes réponses pour chaque seuil candidat."""
    n = len(resultats)
    return [(s, sum(obtenu_avec_seuil(r, s) == r.attendu for r in resultats) / n) for s in seuils]


def percentile(valeurs: list[float], p: int) -> float:
    if len(valeurs) < 2:
        return valeurs[0] if valeurs else 0.0
    return statistics.quantiles(valeurs, n=100, method="inclusive")[p - 1]


def resume(resultats: list[Resultat]) -> dict:
    n = len(resultats)
    hors_faq = [r for r in resultats if r.attendu == "NONE"]
    dans_faq = [r for r in resultats if r.attendu != "NONE"]
    latences = {}
    for etape in ETAPES:
        valeurs = [r.latences[etape] for r in resultats if r.latences[etape] > 0]
        latences[etape] = (round(statistics.median(valeurs), 1) if valeurs else 0.0,
                           round(percentile(valeurs, 90), 1))
    return {
        "questions": n,
        "taux_bonnes_reponses": round(sum(r.correct for r in resultats) / n, 3) if n else 0.0,
        "je_ne_sais_pas_corrects": f"{sum(r.obtenu == 'NONE' for r in hors_faq)}/{len(hors_faq)}",
        "je_ne_sais_pas_a_tort": f"{sum(r.obtenu == 'NONE' for r in dans_faq)}/{len(dans_faq)}",
        "latences_mediane_p90_ms": latences,
        "erreurs": Counter((r.attendu, r.obtenu) for r in resultats if not r.correct),
    }


def ecrire_csv(resultats: list[Resultat], chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fichier", "locuteur", "attendu", "obtenu", "correct", "statut", "faq_proche",
                    "score", "transcription", *ETAPES])
        for r in resultats:
            w.writerow([r.fichier, r.locuteur, r.attendu, r.obtenu, int(r.correct), r.statut,
                        r.faq_proche, r.score, r.transcription, *(r.latences[e] for e in ETAPES)])


def imprimer(bilan: dict) -> None:
    print(f"\nQuestions : {bilan['questions']}")
    print(f"Taux de bonnes réponses (top-1) : {bilan['taux_bonnes_reponses']:.1%}")
    print(f"« Je ne sais pas » corrects : {bilan['je_ne_sais_pas_corrects']}"
          f" · à tort : {bilan['je_ne_sais_pas_a_tort']}")
    print("\nLatences (médiane / p90, ms)")
    for etape, (med, p90) in bilan["latences_mediane_p90_ms"].items():
        print(f"  {etape:<20} {med:>8} / {p90}")
    if bilan["erreurs"]:
        print("\nErreurs (attendu -> obtenu)")
        for (attendu, obtenu), nb in bilan["erreurs"].most_common():
            print(f"  {attendu} -> {obtenu} : {nb}")


def construire_pipeline():
    """Les vrais modules de l'équipe (import ici : les tests n'en ont pas besoin)."""
    from faq_assistant.asr import WhisperASR
    from faq_assistant.pipeline import Pipeline
    from faq_assistant.retrieval import FaqRetriever
    from faq_assistant.tts import EdgeTTS

    rewriter = None
    if SETTINGS.use_llm:
        from faq_assistant.llm import ClaudeRewriter
        rewriter = ClaudeRewriter()
    return Pipeline(WhisperASR(), FaqRetriever(SETTINGS.faq_path), EdgeTTS(), rewriter)


def main() -> None:
    ap = argparse.ArgumentParser(description="Évaluation de l'assistant vocal sur un jeu oral")
    ap.add_argument("--labels", type=Path, default=ROOT / "data" / "test_oral" / "labels.csv")
    ap.add_argument("--audio", type=Path, help="dossier des audios (par défaut : celui de labels.csv)")
    ap.add_argument("--sortie", type=Path, default=ROOT / "eval" / "results.csv")
    ap.add_argument("--balayage", action="store_true",
                    help="tester plusieurs seuils (jeu de DÉVELOPPEMENT uniquement)")
    args = ap.parse_args()

    if args.balayage and "test_oral" in str(args.labels):
        raise SystemExit("Le balayage des seuils se fait sur le jeu de DÉVELOPPEMENT, jamais sur le test.")

    lignes = lire_labels(args.labels)
    pipeline = construire_pipeline()
    resultats = []
    for i, ligne in enumerate(lignes, 1):
        r = evaluer_une(pipeline, ligne, args.audio or args.labels.parent)
        print(f"[{i:>2}/{len(lignes)}] {'OK' if r.correct else 'KO'} {r.fichier} attendu={r.attendu} "
              f"obtenu={r.obtenu} score={r.score} « {r.transcription} »")
        resultats.append(r)

    ecrire_csv(resultats, args.sortie)
    imprimer(resume(resultats))
    print(f"\nSeuil utilisé : {SETTINGS.unknown_threshold} · détail : {args.sortie}")
    if args.balayage:
        print("\nBalayage du seuil (taux de bonnes réponses)")
        for seuil, taux in balayage(resultats, [x / 100 for x in range(50, 91, 2)]):
            print(f"  {seuil:.2f} : {taux:.1%}")


if __name__ == "__main__":
    main()
