from src.contrat import Diagnostic, Signal


def est_repete(sig: Signal, vus: set) -> bool:
    cle = (sig.date, sig.origine, sig.service, sig.categorie, sig.texte)
    if cle in vus:
        return True
    vus.add(cle)
    return False


def compter_incidents(sig: Signal, compteur: dict) -> int:
    if sig.categorie != "JOURNAL" or sig.gravite not in ("MAJEUR", "BLOQUANT"):
        return 0
    compteur[sig.service] = compteur.get(sig.service, 0) + 1
    return compteur[sig.service]


def chercher_fiches(sig: Signal, base: dict) -> list:
    texte = sig.texte.lower()
    return [conseil for cle, conseil in base.items() if cle.lower() in texte]


def evaluer(sig: Signal, nb_incidents: int = 0) -> str:
    if nb_incidents >= 4:
        return "BLOQUANT"
    return sig.gravite


def diagnostiquer(sig: Signal, base: dict, nb_incidents: int = 0) -> Diagnostic:
    niveau = evaluer(sig, nb_incidents)
    fiches = chercher_fiches(sig, base)
    cause = " ; ".join(fiches) if fiches else "Cause inconnue : verification manuelle"
    if sig.categorie == "FAILLE":
        action = f"Corriger la dependance {sig.service}"
    elif sig.categorie == "BUILD_ECHEC":
        action = f"Rejouer le build {sig.service}"
    elif niveau == "BLOQUANT":
        action = f"Isoler le service {sig.service}"
    else:
        action = "Observer"
    sig.etat = "EVALUE"
    return Diagnostic(sig.ref, niveau, cause, action,
                      action.startswith("Isoler"), [sig.origine])
