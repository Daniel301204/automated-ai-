param([string]$TargetDirectory = 'D:\LIBA course\new model\job_agent_mvp')
$ErrorActionPreference = 'Stop'
$Source = $PSScriptRoot
if (!(Test-Path $TargetDirectory)) { New-Item -ItemType Directory -Path $TargetDirectory -Force | Out-Null }
$BackupDir = Join-Path $TargetDirectory ('backups\autojob_verified_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Files = @('streamlit_app.py','live_sources.py','resume_match.py','job_store.py','START_WEBSITE.ps1','WEBSITE_README.md')
foreach ($file in $Files) {
  $src = Join-Path $Source $file
  if (!(Test-Path $src)) { throw "Missing package file: $file" }
  $dest = Join-Path $TargetDirectory $file
  if (Test-Path $dest) { Copy-Item $dest (Join-Path $BackupDir $file) -Force }
  Copy-Item $src $dest -Force
}
$Requirements = Join-Path $TargetDirectory 'requirements.txt'
if (Test-Path $Requirements) { Copy-Item $Requirements (Join-Path $BackupDir 'requirements.txt') -Force }
$Existing = if (Test-Path $Requirements) { @(Get-Content $Requirements) } else { @() }
foreach ($req in @('streamlit>=1.36,<2','pandas>=2,<3','requests>=2.32,<3','beautifulsoup4>=4.12,<5','pypdf>=5,<7','python-docx>=1.1,<2')) {
  $name = ($req -split '[<>=]')[0]
  if (-not ($Existing | Where-Object { $_ -match ('^' + [regex]::Escape($name) + '\s*[<>=]') })) { $Existing += $req }
}
$Existing | Set-Content $Requirements -Encoding utf8
Write-Host "Installed AutoJob AI into $TargetDirectory" -ForegroundColor Green
Write-Host "Code backups: $BackupDir"
Write-Host 'Unchanged: .env, profile.json, OAuth credentials, resume files, data, and logs.'
