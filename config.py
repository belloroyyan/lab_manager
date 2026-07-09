from pathlib import Path
import os, sys, ctypes, subprocess

def get_project_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    else:
        return Path(__file__).resolve().parent
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
#netsh advfirewall firewall add rule name="LabToolListener" dir=in action=allow protocol=TCP localport=YOUR_PORT_NUMBER
def intiate_listener():
    res = subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=listener.py", "dir=in", "action=allow", "protocol=UDP", "localport=8088"])
    

PROJECT_ROOT = get_project_root()
VENV_DIR = PROJECT_ROOT / "venvs"
CORE_DIR = PROJECT_ROOT / "core"
UTILS_DIR = PROJECT_ROOT / "utils"
LOG_DIR = PROJECT_ROOT / "logs"
GIT_DIR = PROJECT_ROOT / "git_repos"
README_DIR = PROJECT_ROOT / "help"
BACKUP_DIR = PROJECT_ROOT / "lab_manager_backups"
REPORT_DIR = PROJECT_ROOT / "reports"
SETTINGS = PROJECT_ROOT / "settings.json"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"
SYSTEM_DRIVE = os.environ.get("SystemDrive", "C:") + "/"

