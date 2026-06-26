import sys
import time
import os
from utils.logger import log_manager
from config import README_DIR
from colorama import init, Fore, Style

logger = log_manager.get_logger("Help")
init(autoreset=True)
magenta = Fore.MAGENTA
green = Fore.GREEN
reset = Style.RESET_ALL
logger = log_manager.get_logger("VenvHandler")


print(f"\n    {magenta}Checking for help folder...")
if not os.path.exists(README_DIR):
    os.mkdir(README_DIR)
    logger.info("Created `help` folder.")
time.sleep(.5)
print(f"\n    {magenta}Found `help` folder within base directory.{reset}")
print(f"    {README_DIR}")
def display_help():
    readme_path = README_DIR / 'readme.txt'
    try:
        with readme_path.open('r', encoding='utf-8') as readme:
            for line in readme:
                is_header = line.strip().startswith('>>')
                output_line = green + line + reset if is_header else line
                print(output_line)
    except FileNotFoundError:
        logger.error(f"Manual missing at {readme_path}")
        print(f"Error: README.txt not found.")
    input("\nPress ENTER key to continue...")