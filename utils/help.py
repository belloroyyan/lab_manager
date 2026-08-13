from utils.logger import log_manager
from colorama import init, Fore, Style

init(autoreset=True)
magenta = Fore.MAGENTA
green = Fore.GREEN
reset = Style.RESET_ALL

readme = """Lab Manager — Help Manual (v2.1.4)
===============================================================================

Short summary
------------
Lab Manager is a Windows-oriented (works on other platforms where noted) console tool that provides:
- A menu-driven admin console for common lab-management tasks.
- A lightweight "agent" mode (listener) that can run on lab PCs and respond to UDP commands.
- Utilities for backups (including AES-encrypted zips), file sorting, venv management, LAN inventory, system health checks, Git operations, and cleanup tasks.
Defaults and important paths:
- Default listening port: 8088
- Desktop workspace for outputs and stores: <User Desktop>\\Lab Manager (DESKTOP_DIR)
- Default venvs folder: <User Desktop>\\Lab Manager\\venvs (VENV_DIR)
- Backups: <User Desktop>\\Lab Manager\\lab_manager_backups (BACKUP_DIR)
- Reports: <User Desktop>\\Lab Manager\\reports (REPORT_DIR)
- App version: 2.1.4

Quick start — first run
-----------------------
1. Copy the files or run main.py (or run packaged EXE if provided).
2. On first run the app will create settings.json and the folders: logs/, reports/, venvs/, help/, git_repos/, lab_manager_backups/ (next to the project /exe location or under DESKTOP_DIR where relevant).
3. Main Menu is presented. Type a number (or letter) and press Enter.

Main menu (what each option does)
---------------------------------
Top-level menu (mapped to ui/menu.py display_dashboard):
  [1] Configure New PC / Install Software
      - Placeholder for "PLEM" module (separate tool) — instruction directs you to run plem.bat in PLEM directory.
  [2] Storage Operations
      - FileSorter: sort files in a chosen directory or drive.
      - Two sorting modes:
        * Rule-Based Sort: group files by extension into categories defined in settings (Images, Documents, Code, Videos, etc.).
        * Auto-Group Shows: detect series patterns (S01E01, 1x01, etc.) and group video/subtitle files into per-series folders.
      - Choose move or copy mode.
  [3] Backup Operations
      - BackupManager: archive specified source paths into a timestamped ZIP under lab_manager_backups.
      - Can AES-encrypt the resulting zip when a password is provided.
      - Skips empty files, ignored folders (from settings BACKUP.ignored_folders), and forbidden extensions.
      - Manifest file (info.json) written to staging area while creating backup.
  [4] Clone Git Repository
      - Uses git clone to clone single or multiple repos (enter URLs separated by |) into DESKTOP_DIR\\git_repos.
      - Opens Git Bash when requested (if installed).
  [5] Virtual Environment
      - Create venv(s), update packages in a venv (or all venvs), install packages into a venv, and list installed packages.
      - Uses system Python to create virtual environments; moves created venvs to the configured VENV_DIR.
  [6] Run Network Tests and Commands
      - Scan LAN: pings your subnet, attempts to resolve hostnames (nbtstat fallback on Windows) and records reachable devices.
      - Broadcast Message: send an encrypted UDP message to discovered devices (encrypt_message from utils.identity is used).
      - Change default listening port (NetworkHandler.change_default_port saves to settings).
      - Retrieve saved records (database of devices).
      - Start Listener: turns this machine into an agent that listens on UDP (default port 8088).
  [7] System Checks and Health
      - Environment status check: verifies Python, Git, is_admin, scans specified directories for venvs, and reports installed packages for venvs.
      - System scans: optionally runs sfc /scannow and DISM checks (Windows, requires admin).
  [8] Cleanup Operations
      - Show top space consumers (ranks top-level folders with a simple bar chart).
      - Clean temporary files (empties OS temp folder).
      - Empty recycle bin (uses winshell if installed).
      - Move large files to a review folder (files >= threshold moved or copied to large_files_review).
  [9] I/O
      - Open shell access (drops to cmd.exe on Windows).
      - Run Inventory check (checks required software on THIS machine).
      - Run Inventory check across LAN (collect telemetry from other agents and optionally produce a PDF report).
      - Generate secret key (utils.identity.generate_and_export_key) and import an existing key.
      - Start/Stop listener related utilities and kill listener port.
  [L] Logs
      - View log summary, analyze recent history, clear logs.
  [S] Settings
      - View all settings.json contents.
      - Edit specific setting by saying "edit", choosing SECTION and KEY (supports booleans, ints with min/max, lists, and strings).
      - Restore to defaults (init_settings).
  [U] Check For Updates
      - check_and_update utility (may query GitHub repository configured in config.py).
  [H] Read Help Manual
      - Prints the help manual text (this file).
  [0] Exit Application
      - Graceful exit; CTRL+C triggers a forceful exit path that is logged.

How to run as admin / elevated operations
-----------------------------------------
- Some features (adding firewall rules, running DISM/sfc, listening on privileged ports if chosen) require elevated privileges.
- main.py checks is_admin on startup and will relaunch as administrator if necessary when _STANDALONE or specific actions require elevation.
- To run as admin manually: right-click packaged EXE -> "Run as administrator".
- If the app needs elevation it will attempt to relaunch itself with ShellExecuteW (Windows).

Agent mode (listener)
---------------------
- Start a listener from UI: [6] Run Network Tests and Commands -> [5] Start Listener (uses utils.listener.start_listener/initiate_listener).
- A running agent listens for encrypted UDP messages on the configured port and responds to inventory/health queries.
- If you see "port already in use", use I/O -> Kill Listener Port to free the port or check for another instance.

Backup: details and options
---------------------------
- BackupManager accepts a list of source paths (space-separated) or uses default sources from settings.
- By passing a password the created archive will be AES-encrypted (pyzipper).
- Output filename format: lab_system_backup_<timestamp>.zip in DESKTOP_DIR\\lab_manager_backups by default.
- The staging folder is created under the working directory (backup_staging) while assembling files then zipped and removed.
- When no files are copied (e.g. all files ignored), backup cancels and staging area deleted.

File sorting (Storage Operations)
--------------------------------
- FileSorter sorts entries in a target folder (uses settings BACKUP.extensions map).
- Two modes:
  - Rule-based: categories determined by extension lists in settings.
  - Auto-group shows: attempts to detect series names and group episodes into folders.
- Interrupt with CTRL+C to cancel; sorting reports progress.

Virtual environments (VENV)
---------------------------
- Create: system Python (find_system_python) used to create a venv, then moved to the chosen destination or VENV_DIR.
- Update: upgrade pip and loop over pip freeze to upgrade packages one-by-one (can be long).
- Install: install packages into a named venv.
- List: pip freeze output printed.

Inventory & Health checks
-------------------------
- gen_soft_report(): checks for configured software (settings.SOFTWARE_CHECKS), prints versions when possible, and returns a compliance report.
- generate_lan_system_report(): sends LAB|INFO broadcast, waits for agent responses, parses device telemetry and prints color-coded health summary (green/yellow/red) and offers to create a PDF via utils.report.create_lab_report.
- print_clean_report() is used internally to produce readable per-node health summaries and detect issues.

Network scanning and messaging
------------------------------
- scan_entire_lan(): enumerates .1..254 on your subnet and pings each address concurrently; records devices found.
- get_hostname(): uses reverse DNS and nbtstat fallback on Windows.
- broadcast_message/broadcast_msg: encrypts messages (utils.identity.encrypt_message) and uses UDP to send bytes to a port (default 8088).
- sendmsg: uses persisted port from local DB if available.
- change_default_port: updates NETWORK.default_port in settings.json and saves.

Settings
--------
- settings.json (PROJECT_ROOT\\settings.json) contains the configuration for BACKUP, NETWORK, HEALTH, LISTENER, and extension categories used by FileSorter.
- Use Settings menu [S], then "edit" to change a SECTION and KEY interactively.
- "R" in Settings restores defaults via init_settings().

Logging
-------
- Logs are created and managed by utils.logger (log_manager). There are menu options to show summaries, view history, and clear logs.
- Check logs/ (in project root or next to exe) for detailed entries.

Reports & PDFs
--------------
- Inventory and LAN reports can be converted to a PDF via utils.report.create_lab_report (the UI prompts after a LAN inventory or when generating from saved data).
- Reports are stored in DESKTOP_DIR\\reports by default.

Identity, encryption, and secrets
---------------------------------
- Symmetric secret for agent messaging is stored in IDENTITY_FILE.
- Use I/O -> Generate Secret Key to create and export a key; or import an existing key with the Import option.
- If the secret is not present/valid, network broadcasting and encryption will fail with a warning.

Common troubleshooting
----------------------
- "Port already in use" starting the listener:
  -> Another instance is likely running. Use I/O -> Kill Listener Port or inspect processes.
- Firewall blocks listener:
  -> Run as Administrator so the app can add a rule, or allow UDP port 8088 manually.
- No devices found during a LAN scan:
  -> Ensure you're on the same subnet. Confirm remote PCs are running the agent listener and not blocking ICMP or UDP.
- Backup says "No files found":
  -> Files were empty, excluded by ignored_folders, or matched forbidden_extensions. Check settings.json -> BACKUP.
- "winshell not installed" when emptying recycle bin:
  -> winshell is optional. Install it via pip if required or skip that operation.

Developer notes and internals (concise)
---------------------------------------
- main.py: boot logic, creates DESKTOP_DIR and IDENTITY_DIR if missing, sets console title, hides identity file, sets up logging, and launches display_menu().
- config.py: central constants and path definitions; get_project_root determines standalone (frozen exe) behavior.
- core/ contains task modules: backup.py, cleanup.py, file_sorter.py, git.py, health.py, inventory.py, network.py, venv.py.
- ui/ contains menus and handler functions that wire user choices to core utilities.
- utils/ contains helpers: settings, logger, identity, database, report generation, listener, shell helpers, update checker, and the current help text (utils/help.py).
- Network encryption uses utils.identity.encrypt_message and a secret stored in IDENTITY_FILE.

Safety and permissions
----------------------
- Some operations (DISM, sfc, adding firewall rules) require admin rights and the app attempts to relaunch with admin elevation when needed on Windows.
- The app writes to user Desktop and ProgramData locations; ensure the account has write permissions there.

Where files are created (typical on Windows)
-------------------------------------------
- Desktop workspace: C:\\Users\\<you>\\Desktop\\Lab Manager\\
  - venvs\\
  - git_repos\\
  - lab_manager_backups\\
  - reports\\
- Application root logs/: for runtime logs
- settings.json: in project root (or next to exe)

Notes about changes from previous manual
---------------------------------------
- This manual reflects current code behavior (v2.1.4), including:
  - Explicit AES zip encryption support in BackupManager using pyzipper when a password is given.
  - LAN scanning/playback behavior and the default UDP port 8088.
  - The venv handler moves created venvs to the selected destination.
  - FileSorter supports both a rule-based and a series auto-grouping approach.
  - Health checks gather venv package lists and optionally call DISM / sfc (Windows admin-required)."""

def display_help():
    print(f"\n{green}{Style.BRIGHT}{readme}\n{reset}")