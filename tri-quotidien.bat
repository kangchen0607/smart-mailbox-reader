@echo off
rem Tri quotidien lancé par le Planificateur de tâches Windows.
rem La sortie de chaque passage est ajoutée à logs\tri.log.
cd /d "%~dp0"
if not exist logs mkdir logs
set PYTHONUTF8=1
echo ===== %date% %time% ===== >> logs\tri.log
".venv\Scripts\python.exe" run.py --apply >> logs\tri.log 2>&1
echo Code retour : %errorlevel% >> logs\tri.log
