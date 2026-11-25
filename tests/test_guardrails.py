from faq_assistant.guardrails import is_urgent


def test_urgent():
    assert is_urgent("y a des étincelles sur le compteur")
    assert is_urgent("le fil est tombé par terre")


def test_not_urgent():
    assert not is_urgent("comment recharger mon compteur")
    assert not is_urgent("mon crédit finit vite")
