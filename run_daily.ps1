$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'logs') | Out-Null
$log = Join-Path $PSScriptRoot ('logs\daily_' + (Get-Date -Format yyyyMMdd_HHmmss) + '.log')
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'agent.py') *> $log
exit $LASTEXITCODE
