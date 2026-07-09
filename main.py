import sys, os
import colorama, time
from pathlib import Path
from ui.menu import display_menu
from utils.logger import log_manager

os.system("title Lab Manager Session")
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

def main():
    try:
        log_manager.setup_logging()
        logger = log_manager.get_logger("Tester")
        logger.info(f"Session launched at {time.ctime()}")
        display_menu()
    except KeyboardInterrupt, EOFError:
        print(f"\n\n{colorama.Fore.RED}    FORCEFULLY exiting...{colorama.Style.RESET_ALL}")
        logger.critical(f"Forceful exit at {time.ctime()}")
        time.sleep(1)
        return

if __name__ == "__main__":
    main()