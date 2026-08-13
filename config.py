from pathlib import Path
import os, sys, ctypes

_STANDALONE = True

def get_project_root():
    if getattr(sys, 'frozen', False):
        global _STANDALONE 
        _STANDALONE = True
        return Path(sys.executable).resolve().parent
    else:
        _STANDALONE = False
        return Path(__file__).resolve().parent
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False 

PROJECT_ROOT = get_project_root()
APP_VERSION = "2.1.4"
GITHUB_REPO = "belloroyyan/lab_manager"
DESKTOP_DIR = Path(os.path.expanduser("~")) / "Desktop" / "Lab Manager"
APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Lab Manager"
PROGRAMDATA = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
IDENTITY_DIR = PROGRAMDATA / "LabManager"
IDENTITY_FILE = IDENTITY_DIR / "lab_secret.json"
TEMP_DIR = PROJECT_ROOT / "%Temp"
VENV_DIR = DESKTOP_DIR / "venvs"
CORE_DIR = PROJECT_ROOT / "core"
UTILS_DIR = PROJECT_ROOT / "utils"
LOG_DIR = PROJECT_ROOT / "logs"
GIT_DIR = DESKTOP_DIR / "git_repos"
BACKUP_DIR = DESKTOP_DIR / "lab_manager_backups"
REPORT_DIR = DESKTOP_DIR / "reports"
ENV_STATUS_FILE = REPORT_DIR / "last_env_status.json"
SETTINGS = PROJECT_ROOT / "settings.json"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RED = "\033[91m"
RESET = "\033[0m"
SYSTEM_DRIVE = os.environ.get("SystemDrive", "C:") + "/"

