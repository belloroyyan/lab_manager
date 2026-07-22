import logging
import sys
import time, os
from pathlib import Path
from config import (LOG_DIR, CYAN, BOLD, GREEN, YELLOW, GRAY, RED, RESET, LOG_DIR)

def should_create_files():
    if getattr(sys, 'frozen', False) and "listener" in sys.executable.lower():
        return False
    return True
if should_create_files():
    LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "lab.log"
class LogHandler():
    def __init__(self):
        pass
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, encoding="utf-8"),
            ],
        )
    def get_logger(self, name):
        self.name = name
        return logging.getLogger(self.name)

    def analyze_logs(self, limit=5):
        try:
            limit = int(limit)
        except ValueError:
            print(f"{YELLOW}Invalid data type. Please input a numerical value.{RESET}")
            return
        if not LOG_FILE.exists():
            print(f"{RED}No log file found.{RESET}")
            return
        print(f"\n{CYAN}{BOLD}RECENT ACTIVITY LOGS (Last {limit}){RESET}")
        print(f"{GRAY}------------------------------------------------------------{RESET}")
        try:
            lines = LOG_FILE.read_text().splitlines()
            recent_lines = lines[-limit:]
            for line in recent_lines:
                if "ERROR" in line or "CRITICAL" in line:
                    print(f"{RED}{line}{RESET}")
                elif "WARNING" in line:
                    print(f"{YELLOW}{line}{RESET}")
                elif "SUCCESS" in line or "Task Started" in line:
                    print(f"{GREEN}{line}{RESET}")
                else:
                    print(f"{GRAY}{line}{RESET}")
        except Exception as e:
            print(f"{RED}Error reading log file: {e}{RESET}")
        print(f"{GRAY}------------------------------------------------------------{RESET}")

    def log_summary(self):
        if not LOG_FILE.exists():
            print(f"{RED}No log file found.{RESET}")
            return

        lines = [line for line in LOG_FILE.read_text().splitlines() if line.strip()]

        summary = {
            "critical": 0,
            "errors": 0,
            "warning": 0,
            "success": 0,
            "info": 0,
        }
        labels = {
            "critical": "Critical",
            "errors": "Error",
            "warning": "Warning",
            "success": "Successful",
            "info": "Info",
        }
        colors = {
            "critical": RED,
            "errors": RED,
            "warning": YELLOW,
            "success": GREEN,
            "info": GRAY,
        }

        for line in lines:
            if "CRITICAL" in line:
                summary["critical"] += 1
            elif "ERROR" in line:
                summary["errors"] += 1
            elif "WARNING" in line:
                summary["warning"] += 1
            elif "SUCCESS" in line or "Task Started" in line:
                summary["success"] += 1
            elif "---" in line:
                continue
            else:
                summary["info"] += 1

        total = len(lines) - 1
        print(f"  {CYAN}Total{RESET}: {total} entries.")
        for key, count in summary.items():
            print(f"    {colors[key]}{labels[key]} entries{RESET}: {count}")

    def clear_system_logs(self):
        print(f"\n{YELLOW}{BOLD} WARNING: This will permanently delete all activity history.{RESET}")
        confirm = input(f"    Are you sure? (y/n): ").lower().strip()
        if confirm == 'y':
            try:
                with LOG_FILE.open('w') as f:
                    f.write(f"--- Log Cleared by {os.path.expanduser("~").split("\\")[-1]} at {time.ctime()} ---\n")
                logging.info("Log file was reset.")
                print(f"\n{GREEN}Logs cleared successfully.{RESET}")
            except Exception as e:
                logging.exception(f"Failed to clear logs: {e}")
                print(f"{RED}Error: Access denied to log file.{RESET}")
        else:
            print(f"\n{GRAY}Operation cancelled.{RESET}")
    
    def get_log_count(self):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return sum(1 for line in f)
        except FileNotFoundError:
            return 0
    
log_manager = LogHandler()