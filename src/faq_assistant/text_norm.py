"""Normalisation du texte avant TTS. PROPRIÉTAIRE : Papa.

À gérer (chaque cas = un test dans tests/test_text_norm.py) :
- montants : « 4 689 FCFA » -> « quatre mille six cent quatre-vingt-neuf francs CFA » (num2words, lang="fr")
- décimales : « 136,49 » -> « cent trente-six virgule quarante-neuf »
- unités : « kWh » -> « kilowattheures », « % » -> « pour cent »
- numéros de téléphone : « 33 867 66 66 » lu par groupes :
  « trente-trois, huit cent soixante-sept, soixante-six, soixante-six »
- codes clavier : « 804 » -> « huit cent quatre » (ou « huit, zéro, quatre » : à choisir à l'écoute)
- sigles : « UEMOA » -> « U-E-M-O-A » ou « ué-moa » selon l'écoute ; « STS » -> « S-T-S » ; « CRSE ».
"""
from __future__ import annotations


def normalize_for_tts(text: str) -> str:
    # TODO Papa
    return text
