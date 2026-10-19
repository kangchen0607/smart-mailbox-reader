"""Point d'entrée : py run.py [--apply]

Par défaut le script tourne en mode essai : il ne modifie rien sur le serveur.
"""
import argparse

from . import move_log
from .classifier import IMPORTANT, SUSPECT, Classification, Classifier
from .config import load_config
from .imap_client import MailboxClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Tri intelligent de la boîte mail")
    parser.add_argument("--apply", action="store_true",
                        help="Applique réellement les changements (sinon mode essai)")
    args = parser.parse_args()
    dry_run = not args.apply
    cfg = load_config()

    print(f"Connexion à {cfg.host} en tant que {cfg.user}"
          f"{' (mode essai, rien ne sera modifié)' if dry_run else ''}")
    with MailboxClient(cfg.host, cfg.port, cfg.user, cfg.password) as client:
        for folder in (cfg.folder_suspect, cfg.folder_important, cfg.folder_less_important):
            if client.ensure_folder(folder, dry_run):
                print(f"Dossier {folder!r} {'à créer' if dry_run else 'créé'}")
            else:
                print(f"Dossier {folder!r} déjà présent")

        if not cfg.criteria:
            print("Aucun fichier de critères trouvé : règles générales seulement.")
        classifier = Classifier(cfg.anthropic_api_key, cfg.model, cfg.criteria)

        messages = client.inbox_messages(cfg.max_messages, readonly=dry_run)
        print(f"\n{len(messages)} message(s) à trier dans la boîte de réception :")
        counts = {cfg.folder_suspect: 0, cfg.folder_important: 0,
                  cfg.folder_less_important: 0, "erreur": 0}
        folders = {SUSPECT: cfg.folder_suspect, IMPORTANT: cfg.folder_important}
        for m in messages:
            label = f"[{m.uid}] {m.sender[:30]} | {m.subject[:50]}"
            try:
                if m.surely_suspect:  # première passe : pas besoin de l'IA
                    c = Classification(SUSPECT, "; ".join(m.signals))
                else:
                    c = classifier.classify(m.sender, m.subject, m.body, m.signals)
            except Exception as e:  # le mail reste simplement dans la boîte de réception
                counts["erreur"] += 1
                print(f"  ?  {label}\n     classement impossible, laissé en place : {e}")
                continue
            folder = folders.get(c.category, cfg.folder_less_important)
            counts[folder] += 1
            print(f"  -> {folder:<17} {label}\n     {c.reason}")
            if dry_run:
                continue
            try:
                status = "déplacé" if client.move(m.uid, folder) else "copié (laissé en boîte de réception)"
            except Exception as e:
                status = f"échec : {e}"
                print(f"     {status}")
            move_log.append(cfg.move_log, m.uid, m.sender, m.subject, folder, c.reason, status)

        print("\nBilan : " + ", ".join(f"{k} : {v}" for k, v in counts.items()))
        if dry_run:
            print("Mode essai : aucun mail déplacé. Relancer avec --apply pour trier.")
        else:
            print(f"Journal des déplacements : {cfg.move_log}")


if __name__ == "__main__":
    main()
