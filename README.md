# smart-mailbox-reader

Agent qui se connecte chaque jour à une boîte IMAP (Free) et range les mails
entre deux dossiers : **Important** et **Moins important**.

> Règle absolue : aucun message n'est jamais supprimé, ils sont seulement déplacés.

## État actuel (étape 3)

Connexion IMAP, création des deux dossiers s'ils manquent, puis tri des
derniers messages de la boîte de réception par l'IA (Claude Haiku) selon vos
critères personnels. Avec `--apply`, chaque mail est déplacé dans son dossier
et noté dans le journal `deplacements.csv` (ouvrable dans Excel).
En cas de doute ou d'erreur, le mail reste dans la boîte de réception.
Le tri peut tourner automatiquement une fois par jour via le Planificateur de tâches.

## Installation sous Windows 11

1. Installer Python 3.11 ou plus récent depuis https://www.python.org (cocher « Add Python to PATH »).
2. Dans un terminal (PowerShell), à la racine du dépôt :
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
3. Ouvrir `.env` et renseigner `IMAP_USER`, `IMAP_PASSWORD` et `ANTHROPIC_API_KEY`.
   Chez Free, l'IMAP doit être activé dans l'espace abonné (Paramètres de la messagerie).
4. Copier `criteres.example.txt` en `criteres.txt` et y décrire, en langage courant,
   ce qui est important pour vous (`copy criteres.example.txt criteres.txt`).

## Utilisation

Depuis le dossier du dépôt (là où se trouve `run.py`), environnement activé :

```powershell
py run.py          # mode essai : affiche le tri proposé, ne déplace rien
py run.py --apply  # crée les dossiers et déplace réellement les mails
```

Le mode essai appelle quand même l'IA (quelques centimes pour 50 mails avec Haiku) :
c'est l'occasion d'ajuster `criteres.txt` avant le premier vrai tri.

## Exécution quotidienne automatique

Une fois le tri vérifié à la main avec `py run.py --apply`, installer la tâche
planifiée (PowerShell, à la racine du dépôt, sans droits administrateur) :

```powershell
powershell -ExecutionPolicy Bypass -File installer-tache.ps1            # tous les jours à 08:00
powershell -ExecutionPolicy Bypass -File installer-tache.ps1 -Heure 19:30
```

- Le tri tourne tant que votre session Windows est ouverte (une fenêtre noire apparaît quelques secondes).
- Si le PC était éteint à l'heure prévue, le tri se lance au prochain démarrage.
- Chaque passage est consigné dans `logs\tri.log` ; les déplacements restent dans `deplacements.csv`.
- Lancer un tri tout de suite : `Start-ScheduledTask -TaskName "Tri des mails (smart-mailbox-reader)"`.
- Désinstaller : `Unregister-ScheduledTask -TaskName "Tri des mails (smart-mailbox-reader)"`.

Ne déplacez pas le dossier du dépôt après l'installation (sinon relancez `installer-tache.ps1`).
