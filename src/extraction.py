import re

from src.contrat import Signal

# Parametres sensibles dont la valeur doit etre masquee (casse ignoree).
PARAMETRES_SENSIBLES = ("password", "pwd", "token", "secret", "card", "iban")

MASQUE = "[MASQUE]"

# nom + separateur + valeur ; la valeur s'arrete a un espace, &, , ou ;
RE_SENSIBLE = re.compile(
    r"\b(" + "|".join(PARAMETRES_SENSIBLES) + r")(\s*[=:]\s*)([^\s&,;]*)",
    re.IGNORECASE,
)

# Niveau du journal -> gravite du signal.
GRAVITES_JOURNAL = {
    "FATAL": "BLOQUANT",
    "CRITICAL": "BLOQUANT",
    "ERROR": "MAJEUR",
    "WARN": "MODERE",
    "WARNING": "MODERE",
}

# Risque du scan -> gravite du signal.
GRAVITES_SCAN = {
    "critique": "BLOQUANT",
    "haut": "MAJEUR",
    "moyen": "MODERE",
}


def masquer_donnees(texte: str) -> str:
    """Remplace la valeur des parametres sensibles par [MASQUE]."""
    return RE_SENSIBLE.sub(r"\1\2" + MASQUE, texte)


def lire_journal(ligne: str, numero: int, origine: str = "PAIEMENT",
                 env: str = "production") -> Signal:
    """Transforme une ligne de journal en Signal."""
    champs = ligne.split(None, 4)
    if len(champs) < 5:
        raise ValueError("ligne de journal incomplete : 5 champs attendus")
    date, heure, service, niveau, texte = champs
    return Signal(
        ref=f"SH-{numero:04d}",
        date=f"{date}T{heure}Z",
        origine=origine,
        service=service,
        env=env,
        categorie="JOURNAL",
        gravite=GRAVITES_JOURNAL.get(niveau.upper(), "MINEUR"),
        texte=masquer_donnees(texte),
    )


def lire_scan(rapport: dict, numero: int, env: str = "production") -> Signal:
    """Transforme un rapport de scan en Signal."""
    try:
        id_faille = rapport["id_faille"]
        paquet = rapport["paquet"]
        risque = rapport["risque"]
        date = rapport["date"]
    except KeyError as erreur:
        raise ValueError(f"cle manquante dans le rapport de scan : {erreur}") from erreur
    return Signal(
        ref=f"SH-{numero:04d}",
        date=date,
        origine="SCANNER",
        service=paquet,
        env=env,
        categorie="FAILLE",
        gravite=GRAVITES_SCAN.get(str(risque).lower(), "MINEUR"),
        texte=f"Faille {id_faille} dans {paquet}",
    )


def lire_build(rapport: dict, numero: int, env: str = "production") -> Signal:
    """Transforme un rapport de build en Signal."""
    try:
        etape = rapport["etape"]
        resultat = rapport["resultat"]
        date = rapport["date"]
    except KeyError as erreur:
        raise ValueError(f"cle manquante dans le rapport de build : {erreur}") from erreur
    echec = str(resultat).lower() == "echec"
    return Signal(
        ref=f"SH-{numero:04d}",
        date=date,
        origine="BUILD",
        service=etape,
        env=env,
        categorie="BUILD_ECHEC" if echec else "BUILD_OK",
        gravite="MAJEUR" if echec else "MINEUR",
        texte=f"Build {etape} : {resultat}",
    )
