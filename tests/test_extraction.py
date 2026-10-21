import unittest

from src.extraction import lire_build, lire_journal, lire_scan, masquer_donnees

LIGNE = "2026-11-27 17:02:11 paiement ERROR timeout passerelle apres 30s card=4970123412341234"
RAPPORT_SCAN = {"id_faille": "CVE-2026-7788", "paquet": "lib-panier",
                "risque": "critique", "date": "2026-11-27T17:09:00Z"}
RAPPORT_BUILD = {"etape": "deploiement", "resultat": "echec",
                 "date": "2026-11-27T17:08:00Z"}


class TestExtraction(unittest.TestCase):
    def test_masquer_donnees(self):
        self.assertEqual(masquer_donnees("client=bob pwd=abc123"), "client=bob pwd=[MASQUE]")

    def test_masquer_donnees_casse_ignoree(self):
        self.assertEqual(masquer_donnees("PWD=abc123"), "PWD=[MASQUE]")

    def test_masquer_donnees_tous_les_parametres(self):
        for nom in ("password", "pwd", "token", "secret", "card", "iban"):
            self.assertEqual(masquer_donnees(f"{nom}=valeur"), f"{nom}=[MASQUE]")

    def test_masquer_donnees_formes_et_separateurs(self):
        self.assertEqual(masquer_donnees("token: abc123"), "token: [MASQUE]")
        self.assertEqual(masquer_donnees("card=4970&client=bob"), "card=[MASQUE]&client=bob")
        self.assertEqual(masquer_donnees("card=4970,client=bob"), "card=[MASQUE],client=bob")
        self.assertEqual(masquer_donnees("card=4970;client=bob"), "card=[MASQUE];client=bob")

    def test_masquer_donnees_ignore_les_autres_noms(self):
        self.assertEqual(masquer_donnees("client=bob"), "client=bob")

    def test_bearer(self):
        self.assertEqual(masquer_donnees("Authorization: Bearer eyJ.abc-1"),
                         "Authorization: Bearer [MASQUE]")
        self.assertEqual(masquer_donnees("discard=1"), "discard=1")

    def test_lire_journal(self):
        sig = lire_journal(LIGNE, 42)
        self.assertEqual(sig.ref, "SH-0042")
        self.assertEqual(sig.date, "2026-11-27T17:02:11Z")
        self.assertEqual(sig.gravite, "MAJEUR")
        self.assertNotIn("4970123412341234", sig.texte)

    def test_lire_journal_champs(self):
        sig = lire_journal(LIGNE, 42)
        self.assertEqual(sig.origine, "PAIEMENT")
        self.assertEqual(sig.service, "paiement")
        self.assertEqual(sig.env, "production")
        self.assertEqual(sig.categorie, "JOURNAL")
        self.assertEqual(sig.texte, "timeout passerelle apres 30s card=[MASQUE]")

    def test_lire_journal_gravites(self):
        attendus = (("FATAL", "BLOQUANT"), ("CRITICAL", "BLOQUANT"),
                    ("ERROR", "MAJEUR"), ("error", "MAJEUR"),
                    ("WARN", "MODERE"), ("WARNING", "MODERE"),
                    ("INFO", "MINEUR"))
        for niveau, attendu in attendus:
            sig = lire_journal(f"2026-11-27 17:02:11 paiement {niveau} message", 1)
            self.assertEqual(sig.gravite, attendu)

    def test_lire_journal_ligne_incomplete(self):
        with self.assertRaises(ValueError):
            lire_journal("2026-11-27 17:02:11 paiement ERROR", 1)

    def test_lire_scan(self):
        sig = lire_scan(RAPPORT_SCAN, 9)
        self.assertEqual(sig.ref, "SH-0009")
        self.assertEqual(sig.date, "2026-11-27T17:09:00Z")
        self.assertEqual(sig.origine, "SCANNER")
        self.assertEqual(sig.service, "lib-panier")
        self.assertEqual(sig.env, "production")
        self.assertEqual(sig.categorie, "FAILLE")
        self.assertEqual(sig.gravite, "BLOQUANT")
        self.assertEqual(sig.texte, "Faille CVE-2026-7788 dans lib-panier")

    def test_lire_scan_gravites(self):
        attendus = (("critique", "BLOQUANT"), ("haut", "MAJEUR"),
                    ("moyen", "MODERE"), ("faible", "MINEUR"))
        for risque, attendu in attendus:
            rapport = dict(RAPPORT_SCAN, risque=risque)
            self.assertEqual(lire_scan(rapport, 9).gravite, attendu)

    def test_lire_scan_cle_manquante(self):
        for cle in ("id_faille", "paquet", "risque", "date"):
            rapport = dict(RAPPORT_SCAN)
            del rapport[cle]
            with self.assertRaises(ValueError):
                lire_scan(rapport, 9)

    def test_lire_build(self):
        sig = lire_build(RAPPORT_BUILD, 8)
        self.assertEqual(sig.ref, "SH-0008")
        self.assertEqual(sig.date, "2026-11-27T17:08:00Z")
        self.assertEqual(sig.origine, "BUILD")
        self.assertEqual(sig.service, "deploiement")
        self.assertEqual(sig.env, "production")
        self.assertEqual(sig.categorie, "BUILD_ECHEC")
        self.assertEqual(sig.gravite, "MAJEUR")
        self.assertEqual(sig.texte, "Build deploiement : echec")

    def test_lire_build_reussite(self):
        rapport = dict(RAPPORT_BUILD, etape="tests", resultat="succes")
        sig = lire_build(rapport, 8)
        self.assertEqual(sig.categorie, "BUILD_OK")
        self.assertEqual(sig.gravite, "MINEUR")
        self.assertEqual(sig.texte, "Build tests : succes")

    def test_lire_build_cle_manquante(self):
        for cle in ("etape", "resultat", "date"):
            rapport = dict(RAPPORT_BUILD)
            del rapport[cle]
            with self.assertRaises(ValueError):
                lire_build(rapport, 8)


if __name__ == "__main__":
    unittest.main()
