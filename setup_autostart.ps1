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
#   2. Navigate to the WinAgent folder:
#      cd C:\Users\bob\WinAgent
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
# Change AGENT_DIR to the actual path where you put the WinAgent files
$AGENT_DIR   = "C:\Users\$env:USERNAME\WinAgent"
$PYTHON_PATH = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
$AGENT_SCRIPT = Join-Path $AGENT_DIR "agent.py"
$LOG_FILE    = Join-Path $AGENT_DIR "logs\startup.log"
# ────────────────────────────────────────────────────────────────────────────────

Write-Host "=== LISA Agent Autostart Setup ===" -ForegroundColor Cyan

# Verify Python is available
if (-not $PYTHON_PATH) {
    Write-Host "ERROR: Python not found on PATH. Install Python and tick 'Add to PATH'." -ForegroundColor Red
    exit 1
}
Write-Host "Python found: $PYTHON_PATH" -ForegroundColor Green

# Verify agent script exists
if (-not (Test-Path $AGENT_SCRIPT)) {
    Write-Host "ERROR: Agent script not found at: $AGENT_SCRIPT" -ForegroundColor Red
    Write-Host "Make sure you cloned the WinAgent repo to $AGENT_DIR" -ForegroundColor Yellow
    exit 1
}
Write-Host "Agent script found: $AGENT_SCRIPT" -ForegroundColor Green

# Create logs directory if needed
New-Item -ItemType Directory -Force -Path (Join-Path $AGENT_DIR "logs") | Out-Null

# ─── CREATE THE SCHEDULED TASK ────────────────────────────────────────────────
# The task runs python.exe agent.py when the current user logs on.
# RunLevel = Limited means it runs as a normal user — NOT as administrator.
# This is correct: we want the agent to behave like a normal user.
# The task's parent process will be taskhost.exe/svchost.exe — not a terminal.
# This satisfies the "agent must not be parent of launched apps" requirement
# at the process-creation level.

$Action = New-ScheduledTaskAction `
    -Execute $PYTHON_PATH `
    -Argument "agent.py" `
    -WorkingDirectory $AGENT_DIR

# AtLogOn means the task fires when THIS user logs into Windows
$Trigger = New-ScheduledTaskTrigger `
    -AtLogOn `
    -User "$env:USERDOMAIN\$env:USERNAME"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # 0 = no time limit

# Register the task (replaces it if it already exists)
$ExistingTask = Get-ScheduledTask -TaskName "LISA Agent" -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName "LISA Agent" -Confirm:$false
    Write-Host "Removed existing LISA Agent task" -ForegroundColor Yellow
}

Register-ScheduledTask `
    -TaskName "LISA Agent" `
    -Description "LISA user behaviour simulation agent" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Limited `
    -Force

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
