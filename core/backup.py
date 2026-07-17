import os
import json
import time
import shutil
import logging
import pyzipper
from utils import settings
from utils.logger import log_manager
from pathlib import Path
from colorama import Fore, Style, init
from core.cleanup import CleanupManager

c = CleanupManager()
init(autoreset=True)
logger = log_manager.get_logger("BackupManager")

class BackupManager:
    def __init__(self, base_workspace=None, encryption_password=None):
        self.base_dir = Path(base_workspace) if base_workspace else Path(os.getcwd())
        self.staging_dir = self.base_dir / "backup_staging"
        self.password = encryption_password
        config = settings.load_settings()
        backup_settings = config.get("BACKUP", {})
        dest_raw = backup_settings.get("default_destination", "lab_manager_backups")
        self.default_dest = self.base_dir / dest_raw if not Path(dest_raw).is_absolute() else Path(dest_raw)
        self.skip_specified = backup_settings.get("skip", True)
        self.forbidden_extensions = backup_settings.get("forbidden_extensions")
        self.ignored_folders = backup_settings.get("ignored_folders")

    def run_backup(self, source_paths):
        print("--- Class-Based Backup Process Initiated ---\n")
        if self.staging_dir.exists():
            shutil.rmtree(self.staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        backup_manifest = {}
        files_copied = 0
        start_time = time.time()
        for source in source_paths:
            source_path = Path(source)
            source_size = c.get_folder_size(source_path)
            print(f"Processing {source_path} -> {round(source_size / (1024 * 1024), 1)}MB")
            if not source_path.exists():
                print(f"-> {Fore.RED}{source_path} does not exist.{Style.RESET_ALL}")
                continue
            staging_subfolder = self.staging_dir / f"Backup_{source_path.name}"
            staging_subfolder.mkdir(parents=True, exist_ok=True)
            is_venv = (source_path / "pyvenv.cfg").exists()
            backup_manifest[source_path.name] = "[VENV]" if is_venv else "[DATA_DIR]"
            backup_manifest["skipped"] = []
            backup_manifest["empty"] = []
            for file in source_path.rglob("*"):
                if (file.is_dir() or file.is_file()) and not file.stat().st_size:
                    backup_manifest["empty"].append(f"{file}")
                    continue
                if any(part in self.ignored_folders for part in file.parts) and self.skip_specified:
                    backup_manifest["skipped"].append(f"{file}")
                    continue
                if file.is_file():
                    if file.suffix.lower() in self.forbidden_extensions and self.skip_specified:
                        backup_manifest["skipped"].append(f"{file}")
                        continue
                    rel_path = file.relative_to(source_path)
                    target_file_path = staging_subfolder / rel_path
                    
                    try:
                        target_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, target_file_path)
                        files_copied += 1
                    except Exception as e:
                        logging.error(f"Copy error: {e}")
        time_taken = time.time() - start_time
        backup_manifest["op_time"] = time_taken
        if files_copied == 0:
            shutil.rmtree(self.staging_dir)
            print(f"{Fore.YELLOW}Backup operation cancelled. No files found.{Style.RESET_ALL}")
            return
        with open(self.staging_dir / 'info.json', "w") as f:
            json.dump(backup_manifest, f, indent=4)
        self.default_dest.mkdir(parents=True, exist_ok=True)
        archive_name = self.default_dest / f'lab_system_backup_{int(time.time())}.zip'
        
        if self.password:
            with pyzipper.AESZipFile(archive_name, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as z:
                z.setpassword(self.password.encode('utf-8'))
                for file in self.staging_dir.rglob('*'):
                    if file.is_file():
                        z.write(file, arcname=file.relative_to(self.staging_dir))
        else:
            shutil.make_archive(str(archive_name.with_suffix('')), "zip", self.staging_dir)
        if self._verify_backup(archive_name):
            print(f"[SUCCESS] Backup created and verified: {archive_name}")
        else:
            print("[WARNING] Backup created but verification failed!")
        shutil.rmtree(self.staging_dir)
        for i,j in backup_manifest.items():
            logger.info(f"{i} : {j}")
        print(f"[SUCCESS] Target files archived by backup instance engine.")
        print(f"\n-> Copied {files_copied} file(s) to {self.default_dest}.")
        print(f"-> Skipped {backup_manifest['empty'].__len__()} empty file(s)/directory.")
        print(f"-> Skipped {backup_manifest['skipped'].__len__()} excluded file(s)/directory.")
        print(f"-> Backup operation lasted {round(backup_manifest['op_time'], 3)} seconds.")
        print("\nCheck logs for more details.")

    def _verify_backup(self, archive_path):
        try:
            with pyzipper.AESZipFile(archive_path, 'r') as z:
                return z.testzip() is None
        except Exception:
            return False
        