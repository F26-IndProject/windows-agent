# LISA Windows Agent — Setup Guide

Complete step-by-step guide for deploying the LISA Windows agent on a target Windows VM. Every command is included and explained.

---

## Requirements Covered

| Requirement | Status | How |
|---|---|---|
| Run as assigned user account | ✅ | Scheduled Task with RunLevel=Limited |
| Auto-start on reboot | ✅ | Windows Scheduled Task at logon |
| Launched apps NOT agent's children | ✅ | ShellExecute + COM automation |
| Work schedule respected | ✅ | is_work_time() check in main loop |
| Heartbeat to server | ✅ | Background thread every 5 minutes |
| Activities logged to dashboard | ✅ | Direct PostgreSQL connection via psycopg2 |
| Browse Google, Bing, Yandex | ✅ | open_browser action in role YAML |
| MS Word — create documents | ✅ | COM automation via pywin32 |
| MS Excel — create spreadsheets | ✅ | COM automation via pywin32 |
| Outlook — read inbox and send email | ✅ | COM automation via pywin32 |
| SMB network share access | ✅ | net use + file operations |
| RDP connections (admin role) | ✅ | mstsc.exe via ShellExecute |
| PowerShell / CMD commands | ✅ | terminal.py with ShellExecute |
| Registry access (admin role) | ✅ | Python winreg module |
| Scheduled task creation (admin) | ✅ | PowerShell New-ScheduledTask |

---

## Prerequisites

Before starting, make sure you have:

- Windows 10 or Windows 11 VM in VMware
- Network connectivity to the LISA Server VM
- Microsoft Office installed (Word, Excel, Outlook)
- Python 3.11 installed — download from python.org
- Git installed — download from git-scm.com
- consider that server IP is 192.168.100.10

When installing Python, tick **"Add python.exe to PATH"** before clicking Install. Without this, pip will not be found.

---

## 1. Verify Python and pip are working

Open PowerShell and run:

```
python --version
pip --version
```

Both should return version numbers. If pip is not found, close PowerShell completely and open a new one. If still not found, run:

```
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311;C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts", "Machine")
```

Close and reopen PowerShell, then test again.

---

## 2. Cloning the windows-agent repo

Open PowerShell and run the command below:

```
git clone git@github.com:F26-IndProject/windows-agent.git
cd windows-agent
```

The final structure must look like this:

```
windows-agent\
    agent.py
    requirements.txt
    setup_autostart.ps1
    SETUP.md
    actions\
        __init__.py
        apps.py
        office.py
        smb.py
        rdp.py
        registry.py
        terminal.py
    client\
        __init__.py
        server_api.py
        database.py
    config\
        settings.yaml
        paths.yaml
    roles\
        user.yaml
        admin.yaml
        dev.yaml
    utils\
        __init__.py
        logger.py
    logs\
```

The `__init__.py` files are critical. Without them Python cannot import from those folders.

---

## 3. Copy all files into the correct folders

Download all files from the repository and place them exactly as shown in the structure above. Every file must be in its correct folder.

---

## 4. Install Python dependencies

Navigate to the windows-agent folder and install:

```
cd C:\Users\$env:USERNAME\windows-agent
pip install -r requirements.txt
```

This installs:
- `requests` — HTTP communication with the server
- `pyyaml` — reading YAML config and role files
- `psycopg2-binary` — direct PostgreSQL connection (same as Linux agent)
- `pywin32` — Windows COM automation for Word, Excel, Outlook

After pywin32 installs, run this one extra step:

```
python -m win32com.client.makepy
```

A small window may appear — close it or click OK. This pre-generates COM type libraries for Office.

---

## 5. Configure the server IP

Open `config\settings.yaml` with Notepad:

```
notepad C:\Users\$env:USERNAME\windows-agent\config\settings.yaml
```

Verify `server_ip` is set to your actual server VM IP:

```yaml
server_ip: "192.168.100.10"
server_port: 8000
```

Also open `agent.py` and confirm the same IP is set at the top:

```python
SERVER_IP = "192.168.100.10"
```

Also verify in `client\database.py`:

```python
DB_CONFIG = {
    "host": "192.168.100.10",
    "password": "PASSWORD-HERE"
}
```

All three must match your actual server VM IP and database password.

---

## 6. Configure the role

