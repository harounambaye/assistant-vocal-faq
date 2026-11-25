"""Évaluation finale. PROPRIÉTAIRE : Fatou (latences : Papa fournit bench_asr.py).

Entrée : data/test_oral/labels.csv  (colonnes : fichier, locuteur, faq_id_attendu)
         faq_id_attendu = "NONE" pour les questions hors FAQ (doivent donner « je ne sais pas »).
Sortie : eval/results.csv + résumé imprimé :
  - taux de bonnes réponses top-1 (sur les 30 questions orales posées par d'AUTRES personnes)
  - taux de « je ne sais pas » corrects / à tort
  - latence médiane et p90 par étape + totale + 1er son
  - matrice des erreurs (attendu -> obtenu) pour la fiche technique

RÈGLE : ce jeu n'est utilisé qu'UNE fois, à la fin, seuils gelés. Tout réglage se fait sur data/dev_oral/.
Usage : python -m eval.evaluate --labels data/test_oral/labels.csv
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Fatou — feat/fatou-eval")


if __name__ == "__main__":
    main()
