import time, subprocess, os, ctypes, sys
from pathlib import Path
from utils.check import is_admin
from utils.env import save_env_status
from utils.execute import execute_task
from utils.logger import log_manager
from utils.settings import load_settings
from colorama import init, Fore, Style

init(autoreset=True)
logger = log_manager.get_logger("HealthWrapper")
config = load_settings()

class HealthCheck:
    def __init__(self):
        pass
    def show_env_status(self):
        print("\033[92m>>>   Checking for elevated permissions...\033[0m")
        time.sleep(2)
        if is_admin():
            print("\n--- Running system checks ---\n")
            print("\n")
            print("This might take a while. You may run other tasks.\n\n")
            data = {
                "python_version": subprocess.run(["python", "--version"], capture_output=True, text=True).stdout.strip(),
                "git_version": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip(),
                "is_admin": is_admin(),
                "venvs": [],}
            base_dirs = input("Enter paths to check for venvs: ")
            elements_to_scan = []
            if base_dirs:
                base_paths = base_dirs.split(" ")
                for base_path in base_paths:
                    base_path = Path(base_path)
                    elements_to_scan.append(base_path)
            if config.get("HEALTH").get("dirs_to_check"):
                for default_path in config.get("HEALTH").get("dirs_to_check"):
                    elements_to_scan.append(Path(default_path))
            python_version_check_cmd = ["python", "--version"]
            execute_task(python_version_check_cmd, "Python Check")
            git_version_check_cmd = ["git", "--version"]
            execute_task(git_version_check_cmd, "Git Check")
            print("\n   Checking Virtual Environments...\n")
            venvs = []
            for base_dir in elements_to_scan:
                if not base_dir:
                    continue
                global elements
                elements = [item for item in base_dir.iterdir() if (base_dir / item).is_dir()]
                for folder in elements:
                    if os.path.exists(f"{folder}/scripts/python.exe"):
                        print(f"-> Folder {Fore.GREEN}{folder.name}{Style.RESET_ALL} is a venv. Appending to venv list...") 
                        logger.info(f"{folder} is a virtual environment")
                        venvs.append(folder)
            logger.info(f"{len(venvs)} virtual environments are present in the base directory.")
            data["venvs_found"] = len(venvs)
            if not venvs:
                print("No venv is present inside the root folder. Skipping...")
            for venv in venvs:
                venv_path_s = os.path.join(venv, 'scripts', 'python.exe')
                freeze_command = [venv_path_s, '-m', 'pip', 'freeze']
                print(f"\nListing installed packages for '{venv}'...")
                pip_result = subprocess.run([venv_path_s, '-m', 'pip', '--version'], capture_output=True,text=True,check=True)
                print(f"-> Pip version for {venv.name}: {pip_result.stdout.strip()}")
                list_packages = config.get("HEALTH").get("list_packages", True)
                try:
                    freeze_result = subprocess.run(freeze_command,capture_output=True,text=True,check=True)
                    packages_to_upgrade = freeze_result.stdout.strip().splitlines()
                    if not packages_to_upgrade:
                        print("No packages found in the virtual environment.")
                    print(f"Found {len(packages_to_upgrade)} packages in {venv}")
                    if list_packages:
                        for line in packages_to_upgrade:
                            package_name = line.split('==')[0].strip()
                            print(f"   -- Package Name: {package_name}")
                            print(f"   -- Package Version: {line.split('==')[1].strip()}")
                            print("     "+("-"*15))
                    data["venvs"].append({
                        "name": venv.name,
                        "path": str(venv),
                        "pip_version": pip_result.stdout.strip(),
                        "package_count": len(packages_to_upgrade),
                        "packages": packages_to_upgrade if list_packages else []
                    })
                    save_env_status(data)
                except subprocess.CalledProcessError as e:
                    print(f"\nFreeze command failed.")
                    logger.error(f"Freeze command failed. Error log: {e}")            
                except Exception as e:
                    print(f"\033[91m\nAn unexpected error occurred. Check logs for details.\033[0m")
                    logger.exception(f"Unexpected crash occured, show_env_status: ")
        else:
            print("Relaunching as administrator to perform system scan...")
            script_path = os.path.abspath(sys.argv[0])
            admin_args = "--scan"
            logger.info(f"Relaunched application to elevate rights and run system scans.")
            logger.info("ADMIN Terminal Start.")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", script_path, admin_args, None, 1)

    def sys_scan(self):
        print("\033[92m>>>   Checking for elevated permissions...\033[0m")
        time.sleep(2)
        if is_admin():
            print("This might take a while. You may run other tasks.\n\n")
            sys_scan = input("\n\033[92mRun system scans (y/n): \033[0m")
            if sys_scan == "y":
                run_system_check_cmd = ["sfc", "/scannow"]
                execute_task(run_system_check_cmd, "System Scan")
                run_system_health_check_cmd = ["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"]
                execute_task(run_system_health_check_cmd, "System Health Check")
                system_health_restore_health_cmd = ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"]
                fix = input("\nRun '/RestoreHealth' to fix system image (y/n): ")
            else:
                return
            if fix == "y":
                execute_task(system_health_restore_health_cmd, "System Restore Health")
            logger.info("sfc and DISM commands successfully run.")
        else:
            print("Relaunching as administrator to perform system scan...")
            script_path = os.path.abspath(sys.argv[0])
            admin_args = "--scan"
            logger.info(f"Relaunched application to elevate rights and run system scans.")
            logger.info("ADMIN Terminal Start.")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", script_path, admin_args, None, 1)