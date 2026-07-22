import subprocess
import os
import time
import shutil
from utils.check import find_system_python
from utils.logger import log_manager
from utils.execute import (execute_task, clear_shell)
from utils.settings import load_settings
from config import VENV_DIR
from colorama import init, Fore, Style
from pathlib import Path

init(autoreset=True)
magenta = Fore.MAGENTA
reset = Style.RESET_ALL
logger = log_manager.get_logger("VenvHandler")
config = load_settings()

print(f"\n    {magenta}Checking for venvs folder...")
if not os.path.exists(VENV_DIR):
    os.mkdir(VENV_DIR)
    logger.info("Created `venvs` folder.")
time.sleep(.5)
print(f"\n    {magenta}Found `venvs` folder within base directory.{reset}")
print(f"    {VENV_DIR}")

class VenvHandler():
    def __init__(self):
        pass
    def create_venv (self, name):
        venv_name = name if name else input("\n\033[92mInput virtual environment name: \033[0m")
        path = input(f"\n\033[92mInput new virtual environment {Style.RESET_ALL}'{venv_name}'{Fore.GREEN} destination path: \033[0m")
        if not path:
            path = VENV_DIR
        path = Path(path)
        global_py = find_system_python()
        if not global_py:
            print("Python is not installed on this device.")
            print("Cannot create virtual environment.")
            return
        if os.path.exists(path / venv_name):
            print(f"\nVirtual environment '{venv_name}' already exists.\n")
            return
        print(f"\nCreating virtual environment '{venv_name}' via {global_py}...\n")
        try:
            cmd_string = f'"{global_py}" -m venv "{venv_name}"'
            subprocess.run(cmd_string, check=True, shell=True, capture_output=False)
            logger.info(f"Created {venv_name} successfully")
            print("  Venv created successfully!\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating virtual environment: {e}")
            print("Error: Failed to create Venv.\n")
            print(f"Command executed: {e.cmd}")
            print(f"Stdout: {e.stdout.strip()}")
            print(f"Stderr: {e.stderr.strip()}")
        try:
            shutil.move(Path(os.getcwd()) / venv_name, path)
            print(f"Moved to {venv_name} to {path}.")
        except Exception as e:
            print(f"[ERROR] Failed to move venv {venv_name} to destination.\nCheck working directory of the application.")
        
    def update_venv_deps(self):
        venv_to_update = input("\n\033[92mEnter venv name ('all' to update all venvs): \033[0m")
        venv_to_update_path = Path(venv_to_update)
        if venv_to_update_path.exists():
            if (venv_to_update_path / "pyvenv.cfg").exists() and (venv_to_update_path / "Scripts" / "python.exe").exists() and(venv_to_update_path / "Scripts" / "pip.exe").exists():
                print(f"{venv_to_update_path.name} is a venv. Parsing through libs...")
                py_path = venv_to_update_path / "Scripts" / "python.exe"
                pip_cmd = [str(py_path), "-m", "pip", "install", "--upgrade", "pip"]
                execute_task(pip_cmd, "Upgrading PIP")
                freeze_command = [py_path, "-m", "pip", "freeze"]
                print("Listing installed packages to upgrade...")
                try:
                    freeze_result = subprocess.run(freeze_command,capture_output=True,text=True,check=True)
                    packages_to_upgrade = freeze_result.stdout.strip().splitlines()
                    if not packages_to_upgrade:
                        print("No packages found in the virtual environment to upgrade.")
                        time.sleep(2)
                    print(f"Found {len(packages_to_upgrade)} packages. Starting individual upgrades...")
                    for line in packages_to_upgrade:
                        package_name = line.split('==')[0].strip()
                        upgrade_command = [py_path, '-m', 'pip', 'install', '-U', package_name]
                        print(f"-> Upgrading {package_name}...")
                        subprocess.run(upgrade_command,capture_output=False,check=True)
                        logger.info(f"Upgrading {line} started.")
                    print("\n--- All packages in the virtual environment have been upgraded. ---")
                except subprocess.CalledProcessError as e:
                    print(f"\nUpgrade failed for a package. Check the logs.")
                    logger.error("Error encountered while upgrading package.")
                    logger.error(f"Error log: {e}")        
                except Exception as e:
                    print(f"\nAn unexpected error occurred: {e}")
                    logger.exception(f"Traceback for failed upgrade, update_venv_deps: {e}")
                    print("All PIP packages updated.")
                    print(f"Finished updating packages for {venv_to_update_path.name}")
                return
            else: 
                print("The specified path exists but is not a virtual environment.")
                return
        else: 
            print("Specified path does not exist.")
        venvs = []
        if venv_to_update == "all":
            elements = [item for item in VENV_DIR.glob("*") if (VENV_DIR / item).is_dir()]
            print(elements)
            for folder in elements:
                if (folder / "pyvenv.cfg").exists():
                    print(f"Folder {folder} is a venv. Appending to venv list...") 
                    venvs.append(folder)
            if not venvs:
                print("No venv is present inside the root folder.")
                return
            for venv in venvs:
                path_s = os.path.join(venv, 'scripts', 'python.exe')
                pip_cmd = [path_s, '-m', 'pip', 'install', '--upgrade', 'pip']
                execute_task(pip_cmd, "Upgrading PIP")
                freeze_command = [path_s, '-m', 'pip', 'freeze']
                print("Listing installed packages for upgrade...")
                try:
                    freeze_result = subprocess.run(freeze_command,capture_output=True,text=True,check=True)
                    packages_to_upgrade = freeze_result.stdout.strip().splitlines()
                    if not packages_to_upgrade:
                        print("No packages found in the virtual environment to upgrade.")
                        time.sleep(2)
                        continue
                    print(f"Found {len(packages_to_upgrade)} packages. Starting individual upgrades...")
                    for line in packages_to_upgrade:
                        package_name = line.split('==')[0].strip()
                        upgrade_command = [path_s, '-m', 'pip', 'install', '-U', package_name]
                        print(f"-> Upgrading {package_name}...")
                        subprocess.run(upgrade_command,capture_output=False,check=True)
                        logger.info(f"Upgrading {line} started.")
                    print("\n--- All packages in the virtual environment have been upgraded. ---")
                except subprocess.CalledProcessError as e:
                    print(f"\nUpgrade failed for a package. Check the logs.")
                    logger.error("Error encountered while upgrading package.")
                    logger.error(f"Error log: {e}")        
                except Exception as e:
                    print(f"\nAn unexpected error occurred: {e}")
                    logger.exception(f"Traceback for failed upgrade, update_venv_deps: ")
                print("All PIP packages updated.")
                print(f"Finished updating packages for {venv}")
        elif venv_to_update in os.listdir(VENV_DIR):
            print("\nUpdating pip...")
            venv_to_update = VENV_DIR / venv_to_update
            path = os.path.join(venv_to_update, 'Scripts', 'python.exe')
            pip_cmd = [path, '-m', 'pip', 'install', '--upgrade', 'pip']
            execute_task(pip_cmd, "Upgrading PIP")
            freeze_command = [path, '-m', 'pip', 'freeze']
            print("Listing installed packages for upgrade...")
            try:
                freeze_result = subprocess.run(freeze_command,capture_output=True,text=True,check=True)
                packages_to_upgrade = freeze_result.stdout.strip().splitlines()
                if not packages_to_upgrade:
                    print("No packages found in the virtual environment to upgrade.")
                    return
                print(f"Found {len(packages_to_upgrade)} packages. Starting individual upgrades...")
                for line in packages_to_upgrade:
                    package_name = line.split('==')[0].strip()
                    upgrade_command = [path, '-m', 'pip', 'install', '-U', package_name]
                    print(f"-> Upgrading {package_name}...")
                    subprocess.run(upgrade_command,capture_output=False,check=True)
                    logger.info(f"Upgrading {line} started.")
                print("\n--- All packages in the virtual environment have been upgraded. ---")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m\nUpgrade failed for a package. Check the logs.\033[0m")
                logger.error("Error encountered while upgrading package.")
                logger.error(f"Error log: {e}")       
            except Exception as e:
                print(f"\033[91m\nAn unexpected error occurred. Check the logs for details.\033[0m")
                logger.exception("Traceback for failed upgrade, update_venv_deps: ")
        else:
            print("ERROR: Venv not found.")
    
    def install_packages(self):
        venv_to_install_to = input("\033[92mEnter venv name: \033[0m")
        package_to_install = input("\n\033[92mEnter package name: \033[0m")
        venv_path = Path(input("\n\033[92mEnter venv path (leave blank if in default): \033[0m"))
        packages_to_install = package_to_install.split(" ")
        if venv_path:
            if venv_path.exists():
                print(f"{venv_path.name} exists. Parsing python libs...")
                venv_path_py_path = venv_path / "Scripts" / "python.exe"
                install_cmd = [str(venv_path_py_path), "-m", "pip", "install"] + packages_to_install
                print(f"Installing {len(packages_to_install)} packages via pip...")
                logger.info(f"Installing {len(packages_to_install)} packages via pip...")
                execute_task(install_cmd, "Package Installation")
                return
        if venv_to_install_to in os.listdir(VENV_DIR):
            venv_to_install_to = os.path.join(VENV_DIR, venv_to_install_to)
            venv_to_install_to_py_path = os.path.join(venv_to_install_to, 'scripts', 'python.exe')
            install_cmd = [venv_to_install_to_py_path, "-m", "pip", "install"] + packages_to_install
            print(f"Installing {len(packages_to_install)} packages via pip...")
            logger.info(f"Installing {len(packages_to_install)} packages via pip...")
            execute_task(install_cmd, "Package Installation")
        else:
            print("ERROR: Venv not found")
            print(f"{venv_to_install_to} not found in {VENV_DIR}")