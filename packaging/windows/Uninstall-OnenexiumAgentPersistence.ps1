#Requires -Version 5.1
Unregister-ScheduledTask -TaskName "OnenexiumAgent-Logon" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "OnenexiumAgent-Watchdog" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Removed Onenexium scheduled tasks (current user)."
Get-Process -Name "OnenexiumAgent" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "Stopped any running OnenexiumAgent.exe processes."
