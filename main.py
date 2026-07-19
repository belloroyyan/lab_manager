try:
    import sys, os
    import colorama, time
    from pathlib import Path
    from config import DESKTOP_DIR
    if not DESKTOP_DIR.exists():
        os.mkdir(DESKTOP_DIR)
    from ui.menu import display_menu
    from utils.logger import log_manager
    from utils.update import check_and_update
    from utils.execute import clear_shell_wi
    os.system("title Lab Manager Session")
    PROJECT_ROOT = Path(__file__).parent
    sys.path.append(str(PROJECT_ROOT))
except ImportError as e:
    print(f"\n\n\033[41mFailed to import modules: {e}\033[0m")
    time.sleep(2)
    sys.exit(1)
except (KeyboardInterrupt, EOFError):
    print("\n\n\033[41mProgram interrupted mid-load.\033[0m")
    time.sleep(2)
    sys.exit(1)

def main():
    try:
        log_manager.setup_logging()
        logger = log_manager.get_logger("Main")
        logger.info(f"Session launched at {time.ctime()}")
        clear_shell_wi()
        check_and_update(auto_download=False)
        display_menu()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{colorama.Fore.RED}    Cancelling process...{colorama.Style.RESET_ALL}")
        logger.critical(f"Forceful exit at {time.ctime()}")
        time.sleep(1)
    except Exception as e:
        print(f"\n\n{colorama.Fore.RED}    Unexpected error.{colorama.Style.RESET_ALL}")
        logger.exception(f"Unexpected error in main: {e}")
        time.sleep(1)
    finally:
        display_menu(boot=False)

if __name__ == "__main__":
    main()