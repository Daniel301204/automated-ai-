param(
 [string]$TargetDirectory = 'D:\LIBA course\new model\job_agent_mvp',
 [string]$SourceDirectory = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath (Join-Path $SourceDirectory 'agent.py'))) { throw 'Source agent.py missing' }
if (!(Test-Path -LiteralPath $TargetDirectory)) { throw 'Target directory missing. Create the folder or use the correct existing path.' }
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path (Split-Path -Parent $TargetDirectory) ("job_agent_mvp_backup_" + $timestamp)
Copy-Item -LiteralPath $TargetDirectory -Destination $backup -Recurse
Write-Host "Original project backed up to $backup"
$codeFiles = @('agent.py','job_discovery.py','application_routing.py','streamlit_app.py','requirements.txt','run_daily.ps1','install_scheduler.ps1','README.md','.env.example')
foreach ($file in $codeFiles) {
 $source = Join-Path $SourceDirectory $file
 if (Test-Path -LiteralPath $source) {
   Copy-Item -LiteralPath $source -Destination (Join-Path $TargetDirectory $file) -Force
 }
}
Write-Host 'Upgrade installed. User profile, tokens, .env, resume, database, and logs were NOT overwritten.'
