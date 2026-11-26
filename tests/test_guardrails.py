import pytest

from faq_assistant.guardrails import is_urgent


@pytest.mark.parametrize("phrase", [
    # fil ou câble
    "le fil est tombé par terre",
    "il y a un câble arraché devant la maison",
    "le fil électrique est dénudé",
    # étincelles, fumée, feu, explosion
    "y a des étincelles sur le compteur",
    "je crois qu'il y a un court-circuit",
    "le compteur fume",
    "il y a de la fumée qui sort du clavier",
    "il y a le feu au compteur",
    "le compteur a explosé",
    # brûlé
    "ça sent le brûlé près du compteur",
    "mon compteur brûle",
    # choc électrique
    "mon fils a été électrocuté",
    "j'ai été électrisé en touchant le compteur",
    "le courant m'a pris quand j'ai touché",
    # wolof
    "compteur bi dafa am safara",
    "compteur bi dafa lakk",
    "saxaar bu bari ngi génn ci compteur bi",
    "fil bi daanu na ci suuf",
    "courant bi jàpp na ma",
    # sans accents (transcription imparfaite)
    "y a des etincelles",
    "le fil est denude",
])
def test_urgent(phrase):
    assert is_urgent(phrase)


@pytest.mark.parametrize("phrase", [
    "comment recharger mon compteur",
    "mon crédit finit vite",
    "mon compteur fait bip toute la nuit",          # Q11 : sonnerie, pas une urgence
    "il n'y a plus de courant dans le quartier",    # Q28 : panne, pas une urgence
    "j'ai du crédit mais le courant est parti",     # Q27
    "mon fils veut acheter du crédit woyofal",      # « fils » sans « tombé »
    "le compteur ne s'allume plus",
    "sama compteur dafa sonner",
])
def test_not_urgent(phrase):
    assert not is_urgent(phrase)
