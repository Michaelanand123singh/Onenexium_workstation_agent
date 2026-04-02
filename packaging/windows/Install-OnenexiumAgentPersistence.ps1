#Requires -Version 5.1
<#
.SYNOPSIS
  Registers Windows Scheduled Tasks so OnenexiumAgent keeps running for this user.

.DESCRIPTION
  - OnenexiumAgent-Logon: starts the agent when this user signs in (after reboot).
  - OnenexiumAgent-Watchdog: every 10 minutes, starts the agent if it is not running
    (e.g. after Task Manager "End task").

  Run in the employee's Windows session (double-click or: powershell -ExecutionPolicy Bypass -File .\Install-...ps1).
  Administrator rights are NOT required (tasks are created for the current user only).

  LIMITATION: Foreground-window telemetry must run in the user session. When this user
  fully logs off, the agent stops until they log in again. There is no supported way to
  capture the interactive user's foreground apps while they are logged off.

.PARAMETER AgentExe
  Full path to OnenexiumAgent.exe. Default: OnenexiumAgent.exe next to this script.
#>
param(
    [string] $AgentExe = ""
)

$ErrorActionPreference = "Stop"

if (-not $AgentExe) {
    $AgentExe = Join-Path $PSScriptRoot "OnenexiumAgent.exe"
}
if (-not (Test-Path -LiteralPath $AgentExe)) {
    Write-Error "OnenexiumAgent.exe not found at: $AgentExe`nUse -AgentExe 'C:\full\path\OnenexiumAgent.exe'"
}
$AgentExe = (Resolve-Path -LiteralPath $AgentExe).Path

$dataDir = Join-Path $env:APPDATA "OnenexiumAgent"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

$watchdogPath = Join-Path $dataDir "watchdog.ps1"
$exeForPs = $AgentExe.Replace("'", "''")
$watchdogBody = @"
`$ErrorActionPreference = 'SilentlyContinue'
if (-not (Get-Process -Name 'OnenexiumAgent' -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath '$exeForPs' -ArgumentList 'run' -WindowStyle Hidden
}
"@
Set-Content -LiteralPath $watchdogPath -Value $watchdogBody -Encoding UTF8

$taskLogon = "OnenexiumAgent-Logon"
$taskWatch = "OnenexiumAgent-Watchdog"

Unregister-ScheduledTask -TaskName $taskLogon -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $taskWatch -Confirm:$false -ErrorAction SilentlyContinue

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

$actionLogon = New-ScheduledTaskAction -Execute $AgentExe -Argument "run"
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName $taskLogon -Action $actionLogon -Trigger $triggerLogon `
    -Settings $settings -Description "Onenexium workstation agent at user logon" | Out-Null

$psArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$watchdogPath`""
$actionWatch = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $psArgs
$start = (Get-Date).AddMinutes(1)
$triggerWatch = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 36525)
Register-ScheduledTask -TaskName $taskWatch -Action $actionWatch -Trigger $triggerWatch `
    -Settings $settings -Description "Restart Onenexium agent if it was killed" | Out-Null

Write-Host "Installed scheduled tasks for current user:"
Write-Host "  - $taskLogon (at sign-in)"
Write-Host "  - $taskWatch (every 10 min if not running)"
Write-Host ""
Write-Host "Starting agent once now..."
Start-Process -FilePath $AgentExe -ArgumentList "run" -WindowStyle Hidden
Write-Host "Done. Logs (packaged build): $dataDir\agent.log"
