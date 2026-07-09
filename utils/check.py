from utils.logger import log_manager
from config import PROJECT_ROOT
import subprocess
import time
import sys
import ctypes
import shutil
import requests
import os
from pathlib import Path

PROJECT_ROOT = Path(PROJECT_ROOT)

logger = log_manager.get_logger("CheckWrapper")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_choco_available():
    print("\nChecking if Chocolatey was pre-installed...")
    time.sleep(1.5)
    try:
            result = subprocess.run(['choco', '-v'], capture_output=True,text=True,check=True)
            print('Chocolatey is Installed.')
    except FileNotFoundError:
        print("Chocolatey is not Installed.")
        install_choco = input('Proceed with Chocolatey installation? (y/n): ')
        powershell_command = (
            "Set-ExecutionPolicy Bypass -Scope Process -Force;"
            "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        )
        if install_choco == "y":
            try:
                command_to_run = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', powershell_command]
                print("Executing Chocolatey installation command...")
                result = subprocess.run(command_to_run,capture_output=True,text=True,check=True)
                print("---Command Output---")
                print(result.stdout)
                print("\n  Re-run PLEM script as chocolatey was just installed.")
                print("---Execution Complete---")
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                print(f"Error during command execution (Exit Code {e.returncode}):")
                print(f"STDOUT: {e.stdout}")
                print(f"STDERR: {e.stderr}")
            except FileNotFoundError:
                print("Error: powershell.exe not found.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else: 
            print("Exiting PLEM script with exit code 2.")
            sys.exit(0)

def check_tool_availability(tool_name, command_to_check):
    print(f"\nChecking for required package manager: {tool_name}...")
    try:
        subprocess.run(command_to_check, shell=True, check=True, capture_output=True,text=True)
        print(f"Tool {tool_name} is installed and available.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Tool {tool_name} is NOT found.")
        print(f"Please install {tool_name} or remove this dependency from the YAML file.")
        return False

def is_choco_package_installed(package_name):
    print(f"Checking Chocolatey for package: {package_name}...")
    try:
        result = subprocess.run(
            ['choco', 'list', package_name],
            capture_output=True,
            text=True,
            check=False 
        )
        if result.returncode != 0:
            print(f"Error running 'choco list': {result.stderr.strip()}")
            return False
        target_entry = f"{package_name}"
        for line in result.stdout.splitlines():
            if line.strip().lower().startswith(target_entry.lower()):
                print(f"Package '{package_name}' found in Chocolatey local list.")
                return True
        print(f"Package '{package_name}' not found in Chocolatey local list.")
        return False
    except FileNotFoundError:
        print("Error: 'choco' command not found. Cannot check package status.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while checking Chocolatey: {e}")
        return False

def is_module_installed(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def is_app_installed(app_package_id):
    return is_choco_package_installed(app_package_id)

def find_system_python():
    system_python_path = shutil.which("python")
    if system_python_path:
        if sys.executable.lower() not in system_python_path.lower():
            return system_python_path
    system_python_path = shutil.which("py")
    if system_python_path:
        return system_python_path
    return None

def check_address_health(url, max_timeout):
    start_time = time.time()
    logger.info(f"Starting ping requests. [{start_time}]")
    result = {
        'url':url,
        'success':False,
        'status_code': None,
        'message': 'An unknown error has occurred',
        'time_ms': None
    }
    try:
        response = requests.get(url, timeout=max_timeout)
        response.raise_for_status()
        result['status_code'] = response.status_code
        result['success'] = True
        result['message'] = f'OK. Address is up and running, responded with status code {response.status_code}'
    except requests.exceptions.RequestException as e:
        logger.error(f"CONNECTION ERROR while trying to connect to {url}")
        result['status_code'] = "CONN_ERROR"
        result['message'] = f"Connection error: {type(e).__name__} - Details: {str(e)}"
    except requests.exceptions.HTTPError as e:
        logger.error(f"{e.response.status_code} returned by {url}")
        result["status_code"] = e.response.status_code
        result["message"] = f"HTTP Failure: Address returned {e.response.status_code}"
    except requests.exceptions.Timeout:
        logger.error(f"Max timeout exceeded.")
        result["status_code"] = "TIMEOUT"
        result["message"] = f"Request timed out after {max_timeout}"
    finally:
        end_time = time.time()
        result["time_ms"] = round((end_time - start_time) * 1000, 2)
        logger.info(f"Ending ping requests. [{end_time}]")
    return result            