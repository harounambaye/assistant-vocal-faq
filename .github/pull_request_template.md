## Ce que fait cette PR

<!-- Une ou deux phrases. Une PR = une fonctionnalité. -->

## Fichiers touchés

- [ ] Uniquement les fichiers dont je suis propriétaire (voir CODEOWNERS)
- [ ] Si je touche `types.py`, `config.py` ou `requirements.txt` : c'est une PR séparée, prévenue sur le groupe

## Vérifications

- [ ] `git pull --rebase origin main` fait juste avant d'ouvrir la PR (aucun conflit)
- [ ] `pytest -q` passe en local
- [ ] Testé sur Colab GPU (pour ASR, TTS, recherche, app)
- [ ] Latence mesurée si le code est sur le chemin de la réponse : ____ ms
- [ ] Aucune clé API, aucun audio de test (`data/test_oral/`) dans la PR
- [ ] Aucune mention de co-auteur Claude dans les commits ni dans cette description

## Comment tester

<!-- Commande ou cellule Colab que le LeadTech lance pour vérifier. -->
