"""Chargement de la configuration depuis le fichier .env."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    user: str
    password: str
    folder_important: str
    folder_less_important: str
    folder_suspect: str
    max_messages: int
    anthropic_api_key: str
    model: str
    criteria: str
    move_log: str


def _read_criteria(path: str) -> str:
    """Lit le fichier de critères (sinon l'exemple fourni), sans les lignes en #."""
    for candidate in (Path(path), Path("criteres.example.txt")):
        if candidate.is_file():
            lines = candidate.read_text(encoding="utf-8").splitlines()
            return "\n".join(l for l in lines if not l.lstrip().startswith("#")).strip()
    return ""


def load_config() -> Config:
    load_dotenv()
    missing = [k for k in ("IMAP_USER", "IMAP_PASSWORD", "ANTHROPIC_API_KEY") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Variables manquantes dans .env : {', '.join(missing)}")
    return Config(
        host=os.getenv("IMAP_HOST", "imap.free.fr"),
        port=int(os.getenv("IMAP_PORT", "993")),
        user=os.environ["IMAP_USER"],
        password=os.environ["IMAP_PASSWORD"],
        folder_important=os.getenv("FOLDER_IMPORTANT", "Important"),
        folder_less_important=os.getenv("FOLDER_LESS_IMPORTANT", "Moins important"),
        folder_suspect=os.getenv("FOLDER_SUSPECT", "Messages suspects"),
        max_messages=int(os.getenv("MAX_MESSAGES", "50")),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"),
        criteria=_read_criteria(os.getenv("CRITERIA_FILE", "criteres.txt")),
        move_log=os.getenv("MOVE_LOG", "deplacements.csv"),
    )
