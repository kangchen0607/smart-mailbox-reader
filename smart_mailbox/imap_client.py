"""Accès IMAP en lecture seule pour l'instant.

Règle absolue du projet : aucun message n'est jamais supprimé.
Ce module n'utilise ni le drapeau \\Deleted ni EXPUNGE, et lit les
messages avec BODY.PEEK pour ne pas les marquer comme lus.
"""
import email
import imaplib
import re
from dataclasses import dataclass
from email.policy import default as default_policy


@dataclass
class MessageSummary:
    uid: str
    sender: str
    subject: str
    date: str


_LIST_NAME = re.compile(r'(?:"((?:[^"\\]|\\.)*)"|(\S+))\s*$')


def _quote(name: str) -> str:
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


class MailboxClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.conn = imaplib.IMAP4_SSL(host, port)
        self.conn.login(user, password)

    def close(self) -> None:
        try:
            self.conn.logout()
        except imaplib.IMAP4.error:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def list_folders(self) -> list[str]:
        typ, data = self.conn.list()
        folders = []
        for raw in data or []:
            # Format : (\Flags) "délimiteur" "Nom" ou Nom sans guillemets
            m = _LIST_NAME.search(raw.decode(errors="replace"))
            if m:
                folders.append(m.group(1).replace('\\"', '"') if m.group(1) is not None else m.group(2))
        return folders

    def ensure_folder(self, name: str, dry_run: bool) -> bool:
        """Crée le dossier s'il n'existe pas. Renvoie True s'il a fallu le créer."""
        if name in self.list_folders():
            return False
        if not dry_run:
            typ, data = self.conn.create(_quote(name))
            if typ != "OK":
                raise RuntimeError(f"Création du dossier {name!r} impossible : {data}")
            self.conn.subscribe(_quote(name))
        return True

    def inbox_messages(self, limit: int) -> list[MessageSummary]:
        """Résumés des messages de la boîte de réception, les plus récents d'abord."""
        self.conn.select("INBOX", readonly=True)
        typ, data = self.conn.uid("SEARCH", None, "ALL")
        uids = data[0].split()[-limit:][::-1] if data and data[0] else []
        result = []
        for uid in uids:
            typ, parts = self.conn.uid(
                "FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            raw = next((p[1] for p in parts if isinstance(p, tuple)), b"")
            msg = email.message_from_bytes(raw, policy=default_policy)
            result.append(MessageSummary(
                uid=uid.decode(),
                sender=str(msg.get("From", "")),
                subject=str(msg.get("Subject", "")),
                date=str(msg.get("Date", "")),
            ))
        return result
