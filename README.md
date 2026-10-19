# smart-mailbox-reader

Agent qui se connecte chaque jour à une boîte IMAP (Free) et range les mails
entre deux dossiers : **Important** et **Moins important**.

> Règle absolue : aucun message n'est jamais supprimé, ils sont seulement déplacés.

## État actuel (étape 1)

Connexion IMAP, création des deux dossiers s'ils manquent, et lecture des
derniers messages de la boîte de réception (sans les marquer comme lus).
Le tri par IA et le déplacement arrivent aux étapes suivantes.

## Installation sous Windows 11

1. Installer Python 3.11 ou plus récent depuis https://www.python.org (cocher « Add Python to PATH »).
2. Dans un terminal (PowerShell), à la racine du dépôt :
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
3. Ouvrir `.env` et renseigner `IMAP_USER` et `IMAP_PASSWORD`.
   Chez Free, l'IMAP doit être activé dans l'espace abonné (Paramètres de la messagerie).

## Utilisation

```powershell
py -m smart_mailbox.main          # mode essai : n'écrit rien sur le serveur
py -m smart_mailbox.main --apply  # crée réellement les dossiers manquants
```
