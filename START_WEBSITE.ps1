$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3 -m venv .venv }
$Python = Join-Path $Root '.venv\Scripts\python.exe'
& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check network and Python.' }
if (-not (Test-Path (Join-Path $Root 'streamlit_app.py'))) {throw 'streamlit_app.py is missing from the extracted folder.'}
Write-Host 'Starting AutoJob AI (not the old Streamlit app) at http://localhost:8502' -ForegroundColor Green
& $Python -m streamlit run (Join-Path $Root 'streamlit_app.py') --server.port 8502 --server.address 127.0.0.1
