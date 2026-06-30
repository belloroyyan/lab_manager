import socket
from tkinter import Tk, messagebox
import subprocess
import platform
import shutil
import os
import json
from datetime import datetime
from pathlib import Path
from core.network import NetworkHandler
from config import REPORT_DIR
from utils.logger import log_manager

report_dir = REPORT_DIR / "inventory.tmp"
log_dir = Path("log.txt")
logger = log_manager.get_logger("Listener")
n = NetworkHandler()

def gather_local_metrics():
    total, used, free = shutil.disk_usage("/")
    metrics = {
        "hostname": platform.node(),
        "os": platform.system(),
        "release": platform.release(),
        "current_user": os.getlogin(),
        "disk_total_gb": round(total / (1024**3), 2),
        "disk_free_gb": round(free / (1024**3), 2),
        "disk_use_percent": round((used / total) * 100, 1)
    }
    return json.dumps(metrics)

def start_listener(port=8088):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('', port))
    except OSError:
        print(f"Port {port} is already in use! Try a different one.")
        return
    print(f"Agent is listening for messages on port {port}...")
    while True:
        data, addr = s.recvfrom(1024)
        msg = data.decode('utf-8')
        if msg == 'SHUTDOWN':
            print(f"    [n] Received remote shutdown signal!")
            subprocess.run(['shutdown', '/s', '/t', '30'])
            continue
        elif msg == 'INFO':
            print("    [n] Gathering info metrics...")
            metrics = gather_local_metrics()
            s.sendto(metrics.encode('utf-8'), (addr[0], port))
            print(f"    [n] Sent info metrics to {addr[0]}")
            continue
        elif "hostname" in msg[:10]:
            with open(report_dir, "a", encoding="utf-8") as report_file:
                report_file.write(f"=== Node Source: {addr[0]} ===\n")
                report_file.write(f"{msg[1:-2]}\n")
                report_file.write(f"-" * 40 + "\n\n")            
                print(f"    [n] Captured telemetry from {addr[0]}")
            print("    [n] Successfully wrote metrics to log file.")
            continue
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showinfo("LAB MANAGER MESSAGE", f"From: {addr}\n\nMessage: {msg}", parent=root)
        root.destroy()
#start_listener(8088)