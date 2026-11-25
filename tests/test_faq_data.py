import json

from faq_assistant.config import SETTINGS


def test_faq_has_30_sourced_entries():
    data = json.loads(SETTINGS.faq_path.read_text(encoding="utf-8"))
    faq = data["faq"]
    assert len(faq) == 30
    assert len({e["id"] for e in faq}) == 30
    for e in faq:
        assert e["question"] and e["reponse"]
        assert e["sources"] and all(s in data["sources"] for s in e["sources"])
        assert len(e["reponse"]) < 320, f"{e['id']} trop long pour l'oral"
