import subprocess
import time
import psutil
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

def kill_port(port=8088):
    is_killed = False
    for conn in psutil.net_connections():
        if conn.laddr.port == 8088 and conn.pid:
            try:
                proc = psutil.Process(pid=conn.pid)
                proc.kill()
                print(f"Killed port {port} with PID {conn.pid}.")
                is_killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"Permission denied to kill port {port}.")
    if not is_killed:
        print(f"Port {port} is free.")

def kill_process_by_name(process_name):
    count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()
                print(f"Success: Terminated {proc.info['name']} (PID: {proc.info['pid']})")
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if count == 0:
        print(f"Info: No running process found matching '{process_name}'")