@echo off
cd /d "%~dp0"

if not exist "venv" (
    python -m venv venv
)

call .\venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

set PYTHONPATH=%~dp0
start "" python src\main.py
start "" python fleet_monitor.py