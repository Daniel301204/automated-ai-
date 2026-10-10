@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START_LOOPINGCV.ps1"
if errorlevel 1 (
    echo LoopingCV stopped or could not start. Read the error above.
    pause
)
