"""Accès IMAP : lecture et déplacement des messages.

Règle absolue du projet : aucun message n'est jamais supprimé.
Un message n'est retiré de la boîte de réception qu'après avoir été copié
avec succès dans son dossier de destination, et seulement par UID MOVE ou
UID EXPUNGE ciblé sur ce seul message. Les messages sont lus avec BODY.PEEK
pour ne pas les marquer comme lus.
"""
import email
import imaplib
import re
from dataclasses import dataclass, field
from email.policy import default as default_policy

from . import security


@dataclass
class MessageSummary:
    uid: str
    sender: str
    subject: str
    date: str
    body: str = ""
    signals: list[str] = field(default_factory=list)
    surely_suspect: bool = False


_LIST_NAME = re.compile(r'(?:"((?:[^"\\]|\\.)*)"|(\S+))\s*$')


_BODY_CHARS = 1500
_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")


def _body_preview(msg) -> str:
    """Début du texte du message, sans pièces jointes ni balises HTML."""
    part = None
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        text = part.get_content() if part else ""
    except (KeyError, LookupError, ValueError, AttributeError):
        text = ""
    if part is not None and part.get_content_subtype() == "html":
        text = _TAGS.sub(" ", text)
    return _SPACES.sub(" ", text).strip()[:_BODY_CHARS]


def _quote(name: str) -> str:
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


class MailboxClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.conn = imaplib.IMAP4_SSL(host, port)
        self.conn.login(user, password)
        # Les capacités peuvent changer après authentification : on les relit.
        typ, data = self.conn.capability()
        self.capabilities = set(data[0].decode().upper().split()) if data and data[0] else set()

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

    def inbox_messages(self, limit: int, readonly: bool = True) -> list[MessageSummary]:
        """Résumés des messages de la boîte de réception, les plus récents d'abord.

        Le dossier reste sélectionné ensuite ; il faut readonly=False pour déplacer.
        """
        self.conn.select("INBOX", readonly=readonly)
        typ, data = self.conn.uid("SEARCH", None, "ALL")
        uids = data[0].split()[-limit:][::-1] if data and data[0] else []
        result = []
        for uid in uids:
            # Les 64 premiers Ko suffisent pour l'en-tête et le début du texte.
            typ, parts = self.conn.uid("FETCH", uid, "(BODY.PEEK[]<0.65536>)")
            raw = next((p[1] for p in parts if isinstance(p, tuple)), b"")
            msg = email.message_from_bytes(raw, policy=default_policy)
            signals, certain = security.analyze(msg)
            result.append(MessageSummary(
                uid=uid.decode(),
                sender=str(msg.get("From", "")),
                subject=str(msg.get("Subject", "")),
                date=str(msg.get("Date", "")),
                body=_body_preview(msg),
                signals=signals,
                surely_suspect=certain,
            ))
        return result

    def move(self, uid: str, folder: str) -> bool:
        """Déplace un message de la boîte de réception vers folder.

        Renvoie False si le message n'a été que copié (serveur sans MOVE ni
        UIDPLUS) : il reste alors dans la boîte de réception, rien n'est perdu.
        """
        caps = self.capabilities
        if "MOVE" in caps:
            typ, data = self.conn.uid("MOVE", uid, _quote(folder))
            if typ != "OK":
                raise RuntimeError(f"Déplacement de {uid} impossible : {data}")
            return True
        typ, data = self.conn.uid("COPY", uid, _quote(folder))
        if typ != "OK":
            raise RuntimeError(f"Copie de {uid} impossible : {data}")
        if "UIDPLUS" not in caps:
            # Un EXPUNGE global effacerait aussi d'autres messages : on s'abstient.
            return False
        self.conn.uid("STORE", uid, "+FLAGS.SILENT", r"(\Deleted)")
        self.conn.uid("EXPUNGE", uid)
        return True
