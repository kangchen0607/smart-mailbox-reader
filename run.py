"""Lanceur : py run.py [--apply]"""
import os
from pathlib import Path

from smart_mailbox.main import main

if __name__ == "__main__":
    # .env, criteres.txt et deplacements.csv sont lus/écrits à côté de ce fichier,
    # même quand le Planificateur de tâches lance le script depuis un autre dossier.
    os.chdir(Path(__file__).resolve().parent)
    main()
