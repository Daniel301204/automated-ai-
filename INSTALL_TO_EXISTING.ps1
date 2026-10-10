param([string]$TargetDirectory = 'D:\LIBA course\AutoJob_Verified_Release')
$ErrorActionPreference='Stop'
$src=$PSScriptRoot
if (!(Test-Path -LiteralPath (Join-Path $TargetDirectory 'streamlit_app.py'))) { throw "Existing AutoJob website not found at $TargetDirectory" }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path (Split-Path -Parent $TargetDirectory) ("AutoJob_Verified_Release_backup_"+$stamp)
Copy-Item -LiteralPath $TargetDirectory -Destination $backup -Recurse
Write-Host "Backup created: $backup"
foreach($name in @('streamlit_app.py','guarded_upgrade.py','requirements.txt')) {
  Copy-Item -LiteralPath (Join-Path $src $name) -Destination (Join-Path $TargetDirectory $name) -Force
}
Write-Host 'Upgrade installed. No .env, credentials, profile.json, data, or resume files replaced.'
