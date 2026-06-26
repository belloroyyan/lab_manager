import subprocess
import os
import shutil
import time
from utils.logger import log_manager
from utils.execute import clear_shell
from config import GIT_DIR
from config import (CYAN, BOLD, GREEN, YELLOW, GRAY, RED, RESET)
from colorama import init, Fore, Style

init(autoreset=True)
magenta = Fore.MAGENTA
reset = Style.RESET_ALL
logger = log_manager.get_logger("GitHandler")

print(f"\n    {magenta}Checking for git folder...")
if not os.path.exists(GIT_DIR):
    os.mkdir(GIT_DIR)
    logger.info("Created `git_repos` folder.")
time.sleep(.5)
print(f"\n    {magenta}Found `git_repos` folder within base directory.{reset}")
print(f"    {GIT_DIR}")

class GitHandler():
    def __init__(self):
        self.bash_cmd = shutil.which('bash')

    def clone(self):
        repo_url = input(f"{GREEN}Input repository URL (separate with | for multiple): {RESET}").strip()
        if not repo_url:
            print(f"{RED}\nError: Repository URL is required. Exiting...{RESET}")
            return
        repo_urls = repo_url.split("|")
        repo_urls = [url.strip() for url in repo_urls if url.strip()]
        base_dir = GIT_DIR
        try:
            if not os.path.exists(base_dir):
                os.mkdir(base_dir)
                print(f"'{base_dir}' folder created.")
                logger.info(f"'{base_dir}' folder created.")
            else:
                print(f"'{base_dir}' folder already exists.")
            print(f'\n   Cloning into "{base_dir}" subdirectories...')
            for repo_url in repo_urls:
                repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                destination_path = os.path.join(base_dir, repo_name)
                print(f"--- Cloning {repo_url} into {destination_path} ---")
                subprocess.run(["git", "clone", "--progress",repo_url, destination_path],check=True,capture_output=True,text=True)
                logger.info(f"{repo_url} cloned into git_repos successfully.")
                print(f"--- Cloned successfully ---")
            print("\n   Git Cloning Complete.\n")
        except FileNotFoundError:
            print(f"{RED}Error: Git command not found. Make sure Git is installed and in your PATH.\n{RESET}")
            logger.error("Error: Git command not found. Make sure Git is installed and in your PATH.\n")
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error cloning git repository. Check URL or path permissions. \n{RESET}")
            print(f"{GRAY}{BOLD}Command: {e.cmd}")
            print(f"Return Code: {e.returncode}")
            print(f"Stderr (Git output): {e.stderr.strip()}{RESET}{RESET}")
            logger.error(f"Error cloning git repository. Check URL or path permissions.{e}")
        except Exception as e:
            print(f"{RED}An unexpected error occurred. Check log for details.{RESET}")
            logger.exception(f"Traceback, git_clone: {e}")
        
    def open_git_bash(self, work_dir=None):
        bash_path = r"C:\Program Files\Git\bin\bash.exe" 
        if not os.path.exists(bash_path):
            bash_path = shutil.which("bash", path=r"C:\Program Files\Git\bin")
        if bash_path and os.path.exists(bash_path):
            print("--- Entering Git Bash ---")
            subprocess.run([bash_path, "--login", "-i"], cwd=work_dir or os.getcwd())
        else:
            print("[ERROR] Git Bash bin/bash.exe not found.")