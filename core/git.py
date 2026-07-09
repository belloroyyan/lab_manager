import subprocess
import os
import shutil
from utils.logger import log_manager
from config import (GREEN, RED, RESET, GIT_DIR)
from colorama import Fore, Style

logger = log_manager.get_logger("GitHandler")
reset = Style.RESET_ALL

class GitHandler:
    def __init__(self):
        self.git_bash = self._find_git_bash()

    def _find_git_bash(self):
        possible_paths = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
            shutil.which("bash")
        ]
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None

    def pull(self, repo_path):
        try:
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
            print(f"{Fore.GREEN}Updated: {repo_path}{reset}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Failed to pull {repo_path}: {e}{reset}")

    def open_git_bash(self, work_dir=None):
        if not self.git_bash:
            print(f"{Fore.RED}Git Bash not found.{reset}")
            return
        subprocess.run([self.git_bash, "--login", "-i"], cwd=work_dir or os.getcwd())
        
    def clone(self):
        repo_url = input(f"\n{GREEN}Input repository URL (separate with | for multiple): {RESET}").strip()
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
        except Exception as e:
            print(f"Could not create git_repos folder.")
            logger.error(f"Could not make git_repos dir: {e}")

        print(f'\n   Cloning into "{base_dir}" subdirectories...\n')
        for repo_url in repo_urls:
            try:
                repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                destination_path = os.path.join(base_dir, repo_name)
                print(f"--- Cloning {repo_url} into {destination_path} ---")
                subprocess.run(["git", "clone", "--progress",repo_url, destination_path],check=True,capture_output=True,text=True)
                logger.info(f"{repo_url} cloned into git_repos successfully.")
                print(f"--- Cloned successfully ---")
            except FileNotFoundError:
                print(f"{RED}Error: Git command not found. Make sure Git is installed and in your PATH.\n{RESET}")
                logger.error("Error: Git command not found. Make sure Git is installed and in your PATH.\n")
            except subprocess.CalledProcessError as e:
                print(f"{RED}Error cloning git repository. Check URL or path permissions. \n{RESET}")
                logger.error(f"Error cloning git repository. Check URL or path permissions.{e}")
                logger.error(f"Command: {e.cmd}")
                logger.error(f"Return Code: {e.returncode}")
                logger.error(f"Stderr (Git output): {e.stderr.strip()}")
            except Exception as e:
                print(f"{RED}An unexpected error occurred. Check log for details.{RESET}")
                logger.exception(f"Traceback, git_clone: {e}")
        print("\n   Git Cloning Complete.")