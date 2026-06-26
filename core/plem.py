import yaml
import platform
import subprocess
import sys
import time
import ctypes
import os
import math
from utils.execute import execute_task
from utils.check import (
    is_admin, check_tool_availability, is_choco_available, 
    is_choco_package_installed, is_module_installed, is_app_installed
)

config_file = 'plem.yaml'

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{file_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

def execute_command(command, command_type="System"):
    print(f"\n--- Running {command_type} Command ---")
    
    is_list = isinstance(command, list)
    command_str = ' '.join(command) if is_list else command
    print(f"Executing: {command_str}")

    try:
        subprocess.run(command, shell=not is_list, check=True, text=True, capture_output=False)
        print(f"--- {command_type} Command Successful ---")
    except subprocess.CalledProcessError as e:
        print(f"\n!!! {command_type} Execution Failed for command: '{e.cmd}'")
        print(f"Return Code: {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"!!! Error: Command/Tool not found. Make sure system tools are installed.")
        sys.exit(1)

def get_venv_python_path(venv_name):
    if platform.system() == "Windows":
        return os.path.join(venv_name, "scripts", "python.exe")
    else:
        print("Unsupported os.")
        return
    
def create_venv():
    if not os.path.exists(venv_dir_name):
        print("Creating virtual environment...")
        execute_command([sys.executable, "-m", "venv", venv_dir_name], "Virtual Environment Creation")
    else:
        print(f"Virtual environment {venv_dir_name} already exists.")
    return get_venv_python_path(venv_dir_name)

def setup_python_dependencies(config, venv_int):
    deps = config.get('python_dependencies', {})
    required_packages = deps.get('pip_install', [])
    if not required_packages:
        print("No Python packages found for 'pip_install'. Skipping.")
        return
    packages_to_install = []
    print(f"\n Checking Python Dependencies ")
    for package_spec in required_packages:
        package_name = package_spec.split('==')[0].split('>')[0].split('<')[0]
        if is_module_installed(package_name):
            print(f"Module {package_name} is already installed. Skipping.")
        else:
            packages_to_install.append(package_spec)
    if not packages_to_install:
        print("All required Python packages are already installed.")
        return
    print(f"\n  Installing {len(packages_to_install)} Python Dependencies via pip ")
    command = [venv_int, "-m", "pip", "install"] + packages_to_install
    execute_command(command, command_type="Pip Installation")

def setup_system_tools(config):
    tools = config.get('system_tools', {})
    current_os = platform.system().lower()
    system_commands = tools.get(current_os, [])
    manager_check = {
        'windows': ('choco', 'choco -v'),
        'darwin': ('brew', 'brew --version'),
        'linux': ('snap', 'snap version') 
    }
    if current_os in manager_check:
        tool_name, check_command = manager_check[current_os]
        if not check_tool_availability(tool_name, check_command):
            print("Skipping system tool setup due to missing package manager.")
            return
    print(f"\n Installing System Tools for {current_os.capitalize()} ")
    for command in system_commands:
        should_skip = False
        if current_os == 'windows' and command.strip().lower().startswith("choco install"):
            package_part = command.split("choco install", 1)[-1].strip()
            choco_package_id = package_part.split(' ', 1)[0].strip()
            if is_choco_package_installed(choco_package_id):
                should_skip = True
        if should_skip:
            print(f"Skipping execution of: {command} (Already installed)")
        else:
            execute_command(command, command_type="System Tool Setup")
def main():
    print("="*40)
    print(f"    PLEM: Py-Lab Environment Manager    ")
    print("="*40)
    config = load_config(config_file)
    metadata = config["metadata"]
    print(f"\n- Lab Name: {metadata['lab_name']}")
    print(f"- Version: {metadata['version']}")
    print(f"- About: {metadata['description']}")
    print(f"\n {metadata['dev']}. All Rights Reserved.")
    time.sleep(2)
    print(" Checking for elevated permissions...")
    time.sleep(1)
    if is_admin():
        global venv_dir_name
        venv_dir_name = input("Enter virtual environment name: ")
        venv_python_interpreter = create_venv()
        setup_python_dependencies(config, venv_python_interpreter)
        is_choco_available()
        setup_system_tools(config)
        print("\n PLEM Setup Complete! ")
    else: 
        print("PLEM is not running as Administrator. Attempting to elevate permissions...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit(0)
if __name__ == "__main__":
    main()