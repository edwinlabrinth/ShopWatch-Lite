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


def masquer_donnees(texte: str) -> str:
    """Remplace la valeur des parametres sensibles par [MASQUE]."""
    return RE_SENSIBLE.sub(r"\1\2" + MASQUE, texte)


def lire_journal(ligne: str, numero: int, origine: str = "PAIEMENT",
                 env: str = "production") -> Signal:
    raise NotImplementedError


def lire_scan(rapport: dict, numero: int, env: str = "production") -> Signal:
    raise NotImplementedError


def lire_build(rapport: dict, numero: int, env: str = "production") -> Signal:
    raise NotImplementedError
