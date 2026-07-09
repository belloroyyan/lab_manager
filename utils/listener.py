import socket
from tkinter import Tk, messagebox
import subprocess
import platform
import shutil
import os
import json
import psutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from core.network import NetworkHandler
from config import REPORT_DIR, LOG_DIR
from utils.logger import log_manager
from utils.shell import kill_port

report_dir = REPORT_DIR / "inventory.tmp"
logger = log_manager.get_logger("Listener")
n = NetworkHandler()

def get_agent_data():
    current_user = os.path.expanduser("~")
    storage_info = []
    for part in psutil.disk_partitions(all=False):
        if os_name := platform.system() == "Windows" and "cdrom" in part.opts:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            storage_info.append(
                {
                    "device": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "used_percent": usage.percent,
                }
            )
        except PermissionError:
            continue
    payload = {
        "agent_id": socket.gethostname(),
        "current_user": current_user.split("\\")[-1],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": platform.processor(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "current_usage_percent": psutil.cpu_percent(interval=1),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "ram_used_percent": psutil.virtual_memory().percent,
        "storage": storage_info,
        "platform": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "uptime_seconds": round(time.time() - psutil.boot_time(), 2),
        "hostname": socket.gethostname(),
        "ip_on_lan": n.get_my_ip(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "mac_address": ":".join([f"{(uuid.getnode() >> ele) & 0xff:02x}"for ele in range(0, 8 * 6, 8)][::-1]),
    }
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        payload['cpu_name'] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except Exception:
        payload['cpu_name'] = platform.processor()
    try:
        serial = subprocess.check_output("wmic bios get serialnumber", shell=True).decode().split('\n')[1].strip()
        model = subprocess.check_output("wmic baseboard get product", shell=True).decode().split('\n')[1].strip()
        payload['serial_number'] = serial
        payload['motherboard'] = model
    except Exception:
        payload['serial_number'] = "Unknown"
        payload['motherboard'] = "Unknown"
    try:
        gpu = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode().split('\n')[1].strip()
        payload['gpu'] = gpu
    except Exception:
        payload['gpu'] = "Integrated/Unknown"
    try:
        cmd = "powershell (Get-PhysicalDisk).MediaType"
        drive_type = subprocess.check_output(cmd, shell=True).decode().strip()
        payload['drive_type'] = drive_type
    except Exception:
        payload['drive_type'] = "Unknown"
    return json.dumps(payload, indent=2)

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
        data, addr = s.recvfrom(2048)
        msg = data.decode('utf-8')
        if msg == 'SHUTDOWN':
            print(f"    [+] Received remote shutdown signal!")
            subprocess.run(['shutdown', '/s', '/t', '30'])
            continue
        elif msg == 'LOGOUT':
            print(f"    [+] Received remote logout signal!")
            subprocess.run(['shutdown', '/l'])
            continue
        elif msg == 'RESTART':
            print(f"    [+] Received remote restart signal!")
            subprocess.run(['shutdown', '/r'])
            continue
        elif msg == 'KILL':
            print(f"    [-] Shutting down port...")
            kill_port(8088)
            continue
        elif msg == 'INFO':
            print("    [+] Gathering info metrics...")
            metrics = get_agent_data()
            s.sendto(metrics.encode('utf-8'), (addr[0], port))
            print(f"    [+] Sent info metrics to {addr[0]}")
            continue
        elif "agent_id" in msg or "cores_physical" in msg or "uptime_seconds" in msg:
            with open(report_dir, "a", encoding="utf-8") as payload_file:
                payload_file.write(f"{msg[1:-2]}\n")
                payload_file.write(f"-" * 40)            
                print(f"    [+] Captured telemetry from {addr[0]}")
            if LOG_DIR.exists():
                logger.info("Successfully wrote metrics to payload file.")
            print("    [+] Successfully wrote metrics to payload file.")
            continue
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showinfo("LAB MANAGER MESSAGE", f"From: {addr}\n\nMessage: {msg}", parent=root)
        root.destroy()
#start_listener(8088)