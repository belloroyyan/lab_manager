import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import socket
from tkinter import Tk, messagebox
import subprocess
import platform
import ctypes
import os
import json
import psutil
import time
import uuid
import hashlib
import logging
import tempfile
from colorama import Fore, Style
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from core.network import NetworkHandler
from config import REPORT_DIR
from utils.identity import decrypt_message, encrypt_message, load_identity
from utils.shell import hide_file, kill_port, unhide_file
from config import IDENTITY_FILE, IDENTITY_DIR

hide_file(IDENTITY_FILE)
report_dir = REPORT_DIR / "inventory.tmp"
n = NetworkHandler()
ENABLEREMOTECOMMANDS = False
REMOTE_COMMANDS_EXPIRE_AT = 0
TASK_NAME = "LabManagerListener"

def setup_listener_logger():
    identity = load_identity()
    log_path = identity.get("log_path")
    logger = logging.getLogger("Listener")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_path:
        try:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create log file ({e}). Continuing with console only.")
    return logger

def handle_enable_remote(addr, sock, port, minutes: int = 10):
    logger = setup_listener_logger()
    global ENABLEREMOTECOMMANDS, REMOTE_COMMANDS_EXPIRE_AT
    ENABLEREMOTECOMMANDS = True
    REMOTE_COMMANDS_EXPIRE_AT = time.time() + (minutes * 60)
    logger.warning(f"Remote commands enabled for {minutes} min by {addr[0]}")
    reply = encrypt_message(f"REMOTE_ENABLED {minutes}")
    if reply:
        sock.sendto(reply.encode(), (addr[0], port))

def handle_disable_remote(addr, sock, port):
    logger = setup_listener_logger()
    global ENABLEREMOTECOMMANDS, REMOTE_COMMANDS_EXPIRE_AT
    ENABLEREMOTECOMMANDS = False
    REMOTE_COMMANDS_EXPIRE_AT = 0
    logger.warning(f"Remote commands disabled by {addr[0]}")

def handle_info(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"Authenticated INFO request from {addr[0]}")
    metrics = get_agent_data()
    encrypted_reply = encrypt_message(metrics)
    if encrypted_reply:
        sock.sendto(encrypted_reply.encode(), (addr[0], port))
        logger.info(f"Encrypted telemetry sent to {addr[0]}")
    else:
        logger.info("Failed to encrypt reply (missing key?)")

def handle_ping(addr, sock, port):
    reply = encrypt_message("PONG")
    if reply:
        sock.sendto(reply.encode(), (addr[0], port))

def handle_shutdown(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"SHUTDOWN command received from {addr[0]}")
    subprocess.run(["shutdown", "/s", "/t", "30"])

def handle_abort(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"SHUTDOWN command received from {addr[0]}")
    subprocess.run(["shutdown", "/a"])

def handle_restart(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"RESTART command received from {addr[0]}")
    subprocess.run(["shutdown", "/r", "/t", "30"])

def handle_logout(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"LOGOUT command received from {addr[0]}")
    subprocess.run(["shutdown", "/l"])

def handle_kill(addr, sock, port):
    logger = setup_listener_logger()
    logger.info(f"KILL_PORT command received from {addr[0]}")
    print("Shutting down listener.")
    kill_port(8088)

SAFE_COMMANDS = {
    "INFO": handle_info,
    "PING": handle_ping,
}

DANGEROUS_COMMANDS = {
    "SHUTDOWN": handle_shutdown,
    "RESTART": handle_restart,
    "LOGOUT": handle_logout,
    "KILL": handle_kill,
    "ABORT": handle_abort
}

