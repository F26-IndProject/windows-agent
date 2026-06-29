# setup_autostart.ps1
# =====================
# Run this script ONCE as Administrator to register the LISA agent
# as a Windows Scheduled Task that starts automatically when the user logs in.
#
# After running this, every time Windows boots and the user logs in,
# the agent starts automatically — no manual action needed.
#
# HOW TO RUN:
#   1. Open PowerShell as Administrator
#      (Right-click Start -> Windows Terminal (Admin))
#   2. Navigate to the windows-agent folder:
#      cd C:\Users\%USERNAME%\windows-agent
#   3. Allow script execution (one-time):
#      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   4. Run this script:
#      .\setup_autostart.ps1
#
# HOW TO VERIFY IT WORKED:
#   Open Task Scheduler (search for it in Start Menu)
#   Look for "LISA Agent" under Task Scheduler Library
#
# HOW TO REMOVE IT:
#   Unregister-ScheduledTask -TaskName "LISA Agent" -Confirm:$false
# ─── CONFIGURATION ────────────────────────────────────────────────────────────
$AGENT_DIR   = "C:\Users\$env:USERNAME\windows-agent"
$AGENT_EXE   = Join-Path $AGENT_DIR "dist\agent.exe"
# ────────────────────────────────────────────────────────────────────────────────
Write-Host "=== LISA Agent Autostart Setup ===" -ForegroundColor Cyan
# Verify agent executable exists
if (-not (Test-Path $AGENT_EXE)) {
    Write-Host "ERROR: Agent executable not found at: $AGENT_EXE" -ForegroundColor Red
    exit 1
}
Write-Host "Agent executable found: $AGENT_EXE" -ForegroundColor Green
# Create logs directory if needed
New-Item -ItemType Directory -Force -Path (Join-Path $AGENT_DIR "logs") | Out-Null
# ─── CREATE THE SCHEDULED TASK ────────────────────────────────────────────────
$Action = New-ScheduledTaskAction -Execute $AGENT_EXE -WorkingDirectory $AGENT_DIR
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$ExistingTask = Get-ScheduledTask -TaskName "LISA Agent" -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName "LISA Agent" -Confirm:$false
    Write-Host "Removed existing LISA Agent task" -ForegroundColor Yellow
}
Register-ScheduledTask -TaskName "LISA Agent" -Description "LISA user behaviour simulation agent" -Action $Action -Trigger $Trigger -Settings $Settings -RunLevel Limited -Force
Write-Host ""
Write-Host "SUCCESS: LISA Agent scheduled task created." -ForegroundColor Green
Write-Host ""
Write-Host "The agent will start automatically next time $env:USERNAME logs in." -ForegroundColor Cyan
Write-Host ""
Write-Host "To start it now without rebooting:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'LISA Agent'" -ForegroundColor White
Write-Host ""
Write-Host "To check if it is running:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName 'LISA Agent'" -ForegroundColor White
Write-Host ""
Write-Host "To stop it:" -ForegroundColor Yellow
Write-Host "  Stop-ScheduledTask -TaskName 'LISA Agent'" -ForegroundColor White