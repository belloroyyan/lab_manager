from core.file_sorter import FileSorter
from core.git import GitHandler
from core.venv import VenvHandler
from core.network import NetworkHandler
from core.backup import BackupManager
from core.cleanup import CleanupManager
from core.inventory import gen_soft_report, generate_lan_system_report
from utils.drive_manager import get_drives
from utils.execute import clear_shell
from utils.database import get_all_saved_devices
from utils.logger import log_manager
from utils.help import display_help
from utils.settings import (init_settings, display_all_settings, load_settings, edit_numeric_setting, edit_boolean_setting, edit_list_setting, edit_string_setting, save_settings, get_min_max)
from utils.shell import open_shell_access
from utils.listener import start_listener
from config import (CYAN, BOLD, GREEN, YELLOW, GRAY, RED, PROJECT_ROOT, BACKUP_DIR)
from colorama import Fore, Back, Style, init

init(autoreset=True)
logger = log_manager.get_logger("Handler")

PRIMARY = Fore.CYAN + Style.BRIGHT
SECONDARY = Fore.BLUE
SUCCESS = Fore.GREEN
WARNING = Fore.YELLOW
MUTED = Fore.WHITE + Style.DIM
RESET = Style.RESET_ALL

def handle_plem():
    print(f"{YELLOW}PLEM runs as a separate module of LAB.\nNavigate to PLEM dir and run `{BOLD}plem.bat`.{RESET}")
    clear_shell()

def handle_sort():
    print("Detected drives:\n")
    drives = get_drives()
    i = 0
    for d in drives:
        print(f"{i}. {d['name']} ({d['letter']}) [{d['type']}] "
            f"{d['free_gb']}GB free / {d['total_gb']}GB total")
        i+=1
    if drives:
        choice = input(f"{GREEN}\nSelect drive number (0 for custom path): {RESET}")
        try:
            choice = int(choice)
        except ValueError:
            print(f"{RED}Invalid data type. Please input an integer as choice.{RESET}")
            clear_shell()
            return
        if not choice and choice != 0:
            print(f"Choice not specified.")
            clear_shell()
            return
        if choice not in range(0, i):
            print(f"{YELLOW}This drive number does not exist.{RESET}")
            clear_shell()
            return
        path = input(F"{GREEN}Enter path: {RESET}")
    else:
        path = input(F"{GREEN}Enter path: {RESET}")
    if not path:
        print(F"Path not specified.")
        clear_shell()
        return
    mode = input("Mode (move/copy) [move]: ").strip() or "move"
    sorter = FileSorter(path, mode=mode)
    sort_types = ["Rule-Based Sort", "Auto-Group Shows"]
    for i, s_t in enumerate(sort_types, 1):
        print(f"   {i}.  {s_t}")
    try:
        item_num = int(input("\nInput sort_type choice:  "))
        if item_num == 1:
            sorter.sort()
            clear_shell()
            return
        elif item_num == 2:
            sorter.sort_repeat()
            clear_shell()
            return
        else: print("Invalid list number selection.")
    except ValueError:
        print("Invalid list number type.")    
        clear_shell()
        return