def process_command(command: str, addr, sock, port):
    logger = setup_listener_logger()
    global ENABLEREMOTECOMMANDS
    if ENABLEREMOTECOMMANDS and time.time() > REMOTE_COMMANDS_EXPIRE_AT:
        ENABLEREMOTECOMMANDS = False
        logger.warning("Remote commands auto-disabled (timeout)")

    parts = command.strip().upper().split()
    cmd = parts[0] if parts else ""
    if cmd == "INFO":
        handle_info(addr, sock, port)
        return
    if cmd == "PING":
        handle_ping(addr, sock, port)
        return
    if cmd == "ENABLE_REMOTE":
        minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
        minutes = max(1, min(minutes, 60))
        handle_enable_remote(addr, sock, port, minutes)
        return
    if cmd == "DISABLE_REMOTE":
        handle_disable_remote(addr, sock, port)
        return
    if cmd in ("SHUTDOWN", "RESTART", "LOGOUT", "ABORT"):
        if ENABLEREMOTECOMMANDS:
            if cmd == "SHUTDOWN":
                handle_shutdown(addr, sock, port)
            elif cmd == "RESTART":
                handle_restart(addr, sock, port)
            elif cmd == "ABORT":
                handle_abort(addr, sock, port)
            elif cmd == "LOGOUT":
                handle_logout(addr, sock, port)
        else:
            logger.warning(f"Rejected '{cmd}' - remote commands are disabled")
        return

    logger.warning(f"Unknown command: {command}")

def hide_console():
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

def is_first_run():
    if not IDENTITY_FILE.exists():
        return True
    try:
        with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return "password_hash" not in data or not data["password_hash"]
    except Exception:
        return True

def hash_password(password):
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )
    return salt.hex() + "$" + pwd_hash.hex()

def task_exists(task_name = TASK_NAME):
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", task_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def create_startup_task():
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = str(Path(__file__).resolve())
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Lab Manager Listener - Auto start + restart on failure</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>999</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
    </Exec>
  </Actions>
