
from src.contrat import Diagnostic, Message, Signal


def choisir_canal(niveau: str) -> str:
    canaux = {
        "BLOQUANT": "SLACK",
        "MAJEUR": "TEAMS",
        "MODERE": "EMAIL",
        "MINEUR": "TABLEAU",
    }

    if niveau not in canaux:
        raise ValueError(f"Niveau inconnu : {niveau}")

    return canaux[niveau]


def composer(sig: Signal, diag: Diagnostic) -> str:
    lignes = [
        f"*** {diag.niveau} *** Service : {sig.service}",
        f"Constat : {sig.texte}",
        f"Cause : {diag.cause}",
        f"A faire : {diag.action}",
        f"Origines : {' + '.join(diag.origines)}",
    ]

    return "\n".join(lignes)


def diffuser(sig: Signal, diag: Diagnostic, registre: list) -> Message:
    canal = choisir_canal(diag.niveau)
    destinataire = "astreinte-shop"

    contenu = composer(sig, diag)

    message = Message(
        signal_ref=sig.ref,
        canal=canal,
        destinataire=destinataire,
        contenu=contenu,
    )

    registre.append(message)
    sig.etat = "DIFFUSE"

    return message


def approuver(diag: Diagnostic, reponse: str) -> bool:
    if not diag.critique:
        return True

    return reponse.strip().upper() in ("O", "OUI", "OK", "YES")


def consigner(
    diag: Diagnostic,
    accord: bool,
    responsable: str,
    carnet: list,
    instant: str,
) -> dict:
    entree = {
        "ref": diag.signal_ref,
        "action": diag.action,
        "accord": accord,
        "responsable": responsable,
        "instant": instant,
    }

    carnet.append(entree)

    return entree
