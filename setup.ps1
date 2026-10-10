$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3 -m venv .venv }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
foreach ($name in @('profile.json','boards.json','approved_contacts.json')) {
  if (-not (Test-Path $name)) { Copy-Item ($name -replace '\.json$','.example.json') $name }
}
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host 'Setup complete. Edit .env/profile.json/boards.json and launch Streamlit.'
