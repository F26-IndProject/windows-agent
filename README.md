# LISA Windows Agent — Setup Guide

## Prerequisites

Before starting, make sure you have:

- Windows 10 or Windows 11
- Network connectivity to the LISA Server
- Microsoft Office installed (Word, Excel, Outlook)
- Python 3.11 installed — download from [python.org](https://www.python.org)
- Git installed — download from [git-scm.com](https://git-scm.com)

> When installing Python, tick **"Add python.exe to PATH"** before clicking Install. Without this, pip will not be found.

---

## 1. Verify Python and pip are working

Open PowerShell and run:

```powershell
python --version
pip --version
```

Both should return version numbers. If pip is not found, close PowerShell completely and open a new one. If still not found, run:

```powershell
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311;C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts", "Machine")
```

Close and reopen PowerShell, then test again.

---

## 2. Clone the Windows Agent Repository

Open PowerShell and run:

```powershell
git clone git@github.com:F26-IndProject/windows-agent.git
cd C:\Users\$env:USERNAME\windows-agent
```

---

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

> This may take some time to complete. If nothing seems to be happening after 2 minutes, click the down arrow in the PowerShell window — the terminal may appear stuck even after installation has finished.

After pywin32 installs, run this one extra step:

```powershell
python -m win32com.client.makepy
```

> When prompted to select a library, just click **Cancel** or close the window.

---

## 4. Configure the Environment File

Configure the `.env` file with the same values used when setting up the LISA Server.

---

## 5. Add Attachments

Put all your images and PDFs in the `attachments` folder. The agent will randomly pick attachments from it when sending emails.

---

## 6. Compile the Agent

If you have older compilations, remove them first:

```powershell
Remove-Item -Recurse -Force build, dist
```

Then compile:

```powershell
pyinstaller --onefile --name agent --hidden-import win32com.client --hidden-import win32com.shell --hidden-import pythoncom --hidden-import psycopg2 --hidden-import yaml --hidden-import requests --hidden-import psutil --hidden-import win32gui --hidden-import win32process --hidden-import win32con --hidden-import dotenv agent.py
```

Copy the attachments folder into the dist directory:

```powershell
xcopy /E /I attachments dist\attachments
```

After compiling, the agent executable will be at `dist\agent.exe`.

---

## 7. Set Up Autostart with Scheduled Task

Open PowerShell as Administrator (right-click Start → Windows Terminal (Admin)):

```powershell
cd C:\Users\$env:USERNAME\windows-agent
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_autostart.ps1
```

> When prompted about execution policy, type `Y` and press Enter.

Verify the task was created:

```powershell
Get-ScheduledTask -TaskName "LISA Agent"
```

---

## 8. Enable Auto-Login

For the agent to run without anyone typing a password on reboot, enable auto-login.

Open PowerShell as Administrator:

```powershell
$reg = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
Set-ItemProperty -Path $reg -Name AutoAdminLogon -Value "1"
Set-ItemProperty -Path $reg -Name DefaultUsername -Value "your-windows-user"
Set-ItemProperty -Path $reg -Name DefaultPassword -Value "YourPasswordHere"
```

Replace `your-windows-user` and `YourPasswordHere` with the actual username and password for that Windows system.

---

## 9. Configure the Agent to Accept RDP Connections from Other Agents

Run the following commands in PowerShell as Administrator:

```powershell
# Enable Remote Desktop
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Allow through firewall
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# Disable Network Level Authentication (so agents can connect without NLA)
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 0

# Enable ping through firewall
Enable-NetFirewallRule -DisplayName "File and Printer Sharing (Echo Request - ICMPv4-In)"
```

---

## 10. DNS, SSL, and Application Configuration

### 10.1 DNS Configuration

Open Notepad as Administrator and edit:

```
C:\Windows\System32\drivers\etc\hosts
```

Add the following line:

```
LISA_SERVER_IP  mail.lisa.local  lisa.local
```

**Example:**

```
192.168.100.10  mail.lisa.local  lisa.local
```

For more details, see [Windows Agent DNS Configuration](https://github.com/F26-IndProject/mailserver#part-1-configuring-local-dns-records).

---

### 10.2 Adding the Server Certificate to the Trust Store

On the LISA Server, start a temporary HTTP server:

```bash
python3 -m http.server 9999 --directory /etc/ssl/mail
```

On the Windows agent, run PowerShell as Administrator:

```powershell
Invoke-WebRequest -Uri "http://LISA_SERVER_IP:9999/mail.lisa.local.crt" -OutFile "$env:USERPROFILE\mail.lisa.local.crt"
Import-Certificate -FilePath "$env:USERPROFILE\mail.lisa.local.crt" -CertStoreLocation Cert:\LocalMachine\Root
```

For more details, see [Adding SSL Certificate to Trust Store](https://github.com/F26-IndProject/mailserver#distribute-the-certificate-to-agents).

---

### 10.3 Adding a Local Email Account

To add a new agent email account on the server, follow this guide: [Adding a New Local Email Account](https://github.com/F26-IndProject/mailserver#part-5-adding-a-new-email-account).

---

### 10.4 Configuring Outlook

To set up the email account in Outlook, follow this guide: [Logging into Email Account on Outlook](https://github.com/F26-IndProject/mailserver#part-6-configuring-email-clients).

---

### 10.5 Install Required Applications

Install the following applications on the Windows agent:

- [Visual Studio Code](https://code.visualstudio.com)
- [Adobe Acrobat Reader](https://get.adobe.com/reader)

---

## Process Verification

To verify the agent is running correctly and check the process tree:

```powershell
Get-WmiObject Win32_Process | Select-Object Name, ProcessId, ParentProcessId, @{Name="ParentName";Expression={($_.GetOwnerProcess().Name)}} | Where-Object {$_.Name -match "WINWORD|EXCEL|msedge|powershell|OUTLOOK|Photos|Acrobat|cmd|firefox|code|rdp|mstsc|wfreerdp|log|runner"}
```

To inspect a specific process by ID:

```powershell
Get-Process -Id <ID>
```