Open `config\settings.yaml`:

```
notepad C:\Users\$env:USERNAME\windows-agent\config\settings.yaml
```

Set the role to one of:
- `user` — office worker (Word, Excel, Outlook, browser, SMB)
- `dev` — developer (VSCode, PowerShell, GitHub, Stack Overflow)
- `admin` — system administrator (PowerShell, registry, RDP, SMB, scheduled tasks)

Example for office worker:

```yaml
role: user
work_days: [1, 2, 3, 4, 5]
work_start: "09:00"
work_end: "18:00"
activity_interval_min: 120
activity_interval_max: 300
```

---

## 7. Verify Office application paths

Open `config\paths.yaml` and check that the Word, Excel, and Outlook paths match what is installed on your VM.

To find the real Word path, run in PowerShell:

```
Get-ChildItem "C:\Program Files*" -Recurse -Filter WINWORD.EXE -ErrorAction SilentlyContinue | Select-Object FullName
```

Update `paths.yaml` with whatever path that returns.

---

## 8. Verify connectivity to the server

Test that the Windows VM can reach the server:

```
python -c "import requests; r = requests.get('http://192.168.100.10:8000/api/health'); print(r.status_code, r.json())"
```

Should print `200` and a JSON status object. If it fails, check that the server VM is running and the backend Docker container is up.

Also test direct database connectivity:

```
python -c "import psycopg2; c = psycopg2.connect(host='192.168.100.10', port=5432, database='lisa_dev', user='lisa', password='lisa_password_2026'); print('DB connected'); c.close()"
```

Should print `DB connected`.

---

## 9. Test the agent manually

Always test manually before setting up autostart. Navigate to the folder and run:

```
cd C:\Users\$env:USERNAME\windows-agent
python agent.py --debug
```

The `--debug` flag clears old log files and lock files so you get a clean start.

Watch the output. You should see:

```
Lock file created: agent_...lock
LISA Windows Agent starting
Loaded role: user
Connected to PostgreSQL database directly
Heartbeat thread started
Running action: word_document
Activity logged to DB: word_document
```

Check the server dashboard at `http://192.168.100.10:3000/agents` — the Windows agent should appear as active with activities showing in the Recent activity list.

To change working hours for testing (so activities run at any time), edit `config\settings.yaml`:

```yaml
work_start: "00:00"
work_end: "23:59"
work_days: [1, 2, 3, 4, 5, 6, 7]
```

Stop the agent with Ctrl+C when done testing. If Ctrl+C does not stop it, open a second PowerShell window and run:

```
Get-Process python | Stop-Process -Force
del C:\Users\$env:USERNAME\windows-agent\*.lock
```

---

## 10. Verify the parent process requirement

While the agent is running and has opened an application, open a second PowerShell window and run:

```
Get-WmiObject Win32_Process | Select-Object Name, ProcessId, ParentProcessId | Sort-Object Name | Where-Object {$_.Name -match "WINWORD|firefox|msedge|powershell"}
```

Note the ParentProcessId of any launched application. Then check what that parent is:

```
Get-WmiObject Win32_Process | Where-Object {$_.ProcessId -eq <ParentProcessId>} | Select-Object Name, ProcessId
```

Replace `<ParentProcessId>` with the actual number.

Expected results:
- WINWORD.EXE parent should be `svchost.exe` (DCOM launcher)
- msedge.exe or firefox.exe parent should be `explorer.exe` or a short-lived shell helper
- powershell.exe parent should be `explorer.exe`

The agent `python.exe` must NOT appear as a parent of any of these. If it does, ShellExecute or COM is not being used correctly.

---

## 11. Set up autostart with Scheduled Task

Open PowerShell **as Administrator** (right-click Start → Windows Terminal (Admin)):

```
cd C:\Users\$env:USERNAME\windows-agent
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_autostart.ps1
```

When prompted about execution policy, type `Y` and press Enter.

You should see green success messages. Verify the task was created:

```
Get-ScheduledTask -TaskName "LISA Agent"
```

Start it immediately without rebooting:

```
Start-ScheduledTask -TaskName "LISA Agent"
```

To stop it:

```
Stop-ScheduledTask -TaskName "LISA Agent"
```

To remove it:

```
Unregister-ScheduledTask -TaskName "LISA Agent" -Confirm:$false
```

---

