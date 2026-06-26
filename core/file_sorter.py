from pathlib import Path
import shutil
from utils.logger import log_manager
from utils.progress_bar import progress_bar
from utils.settings import load_settings
from config import YELLOW, RESET
import signal
import re
import time

logger = log_manager.get_logger("FileSorter")

class FileSorter:
    def __init__(self, root_path, mode="move"):
        self.root = Path(root_path)
        self.mode = mode
        self.cancelled = False

        config = load_settings()
        self.exts : dict = config["BACKUP"]["extensions"]

        signal.signal(signal.SIGINT, self._handle_cancel)

    def _handle_cancel(self, signum, frame):
        self.cancelled = True
        print(f"\n{YELLOW}Sorting cancelled by user...{RESET}")
        logger.warning("Sorting cancelled by user")

    def _get_category(self, file):
        for cat, ext in self.exts.items():
            if file.suffix.lower() in ext:
                return cat
        return "Others"

    def scan_files(self):
        return [f for f in self.root.glob("*")]
    
    def filter_seen(self, path_list : list, keyword):
        for item in path_list:
            if keyword in item.name:
                path_list.pop(path_list[keyword])

    def sort(self):
        files = self.scan_files()
        total = len(files)
        moved = 0
        folder = f"Downloads-{time.ctime().replace(" ", "-").replace(":", "-")}" if self.root.suffix.lower() == "downloads" else "Sorted"
        if total == 0:
            print("No files found to sort.")
            logger.info("No files found to sort.")
            return
        logger.info(f"Sorting started: {total} files found")
        print(f"Sorting {total} files in '{self.root}' using mode '{self.mode}'")
        for i, file in enumerate(files, start=1):
            if self.cancelled:
                logger.warning(f"Sorting cancelled after {i-1}/{total} files.")
                print(f"\n{YELLOW}Sorting stopped after {i-1}/{total} files.{RESET}")
                break
            cat = self._get_category(file)
            if "download" in file.suffix.lower():
                cat = "Uncompleted Downloads"
            elif file.is_dir():
                cat = "Directories"
            dest = self.root / folder / cat
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / file.name

            try:
                if self.mode == "copy":
                    shutil.copy2(file, target)
                    logger.info(f"Copying {file} to {dest} with metadata.")
                else:
                    shutil.move(file, target)
                    logger.info(f"Moving {file} to {dest} with metadata.")
            except Exception as e:
                logger.error(f"Failed to process {file}: {e}")

            progress_bar(i, total, extra=f"Processing: {file.name}")
            moved += 1
        if not self.cancelled:
            logger.info("Sorting finished")
            return({
                "total" : total,
                "moved" : moved
            })
    def sort_repeat(self):
        base_path = Path(self.root)
        if not base_path.exists() or not base_path.is_dir():
            print("[ERROR] Invalid target media directory path.")
            return
        series_pattern = re.compile(r"^(.*?)(?:(?:[sS]\d{1,2})?[eE]\d{1,2}|\d{1,2}x\d{1,2})")
        sorting_matrix = {}
        vid_exts = self.exts.get("Videos")
        sub_exts = self.exts.get("Subtitles")
        print(f"Skimming surface layout of: {base_path.name}\n")
        sorting_matrix["Non-series"] = []
        for file in base_path.iterdir():
            if file.is_file() and ((file.suffix in vid_exts or file.name.split(".")[-1] in vid_exts) or file.suffix in sub_exts):
                match = series_pattern.match(file.name)
                if match:
                    raw_title = match.group(1)
                    clean_title = raw_title.replace(".", " ").replace("_", " ").strip()
                    clean_title = clean_title.rstrip("-").strip()
                    clean_title = clean_title.title()
                    if clean_title not in sorting_matrix:
                        sorting_matrix[clean_title] = []
                    sorting_matrix[clean_title].append(file)
                else:
                    sorting_matrix["Non-series"].append(file)
                    print(f"  [-] Appending non-series media file: {file.name}")
            elif file.is_dir():
                print(f"  [-] Skipping file directory: {file.name}")
            else:
                print(f"  [-] Skipping non-series/unrecognized media file extension: {file.name}")

        print(f"\n  Analysis complete. Found {len(sorting_matrix)} distinct series profiles.")
        for show_name, file_list in sorting_matrix.items():
            show_folder = base_path / show_name
            show_folder.mkdir(parents=True, exist_ok=True)
            print(f"\nMoving files for series: {show_name}")
            total = len(file_list)
            for i, file in enumerate(file_list, start=1):
                if self.cancelled:
                    logger.warning(f"Sorting cancelled after {i-1}/{total} files.")
                    print(f"\n{YELLOW}Sorting stopped after {i-1}/{total} files.{RESET}")
                    break
                destination_path = show_folder / file.name
                try:
                    shutil.move(str(file), str(destination_path))
                except Exception as e:
                    print(f"  [ERROR] Could not relocate file {file.name}: {e}")
                progress_bar(i, total, extra=f"Processing: {file.name}")
                
            print(f"Successfully grouped {show_name}")
        print("\nMedia sorting sequence complete.")
        logger.info("[SUCCESS] Media surface organizational routing sequence complete.")
