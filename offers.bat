@echo off
REM Offers OSS - double-click to open your daily cockpit, or run "offers <command>" from this folder.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python is not installed. Get it from https://www.python.org/downloads/ & pause & exit /b 1)
python -c "import openpyxl, yaml" 2>nul || python -m pip install -r requirements.txt
if not exist "tracker\OffersOSS_Tracker.xlsx" python offers.py setup
if "%~1"=="" (python offers.py go) else (python offers.py %*)
if "%~1"=="" pause
