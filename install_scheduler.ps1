param([string]$Time = '09:00')
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'run_daily.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $script + '"') -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'AutoJob AI Agent' -Action $action -Trigger $trigger -Settings $settings -Description 'Authorized daily job analysis and email automation' -Force
