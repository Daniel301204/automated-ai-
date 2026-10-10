$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Install Python 3.12 first.'"
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 from python.org, then run this launcher again.' }
        & python -m venv .venv
    } else {
        throw 'Install Python 3.12 from python.org, then run this launcher again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the environment. Install Python 3.12 and retry.' }
}

& $Python -c "import sys; assert sys.version_info[:2] == (3, 12), 'This launcher requires Python 3.12.'"
if ($LASTEXITCODE -ne 0) { throw 'Use a Python 3.12 environment for this project.' }
& $Python -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the displayed error and your internet connection.' }
& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed. Check the displayed error.' }
& $Python (Join-Path $Root 'run_local.py')
exit $LASTEXITCODE
