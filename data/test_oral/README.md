# Protocole du jeu de test oral (responsable : Fatou)

## Deux jeux séparés

| Jeu | Dossier | Qui parle | Sert à |
|---|---|---|---|
| Développement | `data/dev_oral/` | l'équipe + 2 proches | régler les seuils, le prompt Whisper, le mélange BM25/embeddings |
| **Test** | `data/test_oral/` | **5 à 6 personnes extérieures** à l'équipe | **la mesure finale, une seule fois, seuils gelés** |

## Consignes aux personnes enregistrées

- On leur montre le **sujet** de la question (ex. « vous voulez savoir combien il vous reste »), **jamais la phrase de la FAQ**.
- Elles parlent comme au téléphone : hésitations, « euh », mots en wolof, phrases incomplètes, bruit de fond normal.
- 30 questions au total : 26 couvertes par la FAQ (au moins une par catégorie) + 4 hors sujet (`NONE`), qui doivent recevoir « je ne sais pas ».
- Formats : téléphone, WhatsApp (ogg), micro de PC : on varie volontairement.

## Fichier `labels.csv`

```
fichier,locuteur,faq_id_attendu,remarque
t01.ogg,L1,Q05,wolof
t02.wav,L2,NONE,hors sujet
```

## Consentement (éthique, 10 points de la grille)

Chaque personne signe une ligne : « J'accepte que ma voix soit enregistrée pour évaluer un projet étudiant. Les fichiers ne seront ni publiés ni utilisés pour cloner ma voix et seront supprimés après la soutenance. » Les audios restent sur le Drive de l'équipe, **pas sur GitHub** (voir `.gitignore`).
