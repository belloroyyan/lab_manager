import os
import tempfile
import shutil
from pathlib import Path
from colorama import init, Fore, Style

from utils.settings import load_settings
from utils.logger import log_manager

init(autoreset=True)
logger = log_manager.get_logger("CleanupManager")
settings = load_settings()

class CleanupManager:
    def __init__(self):
        self.ignored_folders = settings.get("BACKUP", {}).get("ignored_folders", [])
        self.temp_path = Path(tempfile.gettempdir())

    def get_folder_size(self, path: Path) -> int:
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total

    def show_top_space_consumers(self, path=None, top_n=10, bar_width=40):
        if path is None:
            path = os.environ.get('USERPROFILE', 'C:\\')
        base_path = Path(path)
        folder_sizes = []

        print(f"\nAnalyzing disk usage in: {base_path}\n")

        for folder in base_path.iterdir():
            if folder.is_dir() and folder.name not in self.ignored_folders:
                size = self.get_folder_size(folder)
                folder_sizes.append((folder, size))
        folder_sizes.sort(key=lambda x: x[1], reverse=True)
        if not folder_sizes:
            print("No folders found.")
            return
        max_size = folder_sizes[0][1]
        print(f"{'Folder':<75} {'Size (MB)':<20} {'Bar':<45} {'%'}")
        print("-" * 140)

        for folder, size in folder_sizes[:top_n]:
            size_mb = size / (1024 * 1024)
            bar_size = int((size / max_size) * bar_width)
            bar = "█" * bar_size + "░" * (bar_width - bar_size)
            percent = int((size / max_size) * 100)
            print(f"{str(folder):<75} {size_mb:>10.1f} MB  {bar}  {percent:>3}%")

    def clean_temp_files(self, confirm=True):
        if confirm:
            choice = input("Delete temporary files? (y/n): ").lower()
            if choice != 'y':
                return

        deleted, freed = 0, 0
        for item in self.temp_path.iterdir():
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    deleted += 1
                    freed += size
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    deleted += 1
            except Exception:
                continue

        print(f"Deleted {deleted} items. Freed ~{freed / (1024*1024):.2f} MB.")
        logger.info(f"Cleaned temp files: {deleted} items, {freed} bytes freed")

    def empty_recycle_bin(self, confirm=True):
        if confirm:
            choice = input("Empty Recycle Bin? (y/n): ").lower()
            if choice != 'y':
                return

        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False)
            print("Recycle Bin emptied.")
        except ImportError:
            print(f"{Fore.YELLOW}Note: winshell not installed.{Style.RESET_ALL}")

    def move_large_files_to_review(self, source_path: str, min_size_mb: int = 100, mode="move"):
        source = Path(source_path)
        if not source.exists():
            print("Specified path does not exist.")
            return
        review_folder = source / "large_files_review"
        review_folder.mkdir(exist_ok=True)

        moved = 0
        for file in source.rglob('*'):
            if file.is_file() and file.parent.name not in self.ignored_folders:
                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb >= min_size_mb:
                        destination = review_folder / file.name
                        if mode == "move":
                            shutil.move(str(file), str(destination))
                        else:
                            shutil.copy(str(file), str(destination))
                        moved += 1
                        print(f"Moved: {file.name} ({size_mb:.1f} MB)")
                except Exception:
                    continue

        print(f"\n{moved} large files moved to: {review_folder}")