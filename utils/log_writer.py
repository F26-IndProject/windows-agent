"""
utils/log_writer.py — Remote log receiver
==========================================
Launched by agent.exe via spawn.exe (parent = explorer.exe).
Listens on localhost:19999 for log records sent by agent.exe
and writes them to logs/agent.log.

Compile separately:
  pyinstaller --onefile --name log_writer utils/log_writer.py
Copy log_writer.exe to WinAgent root alongside agent.exe and spawn.exe.
"""

import logging
import logging.handlers
import pickle
import socketserver
import struct
import sys
from pathlib import Path

HOST     = "127.0.0.1"
PORT     = 19999
LOG_FILE = "logs/agent.log"


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Receives pickled LogRecord objects and writes them to the local logger."""

    def handle(self):
        while True:
            try:
                # First 4 bytes = length of the pickled record
                header = self.connection.recv(4)
                if len(header) < 4:
                    break
                slen = struct.unpack(">L", header)[0]
                data = b""
                while len(data) < slen:
                    chunk = self.connection.recv(slen - len(data))
                    if not chunk:
                        break
                    data += chunk
                obj    = pickle.loads(data)
                record = logging.makeLogRecord(obj)
                logging.getLogger(record.name).handle(record)
            except Exception:
                break


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    # Prevent multiple instances
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "LISA_LogWriter_Mutex")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)

    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(threadName)s]: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )

    server = LogRecordSocketReceiver((HOST, PORT), LogRecordStreamHandler)
    server.serve_forever()