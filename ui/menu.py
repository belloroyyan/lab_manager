from ui.handler import (handle_plem, handle_sort, handle_backup, handle_git, handle_log, handle_update, handle_venv, handle_network, handle_help, handle_settings, handle_syscheck, handle_io, handle_cleanup)
from utils.execute import clear_shell_wi
from utils.logger import log_manager
from utils.settings import load_settings, save_settings, init_settings
from utils.shell import hide_file, unhide_file
from utils.check import should_create_files
import sys
import time
import os
import platform
from config import IDENTITY_FILE, is_admin
from colorama import Fore, Style, init

logger = log_manager.get_logger("Menu")
init(autoreset=True)
config = load_settings()
MAIN = Fore.CYAN + Style.BRIGHT
DIM = Fore.WHITE + Style.DIM
GOLD = Fore.YELLOW
SUCCESS = Fore.GREEN
RESET = Style.RESET_ALL

def typewriter(text, speed=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print()

def display_dashboard():
    os.system('cls' if os.name == 'nt' else 'clear')

    print("======================================================================")
    print(f"                  {config['GENERAL']['school_name']} LAB MANAGER MAIN MENU                       ")
    print("======================================================================")
    print("\n  [1] Configure New PC / Install Software")
    print("  [2] Storage Operations")
    print("  [3] Backup Operations")
    print("  [4] Clone Git Repository")
    print("  [5] Virtual Environment")
    print("  [6] Run Network Tests and Commands")
    print("  [7] System Checks and Health")
    print("  [8] Cleanup Operations")
    print("  [9] I/O")
    print("\n  [L] Logs")
    print("  [S] Settings")
    print("  [U] Check For Updates")
    print("  [H] Read Help Manual")
    print("\n  [0] Exit Application")
    print("----------------------------------------------------------------------")
    
def display_menu(boot=True):
    clear_shell_wi()
    if boot:
        try:
            if config["GENERAL"]["first_run"]:
                if should_create_files():
                    init_settings()
                typewriter(f"    >>> INITIALIZING LAB MANAGER...", 0.01)
                typewriter(f"    >>> LOADING CORE MODULES AND UTILS...", 0.01)
                time.sleep(0.3)
                config["GENERAL"]["first_run"] = False
                save_settings(config)
                logger.info("First-run flag cleared for future sessions.")
                time.sleep(1.5)
            else: 
                typewriter(f"     Welcome back! Booting Lab Manager main menu...", speed=0.001)
                time.sleep(.5)
        except Exception as e: logger.error(f"Could not retrieve 'FIRST_RUN' info. {e}")

    while True:
        display_dashboard()

        choice = input(f"\n{SUCCESS}    Select option: {RESET}").strip().lower()

        if choice == "1":
            time.sleep(1)
            clear_shell_wi()
            handle_plem()
        elif choice == "2":
            time.sleep(1)
            clear_shell_wi()
            handle_sort()
        elif choice == "3":
            time.sleep(1)
            clear_shell_wi()
            handle_backup()
        elif choice == "4":
            time.sleep(1)
            clear_shell_wi()
            handle_git()
        elif choice == "5":
            time.sleep(1)
            clear_shell_wi()
            handle_venv()
        elif choice == "6":
            time.sleep(1)
            clear_shell_wi()
            handle_network()
        elif choice == "7":
            time.sleep(1)
            clear_shell_wi()
            handle_syscheck()
        elif choice == "8":
            time.sleep(1)
            clear_shell_wi()
            handle_cleanup()
        elif choice == "9":
            time.sleep(1)
            clear_shell_wi()
            handle_io()
        elif choice == "l" or choice == 'log':
            time.sleep(1)
            clear_shell_wi()
            handle_log()
        elif choice == "s" or choice == 'settings':
            time.sleep(1)
            clear_shell_wi()
            handle_settings()
        elif choice == "u" or choice == 'update':
            time.sleep(1)
            clear_shell_wi()
            handle_update()
        elif choice == "h" or choice == 'help':
            time.sleep(1)
            clear_shell_wi()
            handle_help()
        elif choice == "unhide":
            if platform.system() == "Windows":
                unhide_file(IDENTITY_FILE)
                print("\n\n\033[41mIdentity file unhidden.\n\n\033[0m")
            else:
                print("Unhide operation is only supported on Windows.")
        elif choice == "hide":
            if platform.system() == "Windows":
                hide_file(IDENTITY_FILE)
                print("\n\n\033[41mIdentity file hidden.\n\n\033[0m")
            else:
                print("Hide operation is only supported on Windows.")
        elif choice == "0":
            time.sleep(.5)
            print("Exiting Lab Manager.")
            break
        else:
            print("Invalid option.")
        time.sleep(1)
        clear_shell_wi()