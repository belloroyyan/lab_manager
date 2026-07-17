import json, os
from pathlib import Path
from colorama import Fore, Style, init
from config import SETTINGS
from utils.logger import log_manager

init(autoreset=True)
magenta = Fore.MAGENTA
green = Fore.GREEN
red = Fore.RED
reset = Style.RESET_ALL
logger = log_manager.get_logger("Settings")
home = Path(os.path.expanduser("~"))

DEFAULT_SETTINGS = {
    "GENERAL" : {
        "first_run" : True,
        "school_name" : "UNIOSUN",
        "lab_name" : "UNIOSUN FOCIT Lab"
    },
    "NETWORK": {
        "default_port": 5050,
        "max_port_attempts": 5,
        "auto_scan_on_startup": True,
        "ping_timeout" : 500
    },
    "LISTENER" : {
        "port" : 8088,
        "secret" : "3080"
    },
    "BACKUP": {
        "skip" : "False",
        "default_destination": "lab_manager_backups",
        "extensions" : {
            "Images": [".jpg", ".png", ".jpeg", ".jfif", ".jp2", ".heic", ".ico"],
            "Audio": [".mp3", ".wav"],
            "Videos": [".mp4", ".mkv"],
            "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".epub"],
            "Code": [".py", ".cpp", ".js", ".css", ".json", ".ipynb", ".ini"],
            "Archives": [".zip", ".rar", ".aac"],
            "Subtitles": [".srt", ".ass"],
            "Executables": [".exe", ".apk", ".msi"],
            "Others": []
        },
        "forbidden_extensions": [".exe", ".msi", ".bat", ".cmd", ".sys", ".dll", ".lnk", ".spec"],
        "ignored_folders": ["venv", ".git", "__pycache__", "node_modules", "backup_staging", "lab_manager_backups"],
        "default_sources": [],
        "default_venv_destination" : f"{home / "Desktop"}"
    },
    "SOFTWARE_CHECKS" : {
        "Python" : {
            "command" : ["py", "python", "python3"],
            "paths" : [r"C:/Python312/python.exe", r"C:/Program Files/Python312/python.exe", f"{home}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe", r"C:/Python311/python.exe", r"C:/Program Files/Python311/python.exe", f"{home}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe", r"C:/Python313/python.exe", r"C:/Program Files/Python313/python.exe", f"{home}\\AppData\\Local\\Programs\\Python\\Python313\\python.exe", r"C:/Python314/python.exe", r"C:/Program Files/Python314/python.exe", f"{home}\\AppData\\Local\\Programs\\Python\\Python314\\python.exe"],
            "version_flag" : "--version"
        },
        "VS Code" : {
            "command" : ["code"],
            "paths" : [r"C:\Users\Kato\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
            "version_flag" : "--v"
        },
        "Git" : {
            "command" : ["git"],
            "paths" : [r"C:/Program Files/Git"],
            "version_flag" : "-v"
        }
    },
    "SECURITY": {
        "manage_firewall_rules": True,
        "require_admin_privileges": False
    }
}

def init_settings():
    print(f"    {magenta}Initializing default settings...{reset}")
    try:
        with open(SETTINGS, "w") as s:
            json.dump(DEFAULT_SETTINGS, s, indent=4)
        print("    Successfully initialized default settings.")
        logger.info("New settings.json file created.")
        return DEFAULT_SETTINGS
    except Exception as e:
        print("Could not initialize settings.")
        logger.exception(f"Error creating settings.json: {e}")
        return DEFAULT_SETTINGS

def load_settings():
    if not SETTINGS.exists():
        print("Settings file not found. Returning default settings.")
        logger.warning(f"Could not find settings.json: {SETTINGS}")
        return init_settings()
    try:
        with open(SETTINGS, "r") as s:
            return json.load(s)
    except json.JSONDecodeError as e:
        print("Settings file corrupted. Initializing default settings.")
        logger.warning(f"Error decoding json file: {e}")
        return False

def display_all_settings(settings_dict : dict, indent_level : int):
    spacing = "    " * indent_level
    for key, value in settings_dict.items():
        if isinstance(value, dict):
            print(f"{spacing}{Fore.BLUE}{Style.BRIGHT}[{key.upper()}]{Style.RESET_ALL}")
            display_all_settings(value, indent_level+1)
            continue
        if isinstance(value, list):
            print(f"{spacing + "   "}{Fore.CYAN}{key}{Style.RESET_ALL}")
            for i in value:
                print(f"{spacing}  •   {i}")
                continue
        else:
            if isinstance(value, bool):
                val_color = green if value else red
            else:
                val_color = Fore.WHITE
            print(f"{spacing}{Fore.CYAN}{key:<22}{Style.RESET_ALL}: {val_color}{value}{Style.RESET_ALL}")

def edit_string_setting(section, key):
    config = load_settings()
    print(f"\nEditing {Fore.CYAN}{key.replace('_', ' ').title()}{reset}")
    user_input = input(f"\n{Fore.GREEN}Enter new value or press Enter to cancel: {Style.RESET_ALL}").strip()
    if not user_input:
        print("Modification cancelled.")
        return
    config[section][key] = str(user_input)
    save_settings(config)
    print(f"[SUCCESS] {key} updated to {user_input}!")

def edit_numeric_setting(section, key, min_val, max_val):
    config = load_settings()    
    print(f"\nEditing {Fore.CYAN}{key.replace('_', ' ').title()}{reset}")
    user_input = input(f"\nEnter new value ({min_val}-{max_val}) or press Enter to cancel: ").strip()
    if not user_input:
        print("Modification cancelled.")
        return
    try:
        new_value = int(user_input)
        if min_val <= new_value <= max_val:
            config[section][key] = new_value
            save_settings(config)
            print(f"[SUCCESS] {key} updated to {new_value}!")
        else:
            print(f"[ERROR] Value must be between {min_val} and {max_val}.")
    except ValueError:
        print("[ERROR] Input must be a valid integer.")

def edit_boolean_setting(section, key):
    config = load_settings()
    current_value = config[section][key]

    print(f"\nEditing {Fore.CYAN}{key.replace('_', ' ').title()}{reset}")
    print(f"Current Status: {'ENABLED' if current_value else 'DISABLED'}")

    user_input = input(f"\n{green}Enable this feature? (Y/N or press Enter to cancel): {reset}").strip().lower()
    if not user_input:
        return

    if user_input == 'y':
        config[section][key] = True
    elif user_input == 'n':
        config[section][key] = False
    else:
        print("[ERROR] Invalid choice. Please enter Y or N.")
        return

    save_settings(config)
    print(f"[SUCCESS] {key} updated successfully.")

def edit_list_setting(section, key):
    config = load_settings()
    current_list = config[section][key]
    
    print(f"\n--- Managing {Fore.CYAN}{key.title()}{reset} ---")
    for index, item in enumerate(current_list, start=1):
        print(f"  {index}. {item}")
        
    choice = input("\n[A] Add Item  |  [R] Remove Item  |  [0] Cancel: ").strip().lower()
    
    if choice == 'a':
        new_item = input("\nEnter new value to add (e.g., .dll): ").strip()
        if new_item and new_item not in current_list:
            current_list.append(new_item)
            save_settings(config)
            print(f"Added {new_item}!")
    elif choice == 'r':
        try:
            item_num = int(input("\nEnter the number of the item to delete: "))
            if 1 <= item_num <= len(current_list):
                removed = current_list.pop(item_num - 1)
                save_settings(config)
                print(f"Removed {removed} successfully.")
        except ValueError:
            print("Invalid list number selection.")

def get_min_max(key):
    bounds = {
        "default_port": (1024, 65535),
        "max_port_attempts": (5, 25),
        "ping_timeout": (100, 5000),
    }
    return bounds.get(key, (None, None))
    
def save_settings(settings_dict):
    with open(SETTINGS, "w") as s:
        json.dump(settings_dict, s, indent=4)
    logger.info("Settings successfully modified.")
    