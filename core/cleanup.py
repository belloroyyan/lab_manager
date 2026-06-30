import os, tempfile, shutil
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)
from utils.logger import log_manager

logger = log_manager.get_logger("CleanupManager") #manager, handler, wrapper, they are all the same!

class CleanupManager:
    def __init__(self):
        pass
    def get_folder_size(self, path: Path) -> int:
        """Calculate total size of a folder in bytes."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total

    def show_top_space_consumers(self, path = None, top_n= 10, bar_width = 40):
        if path is None:
            path = os.environ.get('USERPROFILE', 'C:\\')
        base_path = Path(path)
        folder_sizes = []
        print(f"\nAnalyzing disk usage in: {base_path}\n")
        try:
            for folder in base_path.iterdir():
                if folder.is_dir():
                    size = self.get_folder_size(folder)
                    folder_sizes.append((folder, size))
            folder_sizes.sort(key=lambda x: x[1], reverse=True)
            print(f"{'Folder':<50} {'Size (MB)':>15}")
            print("-" * 70)
            if not folder_sizes:
                print("No folders found.")
                return
            max_size = folder_sizes[0][1]
            for folder, size in folder_sizes[:top_n]:
                size_mb = size / (1024 * 1024)
                bar_size = int((size / max_size) * bar_width)
                bar = "█" * bar_size + "░" * (bar_width - bar_size)
                print(f"{str(folder):<50} {size_mb:>12.2f} MB  {bar}  {int((size / max_size) * 100)} %")
        except Exception as e:
            print(f"Error analyzing disk: {e}")


    def suggest_cleanup(self, ):
        suggestions = [
            "1. Clean Temporary Files (%temp%)",
            "2. Empty Recycle Bin",
            "3. Remove old log files",
            "4. Move large unused files to 'Review' folder",
            "5. Clean old student project folders (older than X days)"
        ]

        print("\n=== Cleanup Suggestions ===")
        for suggestion in suggestions:
            print(suggestion)

    def clean_temp_files(self, ):
        temp_path = Path(tempfile.gettempdir())
        deleted = 0
        freed = 0

        print(f"\nCleaning temporary files in: {temp_path}")
        for item in temp_path.iterdir():
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

        print(f"Deleted {deleted} items. Freed approximately {freed / (1024*1024):.2f} MB.")

    def empty_recycle_bin(self, ):
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            print("Recycle Bin emptied successfully.")
        except ImportError:
            print(f"{Fore.YELLOW}Note: 'winshell' package not installed. Recycle Bin not emptied.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Could not empty Recycle Bin.{Style.RESET_ALL}")
            logger.error(f"Failed to empty bin: {e}")

    def move_large_files_to_review(self, source_path: str, min_size_mb: int = 100):
        source = Path(source_path)
        review_folder = source / "large_files_review"
        review_folder.mkdir(exist_ok=True)
        moved = 0
        mode = input("mode (move/copy): ").strip().lower()
        for file in source.rglob('*'):
            if file.is_file():
                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb >= min_size_mb:
                        destination = review_folder / file.name
                        if mode == "move":
                            shutil.move(str(file), str(destination))
                        else: shutil.copy(str(file), str(destination))
                        moved += 1
                        print(f"-> Moved: {file.name} ({size_mb:.1f} MB)")
                except Exception:
                    continue
        print(f"\nMoved {moved} large files to: {review_folder}")