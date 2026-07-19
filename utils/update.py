import os
import sys
import requests
from pathlib import Path
from packaging import version
from colorama import Fore, Style, init
from config import APP_VERSION, GITHUB_REPO, TEMP_DIR, BINARY_NAME
from utils.logger import log_manager

logger = log_manager.get_logger("Updater")
init(autoreset=True)

def get_latest_release() -> dict | None:
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch latest release. {e}")
        return None

def is_newer_version(remote_version: str, local_version: str) -> bool:
    try:
        return version.parse(remote_version) > version.parse(local_version)
    except Exception:
        return False

def find_asset(release_data: dict, asset_name: str = "main.exe") -> str | None:
    for asset in release_data.get("assets", []):
        if asset["name"].lower() == asset_name.lower():
            return asset["browser_download_url"]
    return None

def download_file(url: str, save_path: Path) -> bool:
    try:
        logger.info(f"Downloading update from: {url}")
        response = requests.get(url, stream=True, timeout=150)
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Download complete -> {save_path}")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False
    except requests.exceptions.Timeout:
        logger.error("Download timed out.")
        return False


def create_updater_script(new_binary: Path):
    current_exe = Path(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
    bat_path = TEMP_DIR / "apply_update.bat"

    script = f"""@echo off
echo Applying Lab Manager update...
timeout /t 3 /nobreak >nul

:retry
tasklist /FI "IMAGENAME eq {current_exe.name}" 2>NUL | find /I /N "{current_exe.name}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 2 /nobreak >nul
    goto retry
)

copy /Y "{new_binary}" "{current_exe}"
if %ERRORLEVEL%==0 (
    echo Update applied successfully!
) else (
    echo Failed to apply update.
)
del "%~f0"
"""

    with open(bat_path, "w") as f:
        f.write(script)

    os.startfile(str(bat_path))


def check_and_update(auto_download: bool = True):
    release = get_latest_release()
    if not release:
        return None
    remote_version = release.get("tag_name", "").lstrip("v")
    release_notes = release.get("body", "No release notes.")
    published_at = release.get("published_at", "")
    if not is_newer_version(remote_version, APP_VERSION):
        logger.info("Application is up to date.")
        return "Application is up to date."
    print("\n" + "="*60)
    print(f"  NEW VERSION AVAILABLE FROM GITHUB(@belloroyyan): v{remote_version}")
    print("="*60)
    print(f"  Current version : v{APP_VERSION}")
    print(f"  Latest version  : v{remote_version}")
    print(f"  Published       : {published_at}")
    print("-"*60)
    print("  Release Notes:")
    print(release_notes[:500] + ("..." if len(release_notes) > 500 else ""))
    print("="*60)

    if not auto_download:
        print("[-] Please download the update manually from GitHub Releases.")
        return "done"
    choice = input("\nDownload and install this update now? (y/n): ").strip().lower()
    if choice != "y":
        return "done"
    download_url = find_asset(release, BINARY_NAME)
    if not download_url:
        print(f"[ERROR] Could not find '{BINARY_NAME}' in the release assets.")
        return "fail"
    TEMP_DIR.mkdir(exist_ok=True)
    new_binary = TEMP_DIR / BINARY_NAME

    print("\nDownloading update...")
    if download_file(download_url, new_binary):
        create_updater_script(new_binary)
        print("\nUpdate downloaded successfully!")
        print("The new version will be applied when you restart Lab Manager.")
        input("Press Enter to exit...")
        sys.exit(0)
    else:
        print("Download failed. Please try again later.")