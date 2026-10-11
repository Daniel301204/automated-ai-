param(
    [string]$AppUrl = 'https://5dasesqq5hdkocoz5dupwp.streamlit.app/'
)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root
$Helper = Join-Path $Root 'configure_hosting.py'
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (Test-Path $Python) {
    & $Python $Helper --app-url $AppUrl
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 $Helper --app-url $AppUrl
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Helper --app-url $AppUrl
} else {
    throw 'Install Python 3.12 from python.org, then run this helper again.'
}
if ($LASTEXITCODE -ne 0) {
    throw 'Settings preparation stopped. Read the message above; existing private settings were preserved.'
}
$SecretsFile = Join-Path $Root '.streamlit\secrets.toml'
if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
    Set-Clipboard -Value ([System.IO.File]::ReadAllText($SecretsFile))
    Write-Host 'Private settings copied to your clipboard. Paste only into Streamlit app settings -> Secrets.' -ForegroundColor Green
} else {
    Write-Host 'Open .streamlit\secrets.toml privately and copy its contents into Streamlit app settings -> Secrets.' -ForegroundColor Green
}
Write-Host 'Save the Streamlit secrets and restart the app. Keep the encryption key unchanged on future updates.'
Start-Process 'https://share.streamlit.io/'
