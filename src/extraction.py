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
    raise NotImplementedError


def lire_build(rapport: dict, numero: int, env: str = "production") -> Signal:
    raise NotImplementedError
