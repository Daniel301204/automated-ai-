@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0CONFIGURE_STREAMLIT.ps1"
if errorlevel 1 (
    echo Setup stopped. Read the message above.
    pause
)
