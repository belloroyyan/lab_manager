import json
from datetime import datetime, timezone
from pathlib import Path
from config import ENV_STATUS_FILE
from utils.logger import log_manager
from utils.settings import load_settings

logger = log_manager.get_logger("EnvStatus")
config = load_settings()

def save_env_status(data: dict) -> bool:
    try:
        ENV_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(ENV_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.exception(f"Failed to save environment status: {e}")
        print(f"Failed to save environment status: {e}")
        return False

def load_env_status() -> dict | None:
    if not ENV_STATUS_FILE.exists():
        return None
    try:
        with open(ENV_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception(f"Failed to load environment status: {e}")
        return None

def print_saved_env_status():
    data = load_env_status()
    if not data:
        print("No previous environment scan found.")
        return
    print("\n=== Last Environment Status ===")
    print(f"Scanned at     : {data.get('timestamp', 'Unknown')}")
    print(f"Python         : {data.get('python_version', 'N/A')}")
    print(f"Git            : {data.get('git_version', 'N/A')}")
    print(f"Running as Admin: {data.get('is_admin', False)}")
    print(f"Venvs found    : {data.get('venvs_found', 0)}")
    print("-" * 40)
    for venv in data.get("venvs", []):
        print(f"\nVenv: {venv.get('name')}  ({venv.get('path')})")
        print(f"  Pip        : {venv.get('pip_version', 'N/A')}")
        print(f"  Packages   : {venv.get('package_count', 0)}")
        list_packages = config.get("HEALTH", {}).get("list_packages", True)
        if list_packages:
            packages = venv.get("packages")
            if packages:
                for pkg in packages[:15]:
                    print(f"    - {pkg}")
                if len(packages) > 15:
                    print(f"    ... and {len(packages) - 15} more")