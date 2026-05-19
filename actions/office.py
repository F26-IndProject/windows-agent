"""
actions/office.py — MS Office automation via COM
===================================================
COM (Component Object Model) is Microsoft's technology that lets one
program control another. When we use COM to open Word, Windows starts
Word through its own DCOM launcher service (svchost.exe -k DcomLaunch).
The resulting WINWORD.EXE has svchost.exe as parent — NOT our agent.

This is the correct, professional way to automate Office. It:
1. Satisfies the parent-process requirement
2. Lets us actually type content, read emails, click buttons
3. Is how tools like AutoIt, VBA macros, and test frameworks work

REQUIRES: pip install pywin32
After installing, run: python -m win32com.client.makepy
"""

import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path


def create_word_document(filename: str = "document.docx", content: str = ""):
    """
    Open Word via COM, create a new document, type content, save, and close.
    The WINWORD.EXE process will be a child of svchost, not the agent.
    """
    try:
        import win32com.client
        import pythoncom

        # CoInitialize is needed when running COM from a non-main thread
        pythoncom.CoInitialize()

        # This line is what makes the magic happen:
        # Instead of subprocess.Popen("WINWORD.EXE"), which makes agent the parent,
        # we ask the COM system to give us a Word object.
        # COM's DcomLaunch service handles the actual process creation.
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = True   # True = user can see Word opening (realistic)

        # Give Word a moment to fully open
        time.sleep(2)

        # Create a new blank document
        doc = word.Documents.Add()
        time.sleep(1)

        # Type some content
        word.Selection.TypeText(content or _random_work_content())
        time.sleep(1)

        # Save the document to the user's Documents folder
        save_path = os.path.join(
            os.path.expandvars(r"%USERPROFILE%\Documents"),
            filename
        )
        doc.SaveAs2(save_path)
        logging.info(f"Word document saved: {save_path}")

        # Wait a realistic amount of time before closing
        time.sleep(random.randint(10, 30))

        doc.Close(SaveChanges=False)   # Already saved above
        word.Quit()
        logging.info("Word closed via COM")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error(
            "pywin32 not installed. Run: pip install pywin32"
        )
    except Exception as e:
        logging.error(f"Word COM automation failed: {e}")


def create_excel_spreadsheet(filename: str = "data.xlsx"):
    """
    Open Excel via COM, fill a spreadsheet with sample data, save, and close.
    """
    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True
        time.sleep(2)

        wb = excel.Workbooks.Add()
        ws = wb.ActiveSheet

        # Write headers
        ws.Cells(1, 1).Value = "Date"
        ws.Cells(1, 2).Value = "Item"
        ws.Cells(1, 3).Value = "Value"

        # Write some sample data rows
        samples = [
            ("Project Alpha", 142),
            ("Project Beta", 87),
            ("Maintenance", 34),
            ("Review", 56),
        ]
        for i, (item, value) in enumerate(samples, start=2):
            ws.Cells(i, 1).Value = datetime.now().strftime("%Y-%m-%d")
            ws.Cells(i, 2).Value = item
            ws.Cells(i, 3).Value = value

        save_path = os.path.join(
            os.path.expandvars(r"%USERPROFILE%\Documents"),
            filename
        )
        wb.SaveAs(save_path)
        logging.info(f"Excel spreadsheet saved: {save_path}")

        time.sleep(random.randint(8, 20))

        wb.Close(SaveChanges=False)
        excel.Quit()
        logging.info("Excel closed via COM")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed. Run: pip install pywin32")
    except Exception as e:
        logging.error(f"Excel COM automation failed: {e}")


def send_outlook_email(
    to: str = "colleague@company.local",
    subject: str = "Update",
    body: str = "Please see the latest update."
):
    """
    Compose and send an email via Outlook COM.
    Outlook must be installed and a mail account configured.
    """
    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        # GetActiveObject tries to reuse an already-open Outlook instance
        # If Outlook isn't open, Dispatch opens it
        try:
            outlook = win32com.client.GetActiveObject("Outlook.Application")
        except Exception:
            outlook = win32com.client.Dispatch("Outlook.Application")

        time.sleep(2)

        # Create a new email item
        mail = outlook.CreateItem(0)   # 0 = olMailItem
        mail.To = to
        mail.Subject = subject
        mail.Body = f"{body}\n\nSent from LISA simulation agent at {datetime.now().strftime('%H:%M')}"

        # Send the email
        mail.Send()
        logging.info(f"Outlook email sent to: {to}, subject: {subject}")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed. Run: pip install pywin32")
    except Exception as e:
        logging.error(f"Outlook COM send failed: {e}")


def read_outlook_inbox():
    """
    Open Outlook, access the inbox, and read the first few emails.
    Simulates a user checking their mail.
    """
    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        try:
            outlook = win32com.client.GetActiveObject("Outlook.Application")
        except Exception:
            outlook = win32com.client.Dispatch("Outlook.Application")

        time.sleep(2)

        # Navigate to inbox
        namespace = outlook.GetNamespace("MAPI")
        inbox = namespace.GetDefaultFolder(6)   # 6 = olFolderInbox

        # Read the most recent 3 emails
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)   # Sort newest first

        count = 0
        for msg in messages:
            if count >= 3:
                break
            try:
                subject = msg.Subject
                sender  = msg.SenderName
                logging.info(f"Reading email from {sender}: {subject}")
                # Simulate reading time
                time.sleep(random.randint(3, 8))
                count += 1
            except Exception:
                continue

        logging.info("Finished reading Outlook inbox")
        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed. Run: pip install pywin32")
    except Exception as e:
        logging.error(f"Outlook read inbox failed: {e}")


def _random_work_content() -> str:
    """Return a random work-like paragraph to type into documents."""
    contents = [
        "Weekly status update:\n\nProject Alpha is progressing on schedule. "
        "All milestones for Q2 have been completed. The team will present "
        "results in the Friday meeting.\n\nAction items: review the deployment "
        "checklist, update the risk register, confirm stakeholder sign-off.",

        "Meeting notes — Infrastructure review:\n\nAttendees: development team, "
        "DevOps, management.\n\nDecisions made:\n"
        "1. Upgrade server OS to Ubuntu 22.04 LTS by end of month.\n"
        "2. Enable automatic backups on all production databases.\n"
        "3. Schedule penetration test for Q3.",

        "Incident report — System outage:\n\nDate: today\n"
        "Duration: approximately 45 minutes\n"
        "Root cause: network switch firmware update caused port reset.\n"
        "Resolution: switch rebooted, services restored.\n"
        "Prevention: schedule maintenance windows outside business hours.",
    ]
    return random.choice(contents)
