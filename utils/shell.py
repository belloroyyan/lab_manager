import subprocess
import time
from colorama import init, Fore, Style
from utils.logger import log_manager

logger = log_manager.get_logger("ShellWrapper")
CYAN = Fore.CYAN
BOLD = Style.BRIGHT
GRAY = Fore.LIGHTBLACK_EX
RESET = Style.RESET_ALL
RED = Fore.RED
GREEN = Fore.GREEN

def open_shell_access():
    logger.info("User requested Shell Access.")
    print(f"\n{CYAN}{BOLD}>>> SHELL ACCESS ACTIVATED{RESET}")
    print(f"{GRAY}Type 'exit' to return to Lab Manager Menu.{RESET}\n")
    try:
        subprocess.run("cmd.exe /K prompt LAB-SHELL: $P$G", shell=True)
        logger.info("User exited Shell Access.")
        print(f"\n{CYAN}{BOLD}<<< Returned to Lab Manager.{RESET}")
        time.sleep(1)
    except Exception as e:
        logger.exception(f"Failed to launch shell access: {e}")
        print(f"{RED}Error: Could not launch shell.{RESET}")