## 12. Enable auto-login

For the agent to run without anyone typing a password on reboot, enable auto-login.

Open PowerShell as Administrator:

```
$reg = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
Set-ItemProperty -Path $reg -Name AutoAdminLogon -Value "1"
Set-ItemProperty -Path $reg -Name DefaultUsername -Value "LISA-WINDOWS"
Set-ItemProperty -Path $reg -Name DefaultPassword -Value "YourPasswordHere"
```

Replace `LISA-WINDOWS` and `YourPasswordHere` with the actual username and password.

After rebooting: Windows logs in automatically → Scheduled Task fires → agent starts → activities begin.

---

## 13. Reboot test

Reboot the VM:

```
Restart-Computer
```

After reboot, wait 3-5 minutes then check the server dashboard. The agent should appear as active without you doing anything manually. The `Last seen` timestamp should be recent and `Recent activity` should show actions the agent performed.

---

## Troubleshooting

**Agent exits with "Agent already running"**

A lock file from a previous run exists. Delete it:

```
del C:\Users\$env:USERNAME\windows-agent\*.lock
```

**ModuleNotFoundError: No module named 'psycopg2'**

```
pip install psycopg2-binary
```

**ModuleNotFoundError: No module named 'win32com'**

```
pip install pywin32
python -m win32com.client.makepy
```

**Word/Excel/Outlook COM fails with "Cannot connect"**

Outlook requires a configured mail account. Without one, outlook_read and outlook_email actions will fail. Other actions (Word, Excel, browser, PowerShell) are not affected.

**Database connection failed**

- Verify server VM is running: `ping 192.168.100.10`
- Verify backend container is up: SSH to server, run `sudo docker compose ps`
- Verify the password in `client\database.py` matches `docker-compose.yml` on the server
- Verify port 5432 is reachable: `Test-NetConnection -ComputerName 192.168.100.10 -Port 5432`

**Heartbeat succeeds but no activities in dashboard**

This means the direct database connection is failing while the API heartbeat works. Check the PowerShell output for "Connected to PostgreSQL database directly". If that line is missing, the database connection failed — see database troubleshooting above.

**Activities show in database but dashboard shows only heartbeats**

This is a known backend limitation — the API heartbeat endpoint saves all records with activity_type = "heartbeat". Direct database connection bypasses this. Make sure `client\database.py` exists in the `client\` folder and that `psycopg2-binary` is installed.

**Scheduled Task exists but agent does not start after reboot**

- Verify auto-login is configured correctly in the registry
- Verify Python is on PATH for all users (not just the current session)
- Check Task Scheduler history: open Task Scheduler → LISA Agent → History tab
- Try running the task manually: `Start-ScheduledTask -TaskName "LISA Agent"`

**SMB access fails**

- Verify a Samba share exists on the server VM
- Test manually: `net use Z: \\192.168.100.10\share /persistent:no`
- If it fails, configure the share on the server VM first

**RDP fails to connect**

- Enable Remote Desktop on the target: Settings → System → Remote Desktop → Enable
- Verify port 3389: `Test-NetConnection -ComputerName 192.168.100.10 -Port 3389`

---

## File reference

| File | Purpose |
|---|---|
| `agent.py` | Main agent — reads config, runs activities, manages heartbeat and database |
| `actions\apps.py` | Opens applications via ShellExecute (satisfies parent-process requirement) |
| `actions\office.py` | Word, Excel, Outlook via COM automation |
| `actions\smb.py` | SMB network share access using net use |
| `actions\rdp.py` | RDP connections via mstsc.exe |
| `actions\registry.py` | Windows registry read/write via winreg |
| `actions\terminal.py` | PowerShell and CMD via ShellExecute |
| `client\server_api.py` | Sends heartbeats to the backend API |
| `client\database.py` | Direct PostgreSQL connection for activity logging |
| `config\settings.yaml` | Role, work schedule, server IP, activity intervals |
| `config\paths.yaml` | Application executable paths |
| `roles\user.yaml` | Office worker activity list with weights |
| `roles\admin.yaml` | System administrator activity list with weights |
| `roles\dev.yaml` | Developer activity list with weights |
| `utils\logger.py` | Logging configuration |
| `setup_autostart.ps1` | Creates Windows Scheduled Task for autostart |
| `requirements.txt` | Python package dependencies |
