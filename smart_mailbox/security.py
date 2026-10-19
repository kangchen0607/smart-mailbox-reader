"""Première passe : repérage des expéditeurs suspects (hameçonnage, usurpation).

Les signaux viennent des en-têtes du message. Un échec DMARC, ou SPF et DKIM
tous deux en échec, suffit à classer le mail comme suspect sans appeler l'IA.
Les autres signaux sont transmis à l'IA, qui tranche.
"""
import re
from email.utils import getaddresses, parseaddr

# Marques souvent imitées : nom recherché dans le domaine -> domaines officiels.
_BRANDS = {
    "paypal": ("paypal.com", "paypal.fr"),
    "impots": ("impots.gouv.fr", "dgfip.finances.gouv.fr"),
    "ameli": ("ameli.fr", "assurance-maladie.fr"),
    "caf": ("caf.fr",),
    "laposte": ("laposte.fr", "laposte.net", "labanquepostale.fr"),
    "free": ("free.fr", "freetelecom.fr", "free-mobile.fr", "iliad.fr"),
    "amazon": ("amazon.fr", "amazon.com", "amazon.de", "amazonses.com"),
    "netflix": ("netflix.com",),
    "microsoft": ("microsoft.com", "outlook.com", "live.com", "office.com"),
    "apple": ("apple.com", "icloud.com"),
    "antai": ("antai.gouv.fr",),
    "chronopost": ("chronopost.fr",),
    "colissimo": ("colissimo.fr", "laposte.fr"),
}
_AUTH = re.compile(r"\b(spf|dkim|dmarc)\s*=\s*(\w+)", re.I)
_EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")


def _domain(address: str) -> str:
    return address.rpartition("@")[2].lower().strip(" >.")


def _same_org(a: str, b: str) -> bool:
    """Vrai si les deux domaines partagent les deux derniers niveaux (ex. x.free.fr / free.fr)."""
    return a.split(".")[-2:] == b.split(".")[-2:]


def _auth_results(msg) -> dict[str, str]:
    """Résultats SPF/DKIM/DMARC du premier en-tête Authentication-Results (celui du serveur de réception)."""
    header = msg.get_all("Authentication-Results") or []
    results = {}
    if header:
        for kind, value in _AUTH.findall(str(header[0])):
            results.setdefault(kind.lower(), value.lower())
    return results


def analyze(msg) -> tuple[list[str], bool]:
    """Renvoie (signaux de suspicion en français, suspect_certain)."""
    signals = []
    name, address = parseaddr(str(msg.get("From", "")))
    domain = _domain(address)

    auth = _auth_results(msg)
    failed = [k.upper() for k, v in auth.items() if v in ("fail", "softfail", "permerror")]
    if failed:
        signals.append("authentification en échec : " + ", ".join(failed))
    certain = auth.get("dmarc") == "fail" or (
        auth.get("spf") == "fail" and auth.get("dkim") == "fail")

    reply_to = [a for _, a in getaddresses([str(v) for v in msg.get_all("Reply-To") or []]) if a]
    for addr in reply_to:
        if domain and not _same_org(_domain(addr), domain):
            signals.append(f"réponse redirigée vers un autre domaine ({_domain(addr)})")
            break

    shown = _EMAIL.search(name or "")
    if shown and domain and not _same_org(_domain(shown.group(0)), domain):
        signals.append(f"le nom affiché contient une autre adresse ({shown.group(0)})")

    if "xn--" in domain:
        signals.append(f"domaine en caractères internationaux, possible imitation ({domain})")
    for brand, official in _BRANDS.items():
        if brand in re.split(r"[.-]", domain):
            if not any(domain == o or domain.endswith("." + o) for o in official):
                signals.append(f"domaine imitant {brand} ({domain})")
                break
    return signals, certain
