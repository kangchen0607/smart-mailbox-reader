"""Chargement de la configuration depuis le fichier .env."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    user: str
    password: str
    folder_important: str
    folder_less_important: str
    max_messages: int


def load_config() -> Config:
    load_dotenv()
    missing = [k for k in ("IMAP_USER", "IMAP_PASSWORD") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Variables manquantes dans .env : {', '.join(missing)}")
    return Config(
        host=os.getenv("IMAP_HOST", "imap.free.fr"),
        port=int(os.getenv("IMAP_PORT", "993")),
        user=os.environ["IMAP_USER"],
        password=os.environ["IMAP_PASSWORD"],
        folder_important=os.getenv("FOLDER_IMPORTANT", "Important"),
        folder_less_important=os.getenv("FOLDER_LESS_IMPORTANT", "Moins important"),
        max_messages=int(os.getenv("MAX_MESSAGES", "50")),
    )
