from utils.logger import log_manager
from colorama import init, Fore, Style

init(autoreset=True)
magenta = Fore.MAGENTA
green = Fore.GREEN
reset = Style.RESET_ALL

readme = """>> LAB MANAGER - HOW TO USE (EXE VERSION)
==============================================================================

This guide covers running Lab Manager as the packaged main.exe file.
No Python install is needed on machines running the exe.

>> 1. BEFORE YOU START
------------------------------------------------------------------------------
  - Windows only.
  - Some features (firewall rules, elevated shell, remote shutdown/restart)
    work best if you run main.exe as Administrator.
    (Right-click main.exe -> Run as administrator)
  - Unsigned exe: Windows SmartScreen or your antivirus may flag it on first
    run. Choose "More info -> Run anyway" if you trust the build.
  - Keep main.exe and settings.json in the same folder. The app creates
    logs/, reports/, venvs/, help/, git_repos/, and lab_manager_backups/
    right next to the exe.

>> 2. FIRST LAUNCH
------------------------------------------------------------------------------
  1. Double-click main.exe.
  2. A console window titled "Lab Manager Session" opens.
  3. On first run the app will:
       - Create a default settings.json next to the exe.
       - Play a short boot sequence.
       - Create logs/, reports/, venvs/, and help/ folders.
  4. You land on the Main Menu:

      [1] Configure New PC / Install Software
      [2] Storage Operations
      [3] Backup Operations
      [4] Clone Git Repository
      [5] Virtual Environment
      [6] Run Network Tests and Commands
      [7] System Checks and Health
      [8] Cleanup Operations
      [9] I/O

      [L] Logs
      [S] Settings
      [H] Read Help Manual

      [0] Exit Application

  Type a number or letter, press ENTER. Press ENTER again after an action
  to return to this menu.

  NOTE: Option [7] does not currently respond in this build.
  Use [9] I/O -> [3] Run Inventory Check Across LAN instead.

>> 3. SETTING UP MANAGED LAB PCs (THE "AGENT")
------------------------------------------------------------------------------
  Lab Manager runs in two roles from the same exe:

    - ADMIN CONSOLE : the menu above, run on your own machine.
    - AGENT         : runs quietly on each lab PC you want to monitor
                      or control remotely.

  To turn a lab PC into an agent:
    1. Copy main.exe to that PC.
    2. From the Main Menu: [6] Run Network Tests and Commands
                            -> [5] Start Listener
    3. Leave the window running. It listens on UDP port 8088 by default
       and responds to commands sent from your admin console.
    4. If the firewall blocks it, allow the rule when prompted, or run
       the app as Administrator so it can add the rule automatically.

  Repeat this on every lab PC you want visible to the admin console.

>> 4. NETWORK OPERATIONS  [6]
------------------------------------------------------------------------------
  [1] Scan Local Area Network
        Pings every device on your subnet, resolves hostnames, and
        saves discovered devices (with a guessed listener port).
  [2] Broadcast Message
        "all"      -> message every discovered device
        "selected" -> message one IP directly
  [3] Change Default Listening Port
        Updates the port the admin console expects agents to be on.
  [4] Retrieved Stored Records
        Lists every device saved from past scans.
  [5] Start Listener
        Turns THIS machine into an agent. See Section 3.

>> 5. SYSTEM HEALTH & I/O  [9]
------------------------------------------------------------------------------
  [1] Open Shell Access
        Drops into a raw cmd.exe window. Type "exit" to return.
  [2] Run Inventory Check
        Checks THIS machine for required software (Python, Git, VS Code)
        and prints a compliance summary.
  [3] Run Inventory Check Across LAN
        Scans the network, asks every discovered device to report its
        hardware/OS health, and prints a color-coded report:
          GREEN = healthy   YELLOW = warning   RED = critical
        You'll be asked afterward whether to generate a PDF report.
  [5] Kill Listener Port
        Frees up port 8088 if it's stuck in use.

>> 6. STORAGE OPERATIONS  [2]
------------------------------------------------------------------------------
  1. Choose a drive, or enter a custom path.
  2. Choose move or copy.
  3. Choose a sort type:
       Rule-Based Sort   -> groups files into folders (Images, Documents,
                             Code, etc.) by extension.
       Auto-Group Shows  -> groups video/subtitle files into per-series
                             folders by detecting season/episode patterns
                             in filenames.

>> 7. BACKUP OPERATIONS  [3]
------------------------------------------------------------------------------
  1. Enter one or more source paths (space-separated), or leave blank to
     use the default sources from Settings.
  2. Optionally set a password to AES-encrypt the resulting zip.
  3. Output goes to lab_manager_backups/ as
     lab_system_backup_<timestamp>.zip

  Skipped automatically:
    - empty files/folders
    - ignored folders (.git, node_modules, venv, etc.)
    - forbidden extensions (.exe, .dll, .bat, etc.)

>> 8. GIT OPERATIONS  [4]
------------------------------------------------------------------------------
  Requires Git installed and on PATH.
  [1] Clone Git Repository
        Enter one or more URLs separated by "|" to clone them all into
        a git_repos/ folder.
  [2] Open Git Bash
        Opens Git Bash directly, if installed.

>> 9. VIRTUAL ENVIRONMENTS  [5]
------------------------------------------------------------------------------
  [1] Create Virtual Environment
        Builds a new venv, moves it to a chosen destination (or the
        default from Settings).
  [2] Update Venv Packages
        Upgrades pip and every installed package, for one venv or all.
  [3] Install Packages
        Installs named package(s) into a chosen venv.

>> 10. CLEANUP OPERATIONS  [8]
------------------------------------------------------------------------------
  [1] Show Top Space Consumers
        Ranks the largest top-level folders under a path with a bar chart.
  [2] Clean Temporary Files
        Empties the OS temp folder.
  [3] Empty Recycle Bin
        Requires the optional "winshell" library.
  [4] Move Large Files to Review Folder
        Moves files above a size threshold into large_files_review/.

>> 11. LOGS  [L]
------------------------------------------------------------------------------
  Shows a summary of log entries by severity (errors, warnings, etc.),
  then lets you view recent history or clear the log file.

>> 12. SETTINGS  [S]
------------------------------------------------------------------------------
  Displays every current setting.
    "edit"  -> then enter a SECTION (e.g. NETWORK) and a KEY
               (e.g. default_port) to change one value.
    "R"     -> restore all settings to their defaults.

>> 13. HELP MANUAL  [H]
------------------------------------------------------------------------------
  Displays this file (help/readme.txt). Lines starting with ">>" are
  shown as highlighted headers.

>> 14. EXITING
------------------------------------------------------------------------------
  Choose [0] Exit Application, or press CTRL+C to force-quit.
  A forceful exit is logged before the app closes.

>> 15. TROUBLESHOOTING
------------------------------------------------------------------------------
  Option [7] does nothing
      -> Known gap in menu routing. Use [9] -> [3] instead.

  "Port already in use" starting the listener
      -> Another instance is already listening.
         Use [9] I/O -> [5] Kill Listener Port, then retry.

  Firewall blocks the listener
      -> Run main.exe as Administrator, or manually allow UDP port 8088.

  No devices found during a LAN scan
      -> Confirm you're on the same subnet as target PCs, and that their
         local firewalls aren't blocking ICMP ping.

  Backup says "No files found"
      -> Every file in the source path was empty, ignored, or on the
         forbidden-extensions list. Check settings.json -> BACKUP.

  "winshell not installed" on Empty Recycle Bin
      -> Optional library not bundled in this build. Safe to ignore.

  App won't start / SmartScreen warning
      -> Expected for an unsigned exe. Click "More info -> Run anyway",
         or allow it through your antivirus.

==============================================================================
                         END OF LAB MANAGER MANUAL
=============================================================================="""
def display_help():
    print(f"\n{green}{Style.BRIGHT}Lab Manager Help Manual\n{readme}\n{reset}")