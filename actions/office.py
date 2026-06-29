"""
actions/office.py — MS Office automation via COM
===================================================
Outlook operations run in background — no visible window.
Word and Excel open visibly via COM (parent = svchost.exe).

Received attachments:
- Word/ODT  -> ShellExecuteW, closed via taskkill
- PDF       -> spawn.exe (parent = explorer.exe), closed via taskkill
- Images    -> ShellExecuteW (parent = svchost.exe), closed via taskkill

Sent attachments:
- Agent picks files in sorted queue order from WinAgent\attachments\ folder
- 80% of eligible templates include an attachment
- Supports: .docx, .doc, .pdf, .jpg, .jpeg, .png

REQUIRES: pip install pywin32
"""

import ctypes
import ctypes.wintypes
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime

from actions.templates.email import REPLY_TEMPLATES, SEND_TEMPLATES
from actions.templates.word_excel import get_word_content, get_excel_template


if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEND_ATTACHMENTS_DIR = os.path.join(_BASE_DIR, "attachments")
RECV_ATTACHMENTS_DIR = os.path.join(
    os.path.expandvars(r"%USERPROFILE%"), "Downloads", "LISA_Attachments"
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
WORD_EXTENSIONS  = {".docx", ".doc", ".odt", ".odf"}
PDF_EXTENSIONS   = {".pdf"}
ALL_EXTENSIONS   = IMAGE_EXTENSIONS | WORD_EXTENSIONS | PDF_EXTENSIONS


SEE_MASK_NOCLOSEPROCESS = 0x00000040

class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize",        ctypes.wintypes.DWORD),
        ("fMask",         ctypes.wintypes.ULONG),
        ("hwnd",          ctypes.wintypes.HWND),
        ("lpVerb",        ctypes.c_wchar_p),
        ("lpFile",        ctypes.c_wchar_p),
        ("lpParameters",  ctypes.c_wchar_p),
        ("lpDirectory",   ctypes.c_wchar_p),
        ("nShow",         ctypes.c_int),
        ("hInstApp",      ctypes.wintypes.HINSTANCE),
        ("lpIDList",      ctypes.c_void_p),
        ("lpClass",       ctypes.c_wchar_p),
        ("hkeyClass",     ctypes.wintypes.HKEY),
        ("dwHotKey",      ctypes.wintypes.DWORD),
        ("hMonitor",      ctypes.wintypes.HANDLE),
        ("hProcess",      ctypes.wintypes.HANDLE),
    ]


def _get_outlook():
    import win32com.client
    try:
        outlook = win32com.client.GetActiveObject("Outlook.Application")
        logging.info("Outlook: reusing existing COM instance")
    except Exception:
        outlook = win32com.client.Dispatch("Outlook.Application")
        logging.info("Outlook: launched new COM instance")

    try:
        explorer = outlook.Explorers
        if explorer.Count == 0:
            ns = outlook.GetNamespace("MAPI")
            inbox = ns.GetDefaultFolder(6)
            new_explorer = outlook.Explorers.Add(inbox, 0)
            new_explorer.Display()
            time.sleep(5)
        # Window already open — no wait, IMAP already syncing
    except Exception as e:
        logging.warning(f"Outlook explorer setup failed: {e} — continuing anyway")

    return outlook


_attachment_queue_index = 0

def _pick_next_attachment():
    global _attachment_queue_index

    if not os.path.isdir(SEND_ATTACHMENTS_DIR):
        logging.warning(f"Attachments folder not found: {SEND_ATTACHMENTS_DIR}")
        return None

    supported = WORD_EXTENSIONS | PDF_EXTENSIONS | IMAGE_EXTENSIONS
    files = sorted([
        f for f in os.listdir(SEND_ATTACHMENTS_DIR)
        if os.path.splitext(f)[1].lower() in supported
    ])

    if not files:
        logging.warning("No attachment files found in attachments folder")
        return None

    chosen = files[_attachment_queue_index % len(files)]
    _attachment_queue_index += 1
    return os.path.join(SEND_ATTACHMENTS_DIR, chosen)


def _open_word_attachment(file_path: str):
    """
    Open Word/ODT via ShellExecuteW.
    Parent = explorer.exe. Closed via taskkill after reading delay.
    """
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "open", file_path, None, None, 3)
        logging.info(f"Word attachment opened: {os.path.basename(file_path)}")

        read_time = random.randint(25, 35)
        logging.info(f"Reading Word attachment for {read_time}s")
        time.sleep(read_time)

        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".docx", ".doc"]:
            subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)
        elif ext in [".odt", ".odf"]:
            subprocess.run(["taskkill", "/F", "/IM", "soffice.exe"], capture_output=True)
        logging.info(f"Word attachment closed: {os.path.basename(file_path)}")

    except Exception as e:
        logging.error(f"Word attachment failed: {e}")
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)


