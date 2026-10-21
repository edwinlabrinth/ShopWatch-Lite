import unittest

from src.analyse import (chercher_fiches, compter_incidents, diagnostiquer,
                         est_repete, evaluer)
from src.contrat import FICHES, Signal


def sig(categorie="JOURNAL", gravite="MAJEUR", texte="timeout passerelle apres 30s",
        service="paiement", date="2026-11-27T17:00:00Z"):
    return Signal("SH-0001", date, "PAIEMENT", service,
                  "production", categorie, gravite, texte)


class TestAnalyse(unittest.TestCase):
    def test_repete(self):
        vus = set()
        self.assertFalse(est_repete(sig(), vus))
        self.assertTrue(est_repete(sig(), vus))

    def test_repete_secondes_differentes(self):
        vus = set()
        self.assertFalse(est_repete(sig(date="2026-11-27T17:02:11Z"), vus))
        self.assertFalse(est_repete(sig(date="2026-11-27T17:02:12Z"), vus))


if __name__ == "__main__":
    unittest.main()
