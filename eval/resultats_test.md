# Résultats de l'évaluation finale

Mesure faite le 28 novembre 2026, **une seule fois**, sur le jeu de test oral (`data/test_oral/labels.csv`),
avec le seuil **gelé à 0,64**, réglé auparavant sur le jeu de développement (`data/dev_oral/`).

## Conditions

| Élément | Valeur |
|---|---|
| Questions | 29, posées à voix haute par 4 personnes extérieures à l'équipe (25 dans la FAQ, 4 hors sujet) |
| Enregistrement | Notes vocales WhatsApp (Opus, 48 kHz), à la maison, avec hésitations, wolof et bruit de fond |
| ASR | faster-whisper `large-v3-turbo`, GPU T4 (Colab), langue `fr`, VAD, vocabulaire métier en `initial_prompt`. Version provisoire en attendant `asr.py` |
| Recherche | `retrieval.py` : embeddings `multilingual-e5-small` + BM25, poids 0,7 / 0,3 |
| LLM et TTS | Désactivés pendant la mesure (sans effet sur la question trouvée) |
| Seuil « je ne sais pas » | 0,64 (balayage de 0,50 à 0,90 sur le jeu de dev) |

## Résultats

| Mesure | Résultat |
|---|---|
| **Taux de bonnes réponses (top-1)** | **20/29 = 69 %** |
| « Je ne sais pas » corrects (hors sujet refusés) | **4/4** |
| « Je ne sais pas » à tort (question de la FAQ refusée) | 7/25 |
| Réponse fausse donnée à la place d'une autre | 2/25 |
| Latence ASR (médiane / p90) | 529 / 592 ms |
| **Latence recherche (médiane / p90)** | **14 / 19 ms** |
| Latence totale sans LLM ni TTS (médiane / p90) | 550 / 607 ms |

Aucune question hors sujet n'a reçu de fausse réponse : l'assistant n'invente pas.

## Analyse des 9 échecs

| Cause | Questions | Ce qui s'est passé |
|---|---|---|
| Wolof non reconnu par l'ASR | t01, t02, t07 | L'ASR forcée en français produit un texte incompréhensible (« mande maggi sa ma kere kharit… ») : la recherche ne peut rien trouver |
| Erreur de transcription sur un mot-clé | t15, t22, t27, t28 | « facture » → « future », « quel prix » → « premier coûte », « s'allume » → « salue », numéro « T27 » → « Cité 27 » (non retiré) |
| Bonne question, score juste sous le seuil | t18 (0,635), t20 (0,637) | Le seuil a été réglé sur 6 questions de dev seulement |

**Conclusion** : la recherche fonctionne quand la transcription est correcte ; le maillon faible est l'ASR, surtout sur le wolof.

## Pistes d'amélioration

1. Wolof : ne pas forcer la langue, ou utiliser un modèle adapté au wolof ; sinon, le dire au client (« parlez en français »).
2. Ajouter les erreurs d'ASR fréquentes à la normalisation de la requête (`CORRECTIONS` dans `retrieval.py`).
3. Régler le seuil sur un jeu de dev plus grand (30 questions prévues, 6 enregistrées).
4. Refaire la mesure avec le module `asr.py` définitif et la latence du 1er son (TTS).

## Essais complémentaires pour le wolof

Le projet demande un assistant en français **et** en wolof. Les 3 échecs wolof du test ont donc donné lieu à
trois essais (28 novembre 2026), mesurés sur un **jeu de dev wolof** séparé : 7 notes enregistrées par un membre
de l'équipe (4 questions de la FAQ, 3 hors sujet), non publiées. Le jeu de test n'a servi qu'à l'essai 1, sans
changer le seuil (0,64) ni le code : le résultat officiel reste **20/29**.

| Essai | Idée | Résultat |
|---|---|---|
| 1. ASR wolof `M9and2M/whisper-small-wolof` | Transcrire aussi avec un modèle entraîné sur le wolof et garder le texte au meilleur score | Test : 0/3 en wolof, aucun gain global. Dev wolof : 0/4. Jusqu'à 11 s par note |
| 2. Table d'équivalences wolof → français (`CORRECTIONS`) et mots vides wolof | « kontoor » → « compteur », « koti » → « code », « kuuraŋ » → « courant »… | Dev wolof : 0/4. Dev français : 4/6 → 3/6. **Rejetée, non intégrée** |
| 3. Traduction wolof → français (NLLB-200, 600M) avant la recherche | Chercher en français, là où la recherche fonctionne | Dev wolof : 0/4, traductions sans sens |

Dans les trois essais, les questions hors sujet restent refusées (3/3) : l'assistant n'invente pas.

**Pourquoi ça bloque** : une chaîne d'erreurs.
1. On parle en mélangeant wolof et français ; chaque modèle déforme la langue qu'il ne connaît pas
   (« est-ce que » → « eska », « compteur » → « kontoor », « Sonatel » → « su natal »).
2. Le modèle de recherche `multilingual-e5-small` ne comprend pas le wolof : toutes les phrases wolof obtiennent
   un score entre 0,59 et 0,64, qu'elles soient dans la FAQ ou hors sujet.
3. La FAQ ne contient qu'une formulation wolof par question.

**Pistes** : un ASR entraîné sur le wolof mêlé de français ; un modèle de recherche multilingue plus grand ;
plus d'exemples wolof dans la FAQ, écrits par des locuteurs ; en attendant, proposer au client de reformuler
en français quand l'assistant ne comprend pas.

## Limites et transparence

- 4 voix seulement (5 à 6 prévues) ; jeu de dev réduit à 6 questions.
- **t09** retiré : cette situation n'a jamais été enregistrée par la personne 2.
- Les notes de la personne 2 (t10 à t12) et de la personne 4 (t24 à t30) ont été remises en face de leur vraie
  situation d'après les transcriptions (numéro dit au début de chaque note), **avant** l'analyse des scores ;
  le seuil et le code n'ont pas été modifiés.
- Le numéro de la note (« t07 », « d01 ») est retiré de la transcription avant la recherche, car un vrai client ne le dit pas.

## Éthique

Les 5 personnes enregistrées ont donné leur consentement (« J'accepte que ma voix soit enregistrée pour évaluer un projet
étudiant ; les fichiers ne seront ni publiés ni utilisés pour cloner ma voix et seront supprimés après la soutenance »).
Les audios ne sont pas sur GitHub et seront supprimés après la soutenance.
