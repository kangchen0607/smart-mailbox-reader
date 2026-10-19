# Installe (ou met à jour) la tâche planifiée qui trie les mails chaque jour.
# Usage : powershell -ExecutionPolicy Bypass -File installer-tache.ps1 [-Heure 08:00]
param([string]$Heure = "08:00")

$ErrorActionPreference = "Stop"
$dossier = $PSScriptRoot
$nom = "Tri des mails (smart-mailbox-reader)"

if (-not (Test-Path "$dossier\.venv\Scripts\python.exe")) {
    throw "Environnement .venv introuvable : suivez d'abord l'installation du README."
}
if (-not (Test-Path "$dossier\.env")) {
    throw "Fichier .env introuvable : suivez d'abord l'installation du README."
}

$action = New-ScheduledTaskAction -Execute "$dossier\tri-quotidien.bat" -WorkingDirectory $dossier
$declencheur = New-ScheduledTaskTrigger -Daily -At $Heure
# Si le PC était éteint à l'heure prévue, le tri se lance dès que possible ensuite.
$reglages = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $nom -Action $action -Trigger $declencheur -Settings $reglages `
    -Description "Trie la boîte mail entre Important et Moins important (aucune suppression)." `
    -Force | Out-Null

Write-Host "Tâche « $nom » installée : tous les jours à $Heure."
Write-Host "Tester maintenant : Start-ScheduledTask -TaskName '$nom'  puis lire logs\tri.log"