def _open_pdf_or_image_attachment(file_path: str):
    """
    PDF   -> spawn.exe (parent = explorer.exe) verified working.
    Image -> ShellExecuteW (parent = svchost.exe) verified working.
    Closes via taskkill by name after reading delay.
    """
    from actions.apps import open_pdf_via_spawn
    ext = os.path.splitext(file_path)[1].lower()

    if ext in PDF_EXTENSIONS:
        open_pdf_via_spawn(file_path)
    else:
        # Images — ShellExecuteW gives svchost.exe as parent
        ctypes.windll.shell32.ShellExecuteW(None, "open", file_path, None, None, 1)

    logging.info(f"Attachment opened: {os.path.basename(file_path)}")

    read_time = random.randint(25, 35)
    logging.info(f"Reading attachment for {read_time}s")
    time.sleep(read_time)

    if ext in PDF_EXTENSIONS:
        subprocess.run(["taskkill", "/F", "/IM", "Acrobat.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "AcroRd32.exe"], capture_output=True)
    elif ext in IMAGE_EXTENSIONS:
        subprocess.run(["taskkill", "/F", "/IM", "Microsoft.Photos.exe"], capture_output=True)

    logging.info(f"Attachment closed: {os.path.basename(file_path)}")


def _open_received_attachment_and_close(save_path: str):
    """Route to correct open/close method based on file type."""
    ext = os.path.splitext(save_path)[1].lower()
    if ext in WORD_EXTENSIONS:
        _open_word_attachment(save_path)
    elif ext in PDF_EXTENSIONS | IMAGE_EXTENSIONS:
        _open_pdf_or_image_attachment(save_path)
    else:
        logging.warning(f"Unsupported attachment type: {ext} — skipping open")


def _handle_received_attachments(msg):
    """Download all attachments from a received email, open and close the first."""
    try:
        os.makedirs(RECV_ATTACHMENTS_DIR, exist_ok=True)
        for i in range(1, msg.Attachments.Count + 1):
            attachment = msg.Attachments.Item(i)
            save_path  = os.path.join(RECV_ATTACHMENTS_DIR, attachment.FileName)
            attachment.SaveAsFile(save_path)
            logging.info(f"Attachment downloaded: {attachment.FileName}")
            if i == 1:
                _open_received_attachment_and_close(save_path)
    except Exception as e:
        logging.error(f"Attachment handling failed: {e}")


def _reply_to_email(msg):
    try:
        reply      = msg.Reply()
        reply.Body = (
            random.choice(REPLY_TEMPLATES)
            + f"\n\nBest regards\n"
            + f"Sent at {datetime.now().strftime('%H:%M on %d %B %Y')}"
        )
        reply.Send()
        logging.info(f"Reply sent to: {msg.SenderEmailAddress}")
    except Exception as e:
        logging.error(f"Reply failed: {e}")


def read_outlook_inbox():
    try:
        import pythoncom
        pythoncom.CoInitialize()

        outlook   = _get_outlook()
        namespace = outlook.GetNamespace("MAPI")
        inbox     = namespace.GetDefaultFolder(6)

        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        # Get own email so we never reply to ourselves or bounce messages
        own_email = ""
        try:
            own_email = namespace.Accounts.Item(1).SmtpAddress.lower()
            logging.info(f"Own email: {own_email} — will skip self-emails and bounces")
        except Exception as e:
            logging.warning(f"Could not resolve own email: {e}")

        unread_count = 0
        for msg in messages:
            if unread_count >= 3:
                break
            try:
                if not msg.UnRead:
                    continue
                sender_addr = (msg.SenderEmailAddress or "").lower()
                # Skip own emails (self-loop) and system/bounce senders
                if own_email and sender_addr == own_email:
                    logging.info(f"Skipping self-email: {msg.Subject}")
                    msg.UnRead = False
                    msg.Save()
                    continue
                if any(x in sender_addr for x in ("mailer-daemon", "postmaster", "noreply", "no-reply")):
                    logging.info(f"Skipping system email from {sender_addr}")
                    msg.UnRead = False
                    msg.Save()
                    continue
                subject = msg.Subject
                sender  = msg.SenderName
                logging.info(f"Reading unread email from {sender}: {subject}")
                msg.UnRead = False
                msg.Save()
                time.sleep(random.randint(3, 6))
                if msg.Attachments.Count > 0:
                    _handle_received_attachments(msg)
                _reply_to_email(msg)
                unread_count += 1
            except Exception as e:
                logging.error(f"Error processing email: {e}")
                continue

        if unread_count == 0:
            logging.info("Outlook: no unread emails found")
        else:
            logging.info(f"Outlook: processed {unread_count} unread emails")

        try:
            outlook.Quit()
        except Exception:
            pass
        subprocess.run(["taskkill", "/F", "/IM", "OUTLOOK.EXE"], capture_output=True)
        logging.info("Outlook closed after read")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed.")
    except Exception as e:
        logging.error(f"Outlook read inbox failed: {e}")


def send_outlook_email(
    to: str = None,
    subject: str = None,
    body: str = None,
    recipients: list = None
):
    try:
        import pythoncom
        pythoncom.CoInitialize()

        outlook  = _get_outlook()
        template = random.choice(SEND_TEMPLATES)
        subject  = subject or template["subject"]
        body     = body    or template["body"]

        # If a recipients list was passed, filter own email and pick one.
        # We do this here — inside COM context — so own email is always available.
        if recipients:
            try:
                namespace  = outlook.GetNamespace("MAPI")
                own_email  = namespace.Accounts.Item(1).SmtpAddress.lower()
                filtered   = [r for r in recipients if r.lower() != own_email]
                logging.info(f"Own email: {own_email} — filtered to {len(filtered)}/{len(recipients)} recipients")
                to = random.choice(filtered if filtered else recipients)
            except Exception as e:
                logging.warning(f"Could not resolve own email: {e} — picking from full list")
                to = random.choice(recipients)
        elif not to:
            to = "admin@lisa.local"

        mail         = outlook.CreateItem(0)
        mail.To      = to
        mail.Subject = subject
        mail.Body    = body + f"\n\nSent at {datetime.now().strftime('%H:%M on %d %B %Y')}"

        if template.get("attach") and random.random() < 0.8:
            attachment_path = _pick_next_attachment()
            if attachment_path:
                mail.Attachments.Add(attachment_path)
                logging.info(f"Attachment added: {os.path.basename(attachment_path)}")

        mail.Send()
        logging.info(f"Outlook email sent to: {to} — subject: {subject}")

        try:
            outlook.Quit()
        except Exception:
            pass
        subprocess.run(["taskkill", "/F", "/IM", "OUTLOOK.EXE"], capture_output=True)
        logging.info("Outlook closed after send")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed.")
    except Exception as e:
        logging.error(f"Outlook send failed: {e}")


def create_word_document(filename: str = "document.docx", content: str = ""):
    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        word         = win32com.client.Dispatch("Word.Application")
        word.Visible = True
        time.sleep(2)

        doc = word.Documents.Add()
        time.sleep(1)
        word.Selection.TypeText(content if content and content.strip() else get_word_content())
        time.sleep(1)

        base, ext = os.path.splitext(filename)
        unique_filename = f"{base}_{datetime.now().strftime('%m%d_%H%M%S')}{ext}"
        save_path = os.path.join(
            os.path.expandvars(r"%USERPROFILE%\Documents"), unique_filename
        )
        doc.SaveAs2(save_path)
        logging.info(f"Word document saved: {save_path}")

        time.sleep(random.randint(10, 30))
        try:
            doc.Close(SaveChanges=False)
        except Exception:
            pass
        try:
            word.Quit()
        except Exception:
            pass
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)
        logging.info("Word closed")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed.")
    except Exception as e:
        logging.error(f"Word COM failed: {e}")
        subprocess.run(["taskkill", "/F", "/IM", "WINWORD.EXE"], capture_output=True)


def create_excel_spreadsheet(filename: str = "data.xlsx"):
    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()

        excel         = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True
        time.sleep(2)

        wb = excel.Workbooks.Add()
        ws = wb.ActiveSheet

        template = get_excel_template()
        ws.Name  = template["sheet"]

        for col, header in enumerate(template["headers"], start=1):
            ws.Cells(1, col).Value = header

        for row_idx, row_data in enumerate(template["rows"], start=2):
            for col_idx, cell_val in enumerate(row_data, start=1):
                ws.Cells(row_idx, col_idx).Value = cell_val

        sheet_name      = template["sheet"].lower().replace(" ", "_")
        unique_filename = f"{sheet_name}_{datetime.now().strftime('%m%d_%H%M%S')}.xlsx"
        save_path = os.path.join(
            os.path.expandvars(r"%USERPROFILE%\Documents"), unique_filename
        )
        wb.SaveAs(save_path)
        logging.info(f"Excel spreadsheet saved: {save_path}")

        time.sleep(random.randint(8, 20))
        try:
            wb.Close(SaveChanges=False)
        except Exception:
            pass
        try:
            excel.Quit()
        except Exception:
            pass
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], capture_output=True)
        logging.info("Excel closed")

        pythoncom.CoUninitialize()

    except ImportError:
        logging.error("pywin32 not installed.")
    except Exception as e:
        logging.error(f"Excel COM failed: {e}")
        subprocess.run(["taskkill", "/F", "/IM", "EXCEL.EXE"], capture_output=True)