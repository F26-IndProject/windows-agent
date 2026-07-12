# LISA Windows Agent — Setup Guide

## Prerequisites

Before starting, make sure you have:

- Windows 10 or Windows 11
- Network connectivity to the LISA Server
- Microsoft Office installed (Word, Excel, Outlook)
- VS Code installed — download from [Visual Studio Code](https://code.visualstudio.com/download)
- Adobe Acrobat Reader installed — download from [Get Adobe Acrobat Reader](https://get.adobe.com/reader/)
- Python 3.11 installed — download from [python.org](https://www.python.org/)
- Git installed — download from [git-scm.com](https://git-scm.com/)
- Agent email account already created on the LISA Server — [Read Part 4 of the Mailserver Repo (Managing email accounts)](https://github.com/F26-IndProject/mailserver/)

When installing Python, tick **"Add python.exe to PATH"** before clicking Install. Without this, pip will not be found.

---

## 1. Verify Python and pip

Open PowerShell and run:

```powershell
python --version
pip --version
```

Both should return version numbers. If pip is not found, close PowerShell completely and open a new Powershell as an Administrator. If still not found, run:

```powershell
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LOCALAPPDATA\Programs\Python\Python311;$env:LOCALAPPDATA\Programs\Python\Python311\Scripts", "Machine")
```

If Git if not recognised after installing it, open Powershell as an Administrator and manulally add git to PATH, close the windows and re-open powershell to run your commands 

```powershell
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:ProgramFiles\Git\cmd", "Machine")
```

---

## 2. Clone the Windows Agent Repository

Open PowerShell and run:

```powershell
git clone https://github.com/F26-IndProject/windows-agent.git
cd "$env:USERPROFILE\windows-agent"
```

---

## 3. Configure the Environment and Add Attachments

Configure the `.env` file with the same values used when setting up the LISA Server.

```powershell
notepad .env
```

Save and close when done.

Put all your images and PDFs in the `attachments` folder. The agent will randomly pick attachments from it when sending emails. After the script runs, they will be copied to `dist\attachments`.

---

## 4. Run the Installation Script

```powershell
Start-Process powershell -ArgumentList "-ExecutionPolicy RemoteSigned -Command `"Set-Location -Path '$PWD'; & '.\install.ps1'`"" -Verb RunAs
```

The script will prompt for:
- **Login password** — used to enable auto-login on reboot
- **LISA Server IP** — used to configure the hosts file

> **Note:** During step 2 of the script, a window will appear asking you to select a library. **Click Cancel or close the window** — this is expected behaviour.

The script will then:
- Install Python dependencies
- Compile the agent
- Copy attachments to `dist\attachments`
- Set up the autostart scheduled task
- Enable auto-login
- Configure RDP and OpenSSH
- Update the hosts file

---

## 5. Adding the Server Certificate to the Trust Store

On the LISA Server, start a temporary HTTP server:

```bash
python3 -m http.server 9999 --directory /etc/ssl/mail
```

On the Windows agent, download the certificate:

```powershell
Invoke-WebRequest -Uri "http://LISA_SERVER_IP:9999/mail.lisa.local.crt" -OutFile "$env:USERPROFILE\mail.lisa.local.crt"
```

Add it to the trust store:

```powershell
Start-Process powershell -ArgumentList "-ExecutionPolicy RemoteSigned -Command `"Import-Certificate -FilePath '$env:USERPROFILE\mail.lisa.local.crt' -CertStoreLocation Cert:\LocalMachine\Root`"" -Verb RunAs
```

---

## 6. Adding a Local Email Account

You need to set up the agent's email account on the LISA Server before configuring Outlook.
Follow this guide: [Read Part 4 of the Mailserver Repo (Managing email accounts)](https://github.com/F26-IndProject/mailserver/)

---

## 7. Configuring Outlook

### Outlook (Windows Agents)

**Incoming mail (IMAP):**

| Setting    | Value           |
|------------|-----------------|
| Server     | mail.lisa.local |
| Email      | your@lisa.local |
| Port       | 993             |
| Encryption | SSL/TLS         |

**Outgoing mail (SMTP):**

| Setting    | Value           |
|------------|-----------------|
| Server     | mail.lisa.local |
| Port       | 587             |
| Encryption | STARTTLS        |

---

## Disable Warning for Programmatic Access (Important)

1. Close the Ouylook windows from above and Run Outlook again as administrator.
2. Go to **File > Options > Trust Center > Trust Center Settings > Programmatic Access**.
3. Select **Never warn me about suspicious activity (not recommended)** and click **OK**.

---

## Default Apps for Images and PDF

Open the `attachments` folder and open an image file — when the **"How do you want to open this file?"** dialog appears, select **Photos** and click **Always**. This sets Photos as the permanent default for images.

Do the same for a PDF file — open it and select **Adobe Acrobat Reader** when prompted, then click **Always**.

This only needs to be done once per machine.

---

***Now, reboot the Windows agent to apply all changes and start the agent automatically.***

---

## Process Tree Verification

To verify the process tree:

```powershell
Get-WmiObject Win32_Process | Select-Object Name, ProcessId, ParentProcessId, @{Name="ParentName";Expression={($_.GetOwnerProcess().Name)}} | Where-Object {$_.Name -match "WINWORD|EXCEL|msedge|powershell|OUTLOOK|Photos|Acrobat|cmd|firefox|code|rdp|mstsc|wfreerdp|log|runner"}
```

To inspect a specific process by ID:

```powershell
Get-Process -Id <ID>
```

---

## In Case the Agent Needs to Be Recompiled

Stop the agent first:

```powershell
Stop-ScheduledTask -TaskName "LISA Agent"
```

Then rerun the script. After it finishes:

```powershell
Start-ScheduledTask -TaskName "LISA Agent"
```

```powershell
cd "$env:USERPROFILE\windows-agent"
```

Remove older compilations first:

```powershell
Remove-Item -Recurse -Force build, dist
```

Then compile:

```powershell
pyinstaller --onefile --name agent --hidden-import win32com.client --hidden-import win32com.shell --hidden-import pythoncom --hidden-import psycopg2 --hidden-import yaml --hidden-import requests --hidden-import psutil --hidden-import win32gui --hidden-import win32process --hidden-import win32con --hidden-import dotenv agent.py
```

Copy the attachments folder into the dist directory:

```powershell
Copy-Item -Path "attachments" -Destination "dist\attachments" -Recurse -Force
```

After compiling, the agent executable will be at `dist\agent.exe`.