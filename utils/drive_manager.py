import ctypes
import string
import shutil
from utils.logger import log_manager
from utils.execute import clear_shell
from config import SYSTEM_DRIVE
from colorama import init, Fore, Style

init(autoreset=True)
logger = log_manager.get_logger("DriveManager")

def bytes_to_gb(b):
    return round(b / (1024**3), 2)

def get_drives(include_fixed=True, include_removable=True):
    kernel32 = ctypes.windll.kernel32
    drives = []
    bitmask = kernel32.GetLogicalDrives()

    for letter in string.ascii_uppercase:
        try:
            if bitmask & 1:
                drive = f"{letter}:/"
                drive_type = kernel32.GetDriveTypeW(drive)
                if (drive_type == 2 and include_removable) or (drive_type == 3 and include_fixed):

                    volume_name = ctypes.create_unicode_buffer(1024)
                    kernel32.GetVolumeInformationW(
                        ctypes.c_wchar_p(drive),
                        volume_name,
                        1024,
                        None, None, None, None, 0
                    )

                    total, used, free = shutil.disk_usage(drive)

                    drives.append({
                        "letter": drive,
                        "name": volume_name.value or "NO_LABEL",
                        "type": "REMOVABLE" if drive_type == 2 else "FIXED",
                        "total_gb": bytes_to_gb(total),
                        "free_gb": bytes_to_gb(free),
                    })

                    logger.info(f"Detected {drives[-1]['type']} drive: {drive}")

            bitmask >>= 1
        except OSError as e:
            print(f"   {Fore.RED+Style.BRIGHT}Could not retrieve drive info. Is it locked? {Style.RESET_ALL}")
            logger.info(f"Could not open drive: {e}")
            continue

    return drives