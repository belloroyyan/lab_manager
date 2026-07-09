# Lab Manager

A Windows console application for administering a shared/networked computer lab (default label: **"UNIOSUN FOCIT Lab"**). It centralizes the tasks an IT admin normally does by hand — setting up new PCs, scanning the LAN, pushing messages/commands to lab machines, backing up data, managing Python virtual environments, cleaning disk space, and generating inventory/health reports — behind a single menu-driven CLI.

The project has two operating "roles" that run the same codebase:

- **Console / Admin instance** — the interactive menu (`main.py`) an administrator runs to manage the lab.
- **Agent instance** — `listener.py`, run on individual lab PCs, which listens for commands broadcast from the admin console and reports back system telemetry.

---

## Table of Contents

- [Architecture](#architecture)
- [Feature Overview](#feature-overview)
- [Module Reference](#module-reference)
  - [Entry Point](#entry-point)
  - [`ui/` — Menu & Input Handling](#ui--menu--input-handling)
  - [`core/` — Feature Engines](#core--feature-engines)
  - [`utils/` — Shared Services](#utils--shared-services)
- [Configuration](#configuration)
- [Data Storage](#data-storage)
- [Setup](#setup)
- [Usage](#usage)
- [Known Issues](#known-issues)
- [Security Notes](#security-notes)

---

## Architecture

```
lab_manager/
├── core/                   # Feature engines (business logic)
│   ├── backup.py           # Encrypted, filtered backup/archival engine
│   ├── cleanup.py          # Disk usage analysis & cleanup engine
│   ├── file_sorter.py      # File/media sorting engine
│   ├── git.py              # Git clone / Git Bash automation
│   ├── inventory.py        # Software + LAN hardware inventory & reporting
│   ├── network.py          # LAN scanning & UDP messaging engine
│   └── venv.py             # Virtual environment lifecycle manager
│
├── ui/
│   ├── menu.py              # Main dashboard loop
│   └── handler.py           # Routes menu choices to core/utils logic
│
├── utils/                   # Shared low-level services
│   ├── check.py             # Environment/tool availability checks
│   ├── database.py          # SQLite device registry
│   ├── drive_manager.py     # Physical drive enumeration
│   ├── execute.py           # Subprocess execution wrapper
│   ├── report.py            # PDF report generator (fpdf)
│   ├── help.py              # In-app help/manual viewer
│   ├── listener.py          # UDP agent — runs on lab PCs
│   ├── logger.py            # Central logging + log analysis
│   ├── progress_bar.py      # CLI progress bar
│   ├── settings.py          # settings.json load/save/edit
│   └── shell.py             # Elevated shell + process/port killer
│
├── config.py                 # Paths, colors, admin/firewall helpers
├── main.py                   # Application bootstrapper
├── settings.json              # Runtime configuration (auto-generated)
└── lab_manager.db              # SQLite device registry (auto-generated)
```

At startup, several modules (`database.py`, `help.py`, `venv.py`, `inventory.py`) automatically create their required folders (`logs/`, `help/`, `venvs/`, `reports/`) and files under the project root the first time they're imported.

---

## Feature Overview

| Category | What it does |
|---|---|
| **PC Setup** | Placeholder hook into an external "PLEM" tool for provisioning new machines. |
| **Storage Operations** | Sorts loose files into categorized folders by extension, or groups TV episodes into per-show folders using regex pattern matching on filenames. |
| **Backup** | Archives one or more source paths into a password-protected (AES) ZIP, excluding empty files, ignored folders, and forbidden extensions; verifies the archive afterward. |
| **Git Operations** | Bulk-clones one or more repositories into a `git_repos/` folder; can also drop into a Git Bash shell. |
| **Virtual Environments** | Creates, moves, and manages Python venvs; can bulk-upgrade every installed package in one or all venvs; installs arbitrary packages into a chosen venv. |
| **Network** | Multi-threaded ping sweep of the local subnet, hostname resolution, UDP broadcast messaging to all/selected devices, port scanning + SQLite persistence of discovered devices, and starting the listener agent. |
| **System Checks / Inventory** | Verifies required software (Python, Git, VS Code, etc.) is installed and reports versions; can query every online LAN device for hardware/OS telemetry and assemble a lab-wide health report. |
| **Cleanup** | Reports the largest folders under a path, purges the temp directory, empties the Recycle Bin, and relocates oversized files into a review folder. |
| **I/O** | Opens an elevated system shell, runs local or LAN-wide inventory checks, prints saved inventory data, and can force-kill the listener port. |
| **Logs** | Summarizes and colorizes recent log activity by severity, or wipes the log file. |
| **Settings** | View and interactively edit any setting (strings, numbers, booleans, lists) in `settings.json`, or reset to defaults. |
| **Reporting** | Generates a styled multi-section PDF ("FOCIT Lab Manager Central Report") summarizing fleet status, critical flags, and per-device hardware/storage detail. |

---

## Module Reference

### Entry Point

**`main.py`**
Sets the console window title, initializes logging, and launches `display_menu()`. Wraps the whole session in a `try/except` so `Ctrl+C` / EOF triggers a graceful "forcefully exiting" message and a final critical log entry.

**`config.py`**
Resolves the project root (handles both normal script execution and a PyInstaller-frozen `.exe`), defines all shared folder/file path constants (`VENV_DIR`, `LOG_DIR`, `GIT_DIR`, `REPORT_DIR`, `SETTINGS`, etc.), ANSI color codes used throughout the UI, an `is_admin()` check, and a helper to add a Windows Firewall inbound rule for the listener port.

### `ui/` — Menu & Input Handling

**`menu.py`**
Renders the main dashboard and runs the input loop. On first run it initializes default settings and plays a "typewriter" boot sequence; on later runs it shows a shorter welcome. Dispatches numeric/letter choices to the corresponding `handle_*` function in `handler.py`.

**`handler.py`**
One `handle_*` function per top-level menu item. Each prints a sub-menu, takes a choice, and calls into the relevant `core`/`utils` class or function — e.g. `handle_network()` drives `NetworkHandler`, `handle_backup()` drives `BackupManager`, `handle_settings()` drives the settings editor functions, etc.

### `core/` — Feature Engines

**`network.py` — `NetworkHandler`**
- `scan_entire_lan()` — determines the local subnet by opening a dummy UDP socket to `8.8.8.8`, then pings every `.1`–`.254` address concurrently (`ThreadPoolExecutor`, 50 workers) to find live hosts.
- `get_and_save_port()` — probes a range of ports on a discovered IP and records the first responsive one, along with hostname and status, into the SQLite device table.
- `broadcast_msg()` / `broadcast_message()` / `sendmsg()` — send UDP text messages to one, many, or a specific saved device/port.
- `change_default_port()` — edits the configured default listener port in `settings.json`.
- `get_hostname()` — resolves hostname via reverse DNS, falling back to `nbtstat`.

**`inventory.py`**
- `scan_software()` / `check_software()` — walks the `SOFTWARE_CHECKS` section of `settings.json`, checking `PATH` and hardcoded install paths for each tool, and captures its version.
- `gen_soft_report()` — prints a compliance summary (installed vs. missing, % compliance) for the local machine.
- `generate_lan_system_report()` — broadcasts an `INFO` request to every device found by a LAN scan, waits for agents (`listener.py`) to respond, parses the accumulated telemetry blocks, prints a colorized health report per device (RAM/disk thresholds flagged as healthy/warning/critical), and optionally hands the aggregated data to `report.py` to produce a PDF.
- `parse_node_block()` / `print_clean_report()` — parse and pretty-print the raw JSON blocks written by remote agents into `reports/inventory.tmp`.

**`backup.py` — `BackupManager`**
Copies files from one or more source paths into a staging area, skipping:
- empty files/dirs
- paths inside any `ignored_folders` (from settings — e.g. `venv`, `.git`, `node_modules`)
- files whose extension is in `forbidden_extensions` (e.g. `.exe`, `.dll`, `.bat`)

It detects Python virtual environments (`pyvenv.cfg` present) and tags them in a manifest, writes an `info.json` manifest (skipped/empty file lists, operation time), then archives the staging folder into a timestamped ZIP — AES-encrypted via `pyzipper` if a password was supplied, or a plain ZIP otherwise — and verifies archive integrity before cleaning up staging files.

**`cleanup.py` — `CleanupManager`**
- `show_top_space_consumers()` — ranks top-level folders under a path by total size and renders an ASCII bar chart.
- `clean_temp_files()` — deletes everything in the OS temp directory.
- `empty_recycle_bin()` — uses `winshell` if available.
- `move_large_files_to_review()` — recursively finds files above a size threshold and moves/copies them into a `large_files_review` folder.

**`file_sorter.py` — `FileSorter`**
- `sort()` — categorizes every file in a target directory by extension (per the `BACKUP.extensions` map in settings) into a `Sorted/<Category>/` structure, with a live progress bar; supports `Ctrl+C` cancellation mid-run via a `SIGINT` handler.
- `sort_repeat()` — a TV-show-specific mode: uses a regex to detect season/episode markers (`SxxExx`, `1x01`, etc.) in filenames, groups matching video/subtitle files by inferred show title into per-show folders, and bins anything unmatched as "Non-series".

**`git.py` — `GitHandler`**
- `clone()` — accepts one or more `|`-separated repo URLs, creates a `git_repos/` folder, and clones each into a subfolder named after the repo.
- `open_git_bash()` — locates and launches `bash.exe` from a typical Git-for-Windows install.
- `pull()` — runs `git pull` against an existing local repo path.

**`venv.py` — `VenvHandler`**
- `create_venv()` — builds a new venv with the system's Python interpreter (auto-detected via `utils.check.find_system_python`) and moves it to a chosen destination (defaulting to a configured folder).
- `update_venv_deps()` — upgrades `pip` and then every installed package individually, either for one named venv or every venv found under `VENV_DIR`.
- `install_packages()` — installs one or more named packages into a specified venv.

### `utils/` — Shared Services

**`logger.py` — `LogHandler` (singleton: `log_manager`)**
Configures a single file-based logger (`logs/lab.log`) with timestamped, leveled entries. Provides `analyze_logs()` (colorized tail view), `log_summary()` (counts by severity), and `clear_system_logs()` (wipe with confirmation).

**`settings.py`**
Defines `DEFAULT_SETTINGS` (see [Configuration](#configuration)) and provides load/save/init for `settings.json`, plus interactive editors for string, numeric (bounded), boolean, and list-type settings, driven from the Settings menu.

**`database.py`**
Thin SQLite wrapper (`lab_manager.db`) with a `devices` table (IP, hostname, port, status, last-seen) and a `settings` table. Provides `save_device`, `get_device`, `get_all_saved_devices`, initializing the schema on import.

**`drive_manager.py`**
Uses `ctypes` calls into `kernel32` to enumerate Windows logical drives, filter by fixed/removable type, and report volume label, type, and free/total space in GB.

**`check.py`**
- Chocolatey detection/installation flow (prompts to install via a PowerShell bootstrap script if missing).
- Generic `check_tool_availability()` / `is_module_installed()` / `is_app_installed()` helpers.
- `find_system_python()` — locates a system Python distinct from the one running the app.
- `check_address_health()` — pings a URL with `requests` and reports status/latency, used for connectivity health checks.

**`execute.py`**
- `execute_task()` — runs a command, streaming stdout live and logging failures; used for long-running operations like pip upgrades.
- `execute_file()` — runs a command and reports success/failure without streaming.
- `clear_shell()` / `clear_shell_wi()` — pause-for-input-then-clear and clear-only screen helpers used throughout the menu system.

**`shell.py`**
- `open_shell_access()` — launches an interactive `cmd.exe` with a custom `LAB-SHELL:` prompt.
- `kill_port()` — finds and kills the process bound to a given port via `psutil`.
- `kill_process_by_name()` — kills all processes whose name matches a substring.

**`listener.py`** *(the agent)*
Meant to be run on each managed lab PC. Binds a UDP socket (default port `8088`) and loops, reacting to messages from the admin console:

| Message | Effect |
|---|---|
| `SHUTDOWN` | Schedules a system shutdown (`shutdown /s /t 30`) |
| `LOGOUT` | Logs the current user out |
| `RESTART` | Restarts the machine |
| `KILL` | Kills whatever is bound to the listener's own port |
| `INFO` | Gathers a full telemetry payload (`get_agent_data()`) and replies to the sender |
| *(telemetry-shaped text)* | Appends the payload to a local inventory temp file, for the LAN report flow |
| *(anything else)* | Pops up a Tkinter message box showing the sender and message |

`get_agent_data()` collects hostname, current user, CPU/RAM/disk usage, per-partition storage, OS platform/version, uptime, IP/MAC address, and — via `winreg`/`wmic`/PowerShell calls — CPU name, BIOS serial number, motherboard model, GPU name, and physical disk media type.

**`report.py`**
Builds a branded, multi-section PDF (`FPDF` subclass with custom header/footer) containing an executive KPI summary and a per-device inventory breakdown (status badge, network info, CPU/RAM/disk/OS detail), color-coded by health status (healthy/warning/critical).

**`help.py`**
Ensures a `help/` folder exists and displays `help/readme.txt` inside the console, highlighting lines starting with `>>` as headers.

**`progress_bar.py`**
A minimal single-line CLI progress bar (`[####----] 42.0%`) used by the file sorter and venv update flows.

---

## Configuration

All runtime configuration lives in a single `settings.json`, generated from `DEFAULT_SETTINGS` on first run:

```
GENERAL          → first_run flag, lab display name
NETWORK          → default_port, max_port_attempts, auto_scan_on_startup, ping_timeout
LISTENER         → agent listening port + a shared secret
BACKUP           → default_destination, per-category extension map, forbidden_extensions,
                    ignored_folders, default_sources, default_venv_destination
SOFTWARE_CHECKS  → per-tool command names, known install paths, and version flag
                    (pre-populated for Python, VS Code, Git)
SECURITY         → manage_firewall_rules, require_admin_privileges
```

Settings can be viewed and edited entirely from the in-app **Settings** menu — including nested dict values, lists (add/remove items), booleans (Y/N toggle), numbers (range-validated), and strings — or restored to defaults.

## Data Storage

- **`lab_manager.db`** (SQLite) — registry of devices discovered on the LAN (IP, hostname, assigned port, status, last-seen timestamp).
- **`logs/lab.log`** — all application logging, viewable/summarized/clearable from the Logs menu.
- **`reports/inventory.tmp`** — scratch file where the admin console accumulates telemetry replies from agents during a LAN-wide inventory scan.
- **`git_repos/`**, **`venvs/`**, **`help/`**, **`lab_manager_backups/`** — working directories created on demand by their respective modules.

## Setup

This is a Windows-only tool (it relies on `netsh`, `wmic`, `winreg`, `ctypes.windll`, `cmd.exe`, and Windows-style drive letters throughout).

1. Install Python 3.11+ and the dependencies used across the codebase:
   ```
   pip install colorama psutil requests pyzipper fpdf winshell
   ```
2. Run the admin console:
   ```
   python main.py
   ```
3. On lab PCs that should be remotely manageable, run the agent instead:
   ```
   python -c "from utils.listener import start_listener; start_listener(8088)"
   ```
   (or package it, e.g. via the referenced `build.bat` / PyInstaller, as `main.exe`).

## Usage

From the main dashboard, pick a number/letter to enter that feature's sub-menu — most sub-menus prompt for any additional input (paths, IPs, package names, etc.) they need. First run auto-generates `settings.json` with sensible defaults; use the **Settings** menu to adjust ports, backup rules, or software checks afterward.

## Known Issues

A few things worth being aware of when running or maintaining this code:

- **`main.py`** uses `except KeyboardInterrupt, EOFError:` — this is Python 2 syntax and will raise a `SyntaxError` under Python 3. It needs to be a tuple: `except (KeyboardInterrupt, EOFError):`.
- **`menu.py`** advertises menu option `[7] System Checks and Health` but the input loop's `if/elif` chain has no branch for `choice == "7"`, so it currently falls through to "Invalid option."
- Two versions of **`network.py`** and **`database.py`**-adjacent imports exist across the uploads (a flat module version and a class-based `core/network.py` version); make sure the final package layout consistently imports from `core/` vs `utils/` as referenced (e.g. `core/inventory.py` imports `from core.network import NetworkHandler`, while `utils/network.py`'s standalone version duplicates similar logic — likely legacy/superseded).
- `settings.py`'s `get_min_max()` only defines bounds for `default_port`; any other integer setting edited via the numeric editor will hit `None, None` bounds and fail comparisons.
- `report.py`'s `create_lab_report()` requires a `data` argument, but its `if __name__ == "__main__":` block calls it with none — running the file directly will raise a `TypeError`.
- `pdf.output("Lab Report.pdf")` in `report.py` doesn't use `REPORT_DIR`, so the PDF is written to the current working directory rather than the reports folder.

## Security Notes

This tool is designed for legitimate lab administration, but a few of its capabilities are inherently sensitive and worth deliberate handling if you deploy it:

- The **listener agent** accepts unauthenticated UDP commands (`SHUTDOWN`, `RESTART`, `LOGOUT`, `KILL`) from anyone on the network who knows the port — there's a `secret` field reserved in `settings.json` under `LISTENER`, but it isn't currently checked against incoming messages. This will be updated in later changes.
- **`shell.py`** exposes an elevated interactive shell and process-killing by name — restrict access to the admin console itself.
- Telemetry gathered (serial numbers, MAC addresses, logged-in usernames) should be handled per your institution's data-handling policy.
