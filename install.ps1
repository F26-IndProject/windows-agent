# install.ps1
# =====================
# LISA Windows Agent - Setup Script
#
# HOW TO RUN:
#   Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy RemoteSigned -Command `"Set-Location -Path '$PWD'; & '.\install.ps1'`"" -Verb RunAs
# Ask for inputs upfront
$PlainPassword = Read-Host -Prompt "Enter the login password for $env:USERNAME"
$ServerIP      = Read-Host -Prompt "Enter the LISA Server IP address"
Write-Host ""
Write-Host "=== LISA Windows Agent - Setup ===" -ForegroundColor Cyan
Write-Host ""
# 1. Install Python dependencies
Write-Host "[1/9] Installing Python dependencies..."
pip install -r requirements.txt
# 2. Run makepy
Write-Host "[2/9] Running makepy - when the window appears, click Cancel or close it..."
python -m win32com.client.makepy
# 3. Compile agent
Write-Host "[3/9] Compiling agent..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller --onefile --name agent `
    --hidden-import win32com.client `
    --hidden-import win32com.shell `
    --hidden-import pythoncom `
    --hidden-import psycopg2 `
    --hidden-import yaml `
    --hidden-import requests `
    --hidden-import psutil `
    --hidden-import win32gui `
    --hidden-import win32process `
    --hidden-import win32con `
    --hidden-import dotenv `
    agent.py
# 4. Copy attachments to dist
Write-Host "[4/9] Copying attachments..."
Copy-Item -Path "attachments" -Destination "dist\attachments" -Recurse -Force
# 5. Setup autostart scheduled task
Write-Host "[5/9] Setting up autostart..."
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.\setup_autostart.ps1
# 6. Enable auto-login
Write-Host "[6/9] Enabling auto-login..."
$reg = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
$ComputerSystem = Get-CimInstance -ClassName Win32_ComputerSystem
$DomainRole     = $ComputerSystem.DomainRole
$IsDomainJoined = $DomainRole -in 3, 4, 5
Set-ItemProperty -Path $reg -Name AutoAdminLogon  -Value "1"
Set-ItemProperty -Path $reg -Name DefaultUsername -Value $env:USERNAME
Set-ItemProperty -Path $reg -Name DefaultPassword -Value $PlainPassword
# Terminate conflicting legacy ForceAutoLogon registry values completely
Remove-ItemProperty -Path $reg -Name ForceAutoLogon -ErrorAction SilentlyContinue
if ($IsDomainJoined) {
    Write-Host "    Domain environment detected ($($ComputerSystem.Domain)). Setting DefaultDomainName." -ForegroundColor Yellow
    Set-ItemProperty -Path $reg -Name DefaultDomainName -Value $ComputerSystem.Domain
} else {
    Write-Host "    Local workgroup environment detected. Setting DefaultDomainName to local machine." -ForegroundColor Yellow
    Set-ItemProperty -Path $reg -Name DefaultDomainName -Value $env:COMPUTERNAME
}
# Globally disable the Windows Workstation Lock feature to prevent headless disconnection locking
$SysPolicies = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
Set-ItemProperty -Path $SysPolicies -Name "DisableLockWorkstation" -Value 1
Set-ItemProperty -Path $SysPolicies -Name "DisableCAD" -Value 1
# 7. Disable sleep and hibernate
Write-Host "[7/9] Disabling sleep and hibernate..."
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0
# 8. Configure RDP and OpenSSH
Write-Host "[8/9] Configuring RDP and OpenSSH..."
$TSPath = "HKLM:\System\CurrentControlSet\Control\Terminal Server"
Set-ItemProperty -Path $TSPath -Name "fDenyTSConnections" -Value 0
Set-ItemProperty -Path $TSPath -Name "fSingleSessionPerUser" -Value 1
Set-ItemProperty -Path $TSPath -Name "fLeaveSessionRunning" -Value 1
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 0
# FIX: Reverted to 0 to preserve original verified working custom security layer mapping
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "SecurityLayer" -Value 0
Enable-NetFirewallRule -DisplayName "File and Printer Sharing (Echo Request - ICMPv4-In)"
$sshStatus = Get-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
if ($sshStatus.State -ne "Installed") {
    Write-Host "    OpenSSH Server not found. Downloading from Windows Update (this may take a few minutes)..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -Verbose
} else {
    Write-Host "    OpenSSH Server already installed - skipping." -ForegroundColor Green
}
# Unconditionally enforce, re-verify parameters, and boot the OpenSSH background daemon
Set-Service -Name sshd -StartupType "Automatic" -ErrorAction SilentlyContinue
Restart-Service sshd -Force -ErrorAction SilentlyContinue
# FIX: Dynamically targets the unblocking engine via $PWD to avoid blank variable properties or hardcoded user folders
if (Test-Path "$PWD\sshpass.exe") {
    Unblock-File -Path "$PWD\sshpass.exe" -ErrorAction SilentlyContinue
}
# 9. Configure hosts file
Write-Host "[9/9] Configuring hosts file..."
$hostsPath  = "$env:windir\System32\drivers\etc\hosts"
$hostsEntry = "$ServerIP  mail.lisa.local  lisa.local"
if (-not (Get-Content $hostsPath | Select-String -SimpleMatch $hostsEntry)) {
    Add-Content -Path $hostsPath -Value "`n$hostsEntry"
} else {
    Write-Host "    Hosts entry already exists - skipping." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  - Import the server certificate"
Write-Host "  - Configure Outlook"
Write-Host "  - Reboot Windows"
Start-Sleep -Seconds 3
exit