import webbrowser
import requests
import re
from xml.etree import ElementTree as ET
from packaging import version
from colorama import Fore, Style, init
from config import APP_VERSION, GITHUB_REPO
from utils.logger import log_manager

logger = log_manager.get_logger("Updater")
init(autoreset=True)

RELEASES_URL = f"https://belloroyyan.github.io/lab_manager#downloads"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
FEED_URL = "https://github.com/belloroyyan/lab_manager/releases.atom"

def get_latest_release():
    try:
        response = requests.get(API_URL, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch latest release: {e}")
        return None

def get_latest_release_from_atom():
    try:
        resp = requests.get(FEED_URL, timeout=8)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            return None
        title = entry.find("atom:title", ns)
        if title is None or not title.text:
            return None
        match = re.search(r"v?(\d+\.\d+\.\d+)", title.text)
        return match.group(1) if match else None
    except Exception as e:
        logger.error(f"Failed to fetch latest release from Atom feed: {e}")
        return None

def is_newer_version(remote_version: str, local_version: str):
    try:
        return version.parse(remote_version) > version.parse(local_version)
    except Exception:
        return False

def check_and_update(auto_open = True):
    release = get_latest_release()
    if release:
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
    else:
        release = get_latest_release_from_atom()
        if release:
            remote_version = release
            if not is_newer_version(remote_version, APP_VERSION):
                print(f"{Fore.GREEN}You are running the latest version (v{APP_VERSION}).{Style.RESET_ALL}")
                logger.info("Application is up to date.")
                return "up_to_date"

            print("\n" + "=" * 60)
            print(f"  NEW VERSION AVAILABLE FROM GITHUB(@belloroyyan): v{remote_version}")
            print("=" * 60)
            print(f"  Current version : v{APP_VERSION}")
            print(f"  Latest version  : v{remote_version}")
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
        else:
            print(f"{Fore.YELLOW}Could not determine the latest version. Please check manually at {RELEASES_URL}.{Style.RESET_ALL}")
            logger.warning("Failed to fetch latest release information.")
            return "error"