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

    def test_compter_incidents_majeur_et_bloquant(self):
        compteur = {}
        self.assertEqual(compter_incidents(sig(gravite="MAJEUR"), compteur), 1)
        self.assertEqual(compter_incidents(sig(gravite="BLOQUANT"), compteur), 2)
        self.assertEqual(compteur, {"paiement": 2})

    def test_compter_incidents_par_service(self):
        compteur = {}
        compter_incidents(sig(service="paiement"), compteur)
        self.assertEqual(compter_incidents(sig(service="panier"), compteur), 1)
        self.assertEqual(compteur, {"paiement": 1, "panier": 1})

    def test_compter_incidents_ignore_gravite_faible(self):
        compteur = {}
        self.assertEqual(compter_incidents(sig(gravite="MODERE"), compteur), 0)
        self.assertEqual(compter_incidents(sig(gravite="MINEUR"), compteur), 0)
        self.assertEqual(compteur, {})

    def test_compter_incidents_ignore_hors_journal(self):
        compteur = {}
        self.assertEqual(compter_incidents(sig(categorie="FAILLE", gravite="BLOQUANT"), compteur), 0)
        self.assertEqual(compteur, {})

    def test_chercher_fiches_casse_ignoree(self):
        self.assertEqual(chercher_fiches(sig(texte="TIMEOUT passerelle"), FICHES),
                         [FICHES["timeout"]])

    def test_chercher_fiches_ordre_de_la_base(self):
        base = {"build": "conseil build", "timeout": "conseil timeout"}
        self.assertEqual(chercher_fiches(sig(texte="timeout pendant le build"), base),
                         ["conseil build", "conseil timeout"])

    def test_chercher_fiches_aucune(self):
        self.assertEqual(chercher_fiches(sig(texte="Service demarre"), FICHES), [])

    def test_evaluer_panne_en_boucle(self):
        s = sig()
        self.assertEqual(evaluer(s, 4), "BLOQUANT")
        self.assertEqual(evaluer(s, 3), "MAJEUR")

    def test_evaluer_gravite_du_signal(self):
        self.assertEqual(evaluer(sig(gravite="MINEUR")), "MINEUR")

    def test_diagnostiquer_cause_niveau_origines(self):
        d = diagnostiquer(sig(), FICHES, 2)
        self.assertEqual(d.signal_ref, "SH-0001")
        self.assertEqual(d.niveau, "MAJEUR")
        self.assertEqual(d.cause, FICHES["timeout"])
        self.assertEqual(d.origines, ["PAIEMENT"])

    def test_diagnostiquer_plusieurs_fiches(self):
        d = diagnostiquer(sig(texte="timeout du build"), FICHES)
        self.assertEqual(d.cause, FICHES["timeout"] + " ; " + FICHES["build"])

    def test_diagnostiquer_cause_inconnue(self):
        d = diagnostiquer(sig(texte="Service demarre", gravite="MINEUR"), FICHES)
        self.assertEqual(d.cause, "Cause inconnue : verification manuelle")

    def test_diagnostiquer_action_faille_prioritaire(self):
        d = diagnostiquer(sig(categorie="FAILLE", gravite="BLOQUANT",
                              texte="Faille CVE-2026-7788 dans lib-panier",
                              service="lib-panier"), FICHES)
        self.assertEqual(d.action, "Corriger la dependance lib-panier")
        self.assertFalse(d.critique)

    def test_diagnostiquer_action_build_echec(self):
        d = diagnostiquer(sig(categorie="BUILD_ECHEC", texte="Build deploiement : echec",
                              service="deploiement"), FICHES)
        self.assertEqual(d.action, "Rejouer le build deploiement")
        self.assertFalse(d.critique)

    def test_diagnostiquer_isoler_est_critique(self):
        d = diagnostiquer(sig(), FICHES, 4)
        self.assertEqual(d.niveau, "BLOQUANT")
        self.assertEqual(d.action, "Isoler le service paiement")
        self.assertTrue(d.critique)

    def test_diagnostiquer_observer(self):
        d = diagnostiquer(sig(), FICHES, 1)
        self.assertEqual(d.action, "Observer")
        self.assertFalse(d.critique)

    def test_diagnostiquer_passe_etat_evalue(self):
        s = sig()
        diagnostiquer(s, FICHES)
        self.assertEqual(s.etat, "EVALUE")


if __name__ == "__main__":
    unittest.main()
