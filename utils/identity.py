import json
import os
from pathlib import Path
from datetime import datetime, timezone
from cryptography.fernet import Fernet, InvalidToken
from colorama import Fore, Style
from config import IDENTITY_DIR, IDENTITY_FILE
from utils.shell import hide_file, unhide_file

def _ensure_identity_dir():
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)

def load_identity() -> dict:
    if not IDENTITY_FILE.exists():
        return {}
    unhide_file(IDENTITY_FILE)
    try:
        with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    except PermissionError:
        print(f"{Fore.RED}Failed to edit secret file. Try running as administrator.")
        return
    finally:
        hide_file(IDENTITY_FILE)

def save_identity(data: dict):
    _ensure_identity_dir()
    unhide_file(IDENTITY_FILE)
    try:
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except PermissionError:
        print(f"{Fore.RED}Failed to edit secret file. Try running as administrator.")   
        return    
    finally:
        hide_file(IDENTITY_FILE)

def generate_fernet_key() -> str:
    return Fernet.generate_key().decode("utf-8")

def save_key_to_identity(key: str):
    identity = load_identity()
    identity["secret_key"] = key
    if "created_at" not in identity:
        identity["created_at"] = datetime.now(timezone.utc).isoformat()
    if "school_name" not in identity:
        identity["school_name"] = "UNIOSUN"
    if "lab_name" not in identity:
        identity["lab_name"] = "FOCIT Lab"
    save_identity(identity)

def export_secret_key_file(key: str, destination: Path):
    destination = Path(destination)
    if destination.is_dir() or not destination.suffix:
        target = destination / "secret.key"
    else:
        target = destination
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(key.strip())
    return target

def generate_and_export_key(force: bool = False):
    identity = load_identity()
    existing_key = identity.get("secret_key")
    if existing_key and not force:
        print(f"{Fore.YELLOW}A secret key already exists.{Style.RESET_ALL}")
        choice = input("\nOverwrite it? (yes/no): ").strip().lower()
        if choice not in ("yes", "y"):
            print(f"{Fore.YELLOW}Key generation cancelled.{Style.RESET_ALL}")
            return None
    new_key = generate_fernet_key()
    save_key_to_identity(new_key)
    print(f"{Fore.GREEN}\nNew secret key generated and saved to identity file.{Style.RESET_ALL}")
    export_choice = input("\nExport secret.key file now? (yes/no): ").strip().lower()
    if export_choice in ("yes", "y"):
        dest = input("Enter destination folder (or leave blank for current directory): ").strip()
        dest_path = Path(dest) if dest else Path.cwd()
        try:
            final_path = export_secret_key_file(new_key, dest_path)
            print(f"\n{Fore.GREEN}Exported -> {final_path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Copy this file to a USB stick and use it on the lab PCs.{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Failed to export: {e}{Style.RESET_ALL}")
    return new_key

def get_fernet():
    identity = load_identity()
    key = identity.get("secret_key")
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception:
        return None

def encrypt_message(plaintext: str):
    f = get_fernet()
    if not f:
        return None
    token = f.encrypt(plaintext.encode()).decode()
    return token

def decrypt_message(message: str):
    if message.startswith("LAB|"):
        token = message[4:]
        f = get_fernet()
        if not f:
            return None
        try:
            return f.decrypt(token.encode()).decode()
        except (InvalidToken, Exception):
            return None
    else:
        f = get_fernet()
        if not f:
            return None
        try:
            return f.decrypt(message.encode()).decode()
        except (InvalidToken, Exception):
            return None