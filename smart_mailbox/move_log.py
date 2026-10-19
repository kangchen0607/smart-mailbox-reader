"""Journal des déplacements, au format CSV (ouvrable dans Excel)."""
import csv
from datetime import datetime
from pathlib import Path

_HEADER = ["date_tri", "uid", "expediteur", "objet", "dossier", "raison", "statut"]


def append(path: str, uid: str, sender: str, subject: str,
           folder: str, reason: str, status: str) -> None:
    file = Path(path)
    new = not file.exists()
    with file.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if new:
            writer.writerow(_HEADER)
        writer.writerow([datetime.now().isoformat(timespec="seconds"),
                         uid, sender, subject, folder, reason, status])
