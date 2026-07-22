import webbrowser
import requests
from packaging import version
from colorama import Fore, Style, init
from config import APP_VERSION, GITHUB_REPO
from utils.logger import log_manager

logger = log_manager.get_logger("Updater")
init(autoreset=True)

RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def get_latest_release():
    try:
        response = requests.get(API_URL, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch latest release: {e}")
        return None

def is_newer_version(remote_version: str, local_version: str):
    try:
        return version.parse(remote_version) > version.parse(local_version)
    except Exception:
        return False

def check_and_update(auto_open = True):
    release = get_latest_release()
    if not release:
        print(f"{Fore.YELLOW}Could not check for updates. Please check your internet connection.{Style.RESET_ALL}")
        return None
    remote_version = release.get("tag_name", "").lstrip("v")
    release_notes = release.get("body", "No release notes provided.")
    published_at = release.get("published_at", "")[:10]
    if not is_newer_version(remote_version, APP_VERSION):
        print(f"{Fore.GREEN}You are running the latest version (v{APP_VERSION}).{Style.RESET_ALL}")
        logger.info("Application is up to date.")
        return "up_to_date"

    print("\n" + "=" * 60)
    print(f"  NEW VERSION AVAILABLE FROM GITHUB(@belloroyyan): v{remote_version}")
    print("=" * 60)
    print(f"  Current version : v{APP_VERSION}")
    print(f"  Latest version  : v{remote_version}")
    print(f"  Published       : {published_at}")
    print("-" * 60)
    print("  Release Notes:")
    print(release_notes[:600] + ("..." if len(release_notes) > 600 else ""))
    print("=" * 60)

    if auto_open:
        choice = input(f"\n{Fore.GREEN}Open download page now? (y/n): {Style.RESET_ALL}").strip().lower()
        if choice == "y":
            print("Opening GitHub Releases page...")
            webbrowser.open(RELEASES_URL)
            print(f"{Fore.CYAN}Please download and run the latest installer.{Style.RESET_ALL}")
        else:
            print("You can update later from the GitHub Releases page.")
    else:
        print(f"\nDownload the latest version here:\n{RELEASES_URL}")
    return "update_available"