</Task>
'''
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-16") as f:
            f.write(xml_content)
            temp_xml = f.name
        result = subprocess.run(
            ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", temp_xml, "/F"],
            capture_output=True,
            text=True
        )
        Path(temp_xml).unlink(missing_ok=True)
        if result.returncode == 0:
            print("[+] Scheduled task created successfully (with restart on failure).")
            return True
        else:
            print(f"[!] Failed to create task:\n{result.stderr}")
            return False

    except Exception as e:
        print(f"[!] Error while creating task: {e}")
        return False

def verify_password(password: str, stored_hash: str):
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000
        )
        return new_hash.hex() == hash_hex
    except Exception:
        return False

def create_identity(password: str, school_name="UNIOSUN", lab_name="FOCIT Lab", log_path=None):
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    unhide_file(IDENTITY_FILE)
    identity = {
        "school_name": school_name,
        "lab_name": lab_name,
        "secret_key": "",
        "password_hash": hash_password(password),
        "log_path" : log_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_modified": datetime.now(timezone.utc).isoformat()
    }
    with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(identity, f, indent=4)
    try:
        hide_file(IDENTITY_FILE)
    except Exception:
        pass
    return identity

def import_secret_key(path: Path):
    try:
        key = path.read_text(encoding="utf-8").strip()
        Fernet(key.encode())
        unhide_file(IDENTITY_FILE)
        with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
            identity = json.load(f)
        identity["secret_key"] = key
        identity["last_modified"] = datetime.now(timezone.utc).isoformat()
        with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=4)
        return True
    except Exception as e:
        logger = setup_listener_logger()
        logger.exception(f"Failed to import key: {e}")
        return False
    finally:
        try:
            hide_file(IDENTITY_FILE)
        except Exception:
            pass
    
def run_first_time_setup():
    print("=" * 50)
    print("   LAB MANAGER LISTENER – FIRST TIME SETUP")
    print("=" * 50)
    print()

    if not is_first_run():
        print("Discovered existing identity file.")
        print("To re-run setup, enter the old password.")
        user_password = input(f"{Fore.GREEN}\nEnter existing password to continue: {Style.RESET_ALL}").strip()
        identity = load_identity()
        if not verify_password(user_password, identity.get("password_hash", "")):
            print("Incorrect password. Exiting setup.\n")
            return
        print("Password correct. Continuing with setup...\n")
    while True:
        password = input("Create Lab Setup Password: ").strip()
        confirm  = input("Confirm Password: ").strip()
        if password and password == confirm:
            break
        print("Passwords do not match or are empty. Try again.\n")

    school = input("School name [UNIOSUN]: ").strip() or "UNIOSUN"
    lab    = input("Lab name [FOCIT Lab]: ").strip() or "FOCIT Lab"
    print("\n--- Logging Setup ---")
    print("Leave blank if you want logs only in the console.")
    log_input = input("Log file path (e.g. C:\\LabManager\\listener.log): ").strip()
    log_path = log_input if log_input else None
    create_identity(password, school, lab, log_path)
    print("\n[+] Identity file created successfully.")
    choice = input("\nImport secret.key now? (y/n): ").strip().lower()
    if choice == "y":
        key_path = input("Path to secret.key (or USB root): ").strip()
        if key_path:
            p = Path(key_path)
            if p.is_dir():
                p = p / "secret.key"
            if p.exists():
                if import_secret_key(p):
                    print("[+] Secret key imported successfully.")
                else:
                    print("[!] Failed to import key. You can do it later with --setup")
            else:
                print("[!] File not found.")
    if is_admin():
        if not firewall_rule_exists("LabManager Listener"):
            print("\n[+] Creating firewall rule for UDP port 8088...")
            if initiate_listener(8088):
                print("[+] Firewall rule created successfully.")
            else:
                print("[!] Failed to create firewall rule. You can do it later with --setup")
    else:
        print("\n[!] You are not running as Administrator.")
        print("[!] Firewall rule for UDP port 8088 will not be created.")
        print("[!] Please run Lab Manager as Administrator once to create the rule.")
    print("\n--- Startup Task ---")
    if task_exists():
        print("[+] Startup task already exists.")
    else:
        print("[!] Startup task not found.")
        choice = input("Would you like to create it now so the listener starts with Windows? (y/n): ").strip().lower()
        if choice == "y":
            success = create_startup_task()
            if not success:
                print("[-] Could not create the task. You may need to run as Administrator.")
        else:
            print("[-] Skipped creating startup task. You can do it later with --setup")
    print("\nSetup complete. Listener will now start.")
    print("Next time it will run silently in the background.\n")

def get_agent_data():
    current_user = os.path.expanduser("~")
    storage_info = []
    for part in psutil.disk_partitions(all=False):
        if (os_name := platform.system()) == "Windows" and "cdrom" in part.opts:
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
            logger = setup_listener_logger()
            logger.warning(f"Permission denied for disk partition: {part.mountpoint}")
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
    logger = setup_listener_logger()
    logger.info(f"Listener started on UDP port {port} at {datetime.now()}.")
    while True:
        data, addr = s.recvfrom(2048)
        raw_msg = data.decode('utf-8', errors='ignore')
        if not raw_msg:
            continue
        msg = decrypt_message(raw_msg)
        if msg.startswith("LAB|"):
            process_command(msg[4:], addr, s, port)
            continue
        if "agent_id" in msg or "cores_physical" in msg or "uptime_seconds" in msg:
            with open(report_dir, "a", encoding="utf-8") as payload_file:
                payload_file.write(f"{msg[1:-2]}\n")
                payload_file.write(f"-" * 40)            
                logger.info(f"Captured telemetry from {addr[0]}")
            logger.info("Successfully wrote metrics to payload file.")
            continue
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        logger.info(f"Received message from {addr[0]}: {msg}")
        messagebox.showinfo("LAB MANAGER MESSAGE", f"From: {addr}\n\nMessage: {msg}", parent=root)
        root.destroy()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def firewall_rule_exists(rule_name: str):
    result = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
        capture_output=True,
        text=True
    )
    return rule_name.lower() in result.stdout.lower() and result.returncode == 0

def initiate_listener(port: int = 8088):
    rule_name = "LabManager Listener"
    if firewall_rule_exists(rule_name):
        logger = setup_listener_logger()
        logger.info(f"Firewall rule '{rule_name}' already exists.")
        print(f"[+] Firewall rule already exists for UDP port {port}")
        return True
    if not is_admin():
        logger.warning("Firewall rule missing and no admin privileges.")
        print("[!] Firewall rule does not exist.")
        print("[!] Please run Lab Manager as Administrator once to create the rule.")
        return False
    result = subprocess.run(
        [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}",
            "dir=in",
            "action=allow",
            "protocol=UDP",
            f"localport={port}",
            "enable=yes",
            "profile=any"
        ],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        logger.info(f"Firewall rule '{rule_name}' created successfully.")
        return True
    else:
        logger.error(f"Failed to create firewall rule: {result.stderr}")
        return False

def main():
    force_setup = "--setup" in sys.argv or "-s" in sys.argv
    if is_first_run() or force_setup:
        run_first_time_setup()
    else:
        hide_console()
    start_listener(port=8088)
    
if __name__ == "__main__":
    main()