def handle_git():
    git_handler = GitHandler()
    print(f"""======================================================================
                            GIT OPS MENU                       
======================================================================

[1] Clone Git Repository
[2] Open Git Bash
[0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(F"{GREEN}Select what git operation you wish to perform: {RESET}").strip()
    if choice == "1":
        git_handler.clone()
    elif choice == "2":
        git_handler.open_git_bash()
    elif choice == "0":
        return
    else : print("Invalid choice.")
    clear_shell()

def handle_backup():
    config = load_settings()
    choice = input(F"{GREEN}Input source path(s) for backup: {RESET}").strip()
    password = input(f"{YELLOW}Input password (leave blank if none): {RESET}")
    source_paths = choice.split(" ") if choice else config["BACKUP"]["default_sources"]
    backup_manager = BackupManager(PROJECT_ROOT, password)
    backup_manager.run_backup(source_paths)
    clear_shell()

def handle_log():
    print(f"""======================================================================
                            LOG OPS MENU                        
======================================================================""")
    log_manager.log_summary()
    print("""
  [1] View Log History
  [2] Clear Activity
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(F"{GREEN}Select what log operation you wish to perform: {RESET}").strip()
    if choice == "1":
        limit = input(f"\n{GREEN}Last log count limit: {RESET}")
        log_manager.analyze_logs(limit=limit)
    elif choice == "2":
        log_manager.clear_system_logs()
    elif choice == "0":
        return
    else : print("Invalid choice.")
    clear_shell()

def handle_venv():
    venv_handler = VenvHandler()
    print(f"""======================================================================
                            VENV OPS MENU                        
======================================================================

  [1] Create Virtual Environment
  [2] Update Venv Packages
  [3] Install Packages
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(F"{GREEN}Select what venv operation you wish to perform: {RESET}").strip()
    if choice == "1":
        venv_handler.create_venv("")
    elif choice == "2":
        venv_handler.update_venv_deps()
    elif choice == "3":
        venv_handler.install_packages()
    elif choice == "0":
        return
    else : print("Invalid choice.")
    clear_shell()

def handle_network():
    networkhandler = NetworkHandler()
    print(f"""======================================================================
                            NETWORK OPS MENU                        
======================================================================

  [1] Scan Local Area Network
  [2] Broadcast Message
  [3] Change Default Listening Port
  [4] Retrieved Stored Records
  [5] Start Listener
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(F"{GREEN}Select what network operation you wish to perform: {RESET}").strip()
    if choice == "1":
        networkhandler.scan_entire_lan()
    elif choice == "2":
        choice2 = input(f"{Fore.GREEN}\n'all' devices or 'selected' devices?: {Style.RESET_ALL}").strip()
        if choice2 == 'all':
            networkhandler.create_message("")
        if choice2 == 'selected':
            ip = input(f'{Fore.GREEN}\nEnter ip: {Style.RESET_ALL}')
            if not ip:
                print(f"Invalid input.")
                clear_shell()
                return
            networkhandler.create_message(ip)
    elif choice == '3':
        networkhandler.change_default_port()
    elif choice == '4':
        devices = get_all_saved_devices()
        for dev in devices:
            print(dev)
    elif choice == '5':
        start_listener(8088)
    elif choice == "0":
        return
    else : print("Invalid choice.")
    clear_shell()

def handle_syscheck():
    print(f"""======================================================================
                            SYSTEM HEALTH MENU                        
======================================================================

  [1] Scan Local Area Network
  [2] Broadcast Message
  [3] Retrieved Stored Records
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")

def handle_io():
    print(f"""======================================================================
                                    I/O MENU                        
======================================================================

  [1] Open Shell Access
  [2] Run Inventory Check
  [3] Run Inventory Check Across LAN
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(f"{GREEN}Select what i/o operation you wish to perform: {RESET}").strip()
    if choice == "1":
        open_shell_access()
    elif choice == "2":
        gen_soft_report()
    elif choice == "3":
        generate_lan_system_report()
    elif choice == "0":
        return
    else: print("Invalid choice.")
    clear_shell()

def handle_cleanup():
    cleanuphandler = CleanupManager()
    print(f"""======================================================================
                                CLEANUP MENU                        
======================================================================

  [1] Show Top Space Consumers
  [2] Clean Temporary Files
  [3] Empty Recycle Bin
  [4] Move Large Files to Review Folder
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    choice = input(f"{GREEN}Select what cleanup operation you wish to perform: {RESET}").strip()
    if choice == "1":
        path = input(f"{GREEN}Enter path to analyze (leave blank for user folder): {RESET}").strip()
        cleanuphandler.show_top_space_consumers(path if path else None)
    elif choice == "2":
        cleanuphandler.clean_temp_files()
    elif choice == "3":
        cleanuphandler.empty_recycle_bin()
    elif choice == "4":
        path = input(f"{GREEN}Enter path to scan for large files: {RESET}").strip()
        size = input(f"{GREEN}Minimum size in MB to move (default 100): {RESET}").strip()
        min_size = int(size) if size.isdigit() else 100
        cleanuphandler.move_large_files_to_review(path, min_size)
    elif choice == "0":
        pass
    else:
        print("Invalid choice.")
    clear_shell()

def handle_settings():
    config = load_settings()
    if not config:
        clear_shell()
        return
    print("\n======================================================================")
    print("                             SETTINGS MENU                             ")
    print("======================================================================\n")
    print("  [edit] Modify Specific Settings\n\n")
    display_all_settings(config, 2)
    print("""
  [R] Restore To Default
  [0] Back to Main Menu""")
    print("----------------------------------------------------------------------\n")
    
    choice = input(f"{GREEN}Input choice: {RESET}").strip().lower()
    if not choice:
        return
    try:
        if choice[0:4] == "edit":
            section_ = input(f"{GREEN}Input setting (section_name): {RESET}").strip().upper()
            section = config.get(section_)
            display_all_settings(config[section_], 3)
            key_ = input(f"{GREEN}Input setting (key): {RESET}").strip().lower()
            key = section.get(key_)
            if isinstance(key, bool):
                edit_boolean_setting(section_, key_)
                return
            if isinstance(key, int):
                min_, max_ = get_min_max(key_)
                edit_numeric_setting(section_, key_, min_, max_)
                return
            elif isinstance(key, list):
                edit_list_setting(section_, key_)
                return
            elif isinstance(key, str):
                edit_string_setting(section_, key_)
                return            
            save_settings(config)
        elif choice == "r":
            init_settings()
        elif choice == "0":
            return
        else: print("Invalid value.")
    except KeyError:
        print("Invalid key.")
    clear_shell()
        
def handle_help():
    display_help()