@echo off
cd /d "%~dp0"
pythonw desktop_app.py
if errorlevel 1 (
    echo CV Optimiser did not start. Make sure Python and project dependencies are installed.
    pause
)
