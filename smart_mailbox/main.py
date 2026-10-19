"""Point d'entrée : python -m smart_mailbox.main [--apply]

Par défaut le script tourne en mode essai : il ne modifie rien sur le serveur.
"""
import argparse

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
        for folder in (cfg.folder_important, cfg.folder_less_important):
            if client.ensure_folder(folder, dry_run):
                print(f"Dossier {folder!r} {'à créer' if dry_run else 'créé'}")
            else:
                print(f"Dossier {folder!r} déjà présent")

        messages = client.inbox_messages(cfg.max_messages)
        print(f"\n{len(messages)} message(s) lus dans la boîte de réception :")
        for m in messages:
            print(f"  [{m.uid}] {m.date[:16]} | {m.sender[:40]} | {m.subject[:60]}")


if __name__ == "__main__":
    main()
