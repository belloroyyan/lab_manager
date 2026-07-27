# Lab Manager

Lab Manager is a Windows-first, menu-driven administration console for managing a fleet of lab computers. It centralizes common IT tasks — provisioning, network scanning, backups, virtualenv management, system checks, cleanup, and reporting — into a single interactive CLI, backed by an encrypted UDP "listener" agent that runs on each managed endpoint.

Two roles are supported from the same codebase:

- **Admin Console** — run `main.py` on an administrative workstation to operate the dashboard and orchestrate actions across the lab.
- **Agent (Listener)** — `utils/listener.py` runs on managed workstations, authenticates and decrypts requests from the admin console, and replies with telemetry or executes approved remote commands.

A companion provisioning tool, **PLEM** (Py-Lab Environment Manager, `core/plem.py`), ships alongside the console for bootstrapping brand-new lab PCs from a YAML spec.

---

## Table of Contents

- [Lab Manager](#lab-manager)
  - [Table of Contents](#table-of-contents)
  - [Highlights](#highlights)
  - [Architecture](#architecture)
  - [Feature Overview](#feature-overview)
  - [Quick Start](#quick-start)
    - [PLEM (standalone provisioning tool)](#plem-standalone-provisioning-tool)
  - [Configuration](#configuration)
  - [Data Storage](#data-storage)
  - [Module Reference](#module-reference)
    - [Entry Point](#entry-point)
    - [`ui/` — Menu \& Input Handling](#ui--menu--input-handling)
    - [`core/` — Feature Engines](#core--feature-engines)
    - [`utils/` — Shared Services](#utils--shared-services)
  - [Security](#security)
  - [Known Issues](#known-issues)
  - [Changelog](#changelog)
  - [Contributing](#contributing)
  - [License \& Acknowledgements](#license--acknowledgements)

---

## Highlights

- Modular design separating UI (`ui/`), core business logic (`core/`), and shared low-level services (`utils/`).
- **Encrypted agent protocol** — all listener traffic is symmetric-encrypted with a shared Fernet key and gated behind a password-protected identity file; destructive commands (`SHUTDOWN`, `RESTART`, `LOGOUT`, `KILL`) are rejected unless an operator explicitly enables a time-boxed remote-command window.
- Inventory and telemetry collection with branded PDF reporting.
- Backup engine with optional AES encryption (`pyzipper`).
- Virtualenv management and bulk package operations.
- Concurrent LAN scanning and device persistence (SQLite).
- Self-update check against GitHub Releases.
- Standalone provisioning tool (PLEM) for setting up brand-new machines from a declarative YAML config.

---

## Architecture

```
lab_manager/
├── core/                   # Feature engines (business logic)
│   ├── backup.py           # Backup/archival engine (pyzipper support)
│   ├── cleanup.py          # Disk usage analysis & cleanup utilities
│   ├── file_sorter.py      # File/media sorting engine
│   ├── git.py              # Git clone and helper utilities
│   ├── inventory.py        # Inventory and LAN reporting flows
│   ├── network.py          # Scanning, hostname resolution, port probing
│   ├── plem.py             # PLEM: standalone new-PC provisioning tool
│   └── venv.py             # Virtual environment lifecycle
│
├── ui/                     # Interactive menu + routing
│   ├── menu.py             # Main dashboard loop
│   └── handler.py          # Submenu handlers that call core/utils
│
├── utils/                  # Shared low-level services
│   ├── check.py            # Software/tool detection, Chocolatey bootstrap
│   ├── database.py         # SQLite device registry (lab_manager.db)
│   ├── drive_manager.py    # Windows logical-drive enumeration (ctypes)
│   ├── execute.py          # Subprocess execution wrapper
│   ├── help.py             # In-console help viewer
│   ├── identity.py         # Encrypted identity file + Fernet key helpers
│   ├── listener.py         # UDP listener agent (runs on endpoints)
│   ├── logger.py           # Central logging utilities
│   ├── progress_bar.py     # Minimal CLI progress bar
│   ├── report.py           # PDF generator (fpdf)
│   ├── settings.py         # settings.json load/save and editors
│   ├── shell.py             # Elevated shell, port/process kill, file hide/unhide
│   └── update.py           # GitHub Releases update checker
│
├── config.py               # Project path constants, ANSI colors, admin check
├── main.py                 # Application bootstrapper (admin console)
├── settings.json            # Runtime settings (generated on first run)
└── lab_manager.db            # SQLite registry (created at runtime)
```

Several folders are created on demand outside the project root, on the user's **Desktop** (see `config.py`): `Desktop/Lab Manager/venvs`, `git_repos`, `lab_manager_backups`, and `reports`. The encrypted device identity lives under `%PROGRAMDATA%/LabManager/lab_secret.json`, separate from the project tree.

---

## Feature Overview

| Category | What it does |
|---|---|
| **Configure New PC / Install Software** | Points operators at the standalone PLEM tool (`plem.bat`) for provisioning brand-new machines — not run in-process from the dashboard. |
| **Storage Operations** | Sorts loose files into categorized folders by extension, or groups TV episodes into per-show folders using regex pattern matching on filenames. |
| **Backup** | Archives one or more source paths into a password-protected (AES) ZIP, excluding empty files, ignored folders, and forbidden extensions; verifies the archive afterward. |
| **Git Operations** | Bulk-clones one or more repositories into a `git_repos/` folder; can also drop into a Git Bash shell. |
| **Virtual Environments** | Creates, moves, and manages Python venvs; can bulk-upgrade every installed package in one or all venvs; installs arbitrary packages into a chosen venv. |
| **Network** | Multi-threaded ping sweep of the local subnet, hostname resolution, encrypted UDP messaging to all/selected devices, port scanning + SQLite persistence of discovered devices, and starting the listener agent locally. |
| **System Checks / Inventory** | Verifies required software (Python, Git, VS Code, etc.) is installed and reports versions; can query every online LAN device for hardware/OS telemetry and assemble a lab-wide health report. |
| **Cleanup** | Reports the largest folders under a path, purges the temp directory, empties the Recycle Bin, and relocates oversized files into a review folder. |
| **I/O** | Opens an elevated system shell, runs local or LAN-wide inventory checks, generates/imports the shared Fernet secret key, rebuilds a PDF from the last saved scan, and can force-kill the listener port. |
| **Logs** | Summarizes and colorizes recent log activity by severity, or wipes the log file. |
| **Settings** | View and interactively edit any setting (strings, numbers, booleans, lists) in `settings.json`, or reset to defaults. |
| **Check for Updates** | Compares the running version against the latest GitHub release and offers to open the download page. |
| **Reporting** | Generates a styled multi-section PDF summarizing fleet status, critical flags, and per-device hardware/storage detail. |

---

## Quick Start

Prerequisites (Windows): Python 3.11+ and the packages below.

Install dependencies:

```powershell
pip install colorama psutil requests pyzipper fpdf winshell cryptography packaging pyyaml
```

Run the admin console:

```powershell
python main.py
```

The console requests administrator elevation on launch and relaunches itself via UAC if needed.

Run the listener agent on a managed workstation:

```powershell
python utils/listener.py
```

or trigger it from the console's **Network → Start Listener** menu item. On first run (or with `--setup` / `-s`), the listener walks through a **first-time setup wizard**: it sets an operator password, records the school/lab name and bench number, optionally imports a shared `secret.key`, creates a Windows Firewall rule for UDP port `8088`, and can register itself as a scheduled task that restarts on failure and auto-starts at logon.

Notes:
- The first run of `main.py` also creates `settings.json` from defaults, plus working folders such as `Desktop/Lab Manager/venvs`, `git_repos`, `reports`, and `lab_manager_backups` as needed.
- Both `main.py` and `utils/listener.py` expect to run elevated; if launched without admin rights they relaunch themselves via `ShellExecuteW("runas", ...)`.

### PLEM (standalone provisioning tool)

`core/plem.py` is a separate entry point (invoked via `plem.bat`, not from the main dashboard) for setting up a brand-new lab PC. Given a `plem.yaml` describing `python_dependencies.pip_install` and per-OS `system_tools` commands, it:

1. Elevates itself to administrator if not already running as one.
2. Creates (or reuses) a dedicated virtualenv and installs any missing pip packages into it.
3. Checks for a package manager (`choco` / `brew` / `snap` depending on OS) and, on Windows, skips Chocolatey installs that are already present before running the rest.

---

## Configuration

All runtime configuration lives in `settings.json`, generated from `utils/settings.DEFAULT_SETTINGS` on first run:

```
GENERAL          → role, first_run flag, school_name, lab_name
NETWORK          → default_port, max_port_attempts, auto_scan_on_startup, ping_timeout
LISTENER         → agent listening port + a (legacy/reserved) secret_key field
BACKUP           → skip flag, default_destination, per-category extension map,
                    forbidden_extensions, ignored_folders, default_sources,
                    default_venv_destination
SOFTWARE_CHECKS  → per-tool command names, known install paths, and version flag
                    (pre-populated for Python, VS Code, Git)
SECURITY         → manage_firewall_rules, require_admin_privileges
```

Settings can be viewed and edited entirely from the in-app **Settings** menu — including nested dict values, lists (add/remove items), booleans (Y/N toggle), numbers (range-validated), and strings — or restored to defaults.

Note: the actual shared encryption key used for agent traffic lives in the separate, encrypted **identity file** (see [Security](#security)), not in `settings.json`'s `LISTENER.secret_key` field, which is a legacy placeholder.

## Data Storage

- **`lab_manager.db`** (SQLite) — registry of devices discovered on the LAN (IP, hostname, assigned port, status, last-seen timestamp).
- **`logs/lab.log`** — application logging, viewable/summarized/clearable from the Logs menu.
- **`Desktop/Lab Manager/reports/inventory.tmp`** — scratch file where the admin console accumulates decrypted telemetry replies from agents during a LAN-wide inventory scan.
- **`Desktop/Lab Manager/{git_repos, venvs, lab_manager_backups, reports}`** — working directories created on demand by their respective modules.
- **`%PROGRAMDATA%/LabManager/lab_secret.json`** — the per-device identity file (Windows hidden attribute set): operator password hash, shared Fernet key, school/lab name, bench number, and optional log path. Used by both the admin console (to encrypt outgoing messages) and the listener (to decrypt/authenticate incoming ones).

---

## Module Reference

### Entry Point

**`main.py`**
Ensures the Desktop working directory and identity directory exist, sets the console window title, hides the identity file, initializes logging, and launches `display_menu()`. Relaunches itself elevated if not already running as administrator, and wraps the session in exception handling so `Ctrl+C` / EOF triggers a graceful exit and a final log entry.

**`config.py`**
Resolves the project root (handles both normal script execution and a PyInstaller-frozen `.exe`), defines the application version and GitHub repo slug, all shared folder/file path constants (`VENV_DIR`, `LOG_DIR`, `GIT_DIR`, `REPORT_DIR`, `IDENTITY_DIR`, `IDENTITY_FILE`, etc.), ANSI color codes used throughout the UI, and an `is_admin()` check.

### `ui/` — Menu & Input Handling

**`menu.py`**
Renders the main dashboard and runs the input loop. On first run it initializes default settings and plays a "typewriter" boot sequence; on later runs it shows a shorter welcome. Dispatches numeric/letter choices to the corresponding `handle_*` function in `handler.py`. Also exposes hidden `hide` / `unhide` commands that toggle the Windows hidden attribute on the identity file.

**`handler.py`**
One `handle_*` function per top-level menu item. Each prints a sub-menu, takes a choice, and calls into the relevant `core`/`utils` class or function — e.g. `handle_network()` drives `NetworkHandler`, `handle_backup()` drives `BackupManager`, `handle_io()` also handles secret-key generation/import and rebuilding a PDF report from the last saved LAN scan, `handle_update()` drives the GitHub update checker, etc.

### `core/` — Feature Engines

**`network.py` — `NetworkHandler`**
- `scan_entire_lan()` — determines the local subnet by opening a dummy UDP socket to `8.8.8.8`, then pings every `.1`–`.254` address concurrently (`ThreadPoolExecutor`, 50 workers) to find live hosts.
- `get_and_save_port()` — probes a range of ports on a discovered IP and records the first responsive one, along with hostname and status, into the SQLite device table.
- `create_message()` / `broadcast_message()` / `sendmsg()` — send encrypted UDP messages to one, many, or a specific saved device/port.
- `change_default_port()` — edits the configured default listener port in `settings.json`.
- `get_hostname()` — resolves hostname via reverse DNS, falling back to `nbtstat`.

**`inventory.py`**
- `scan_software()` / `check_software()` — walks the `SOFTWARE_CHECKS` section of `settings.json`, checking `PATH` and hardcoded install paths for each tool, and captures its version.
- `gen_soft_report()` — prints a compliance summary (installed vs. missing, % compliance) for the local machine.
- `generate_lan_system_report()` — broadcasts an `INFO` request to every device found by a LAN scan, waits for agents (`listener.py`) to respond, parses the accumulated decrypted telemetry blocks, prints a colorized health report per device (RAM/disk thresholds flagged as healthy/warning/critical), and optionally hands the aggregated data to `report.py` to produce a PDF.
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

**`plem.py`** *(standalone tool, see [PLEM](#plem-standalone-provisioning-tool))*
Reads `plem.yaml`, elevates to admin if needed, creates/reuses a virtualenv, installs missing pip dependencies, and runs per-OS system-tool install commands (skipping ones Chocolatey already reports as installed on Windows).

### `utils/` — Shared Services

**`identity.py`**
Manages the encrypted, hidden identity file: load/save helpers that toggle the Windows hidden attribute around file access, Fernet key generation, exporting a `secret.key` file for distribution (e.g. via USB), importing an existing key, and `encrypt_message()` / `decrypt_message()` wrappers used by both the console and the listener.

**`listener.py`** *(the agent)*
Meant to be run on each managed lab PC. Binds a UDP socket (default port `8088`) and loops, decrypting each incoming message and reacting to it:

| Message | Effect |
|---|---|
| `INFO` | Gathers a full telemetry payload (`get_agent_data()`), encrypts it, and replies to the sender |
| `PING` | Replies with an encrypted `PONG` (basic reachability/health check) |
| `ENABLE_REMOTE [minutes]` | Opens a time-boxed window (1–60 min, default 10) during which destructive commands are accepted |
| `DISABLE_REMOTE` | Immediately closes that window |
| `SHUTDOWN` / `RESTART` / `LOGOUT` / `ABORT` / `KILL` | Only executed while the remote-command window is open; otherwise logged and rejected |
| *(telemetry-shaped payload)* | Appended to the local inventory temp file, for the LAN report flow |
| *(anything else)* | Pops up a Tkinter message box showing the sender and message |

On first run (or `--setup`/`-s`), `run_first_time_setup()` prompts for an operator password (PBKDF2-HMAC-SHA256 hashed and salted), school/lab name, bench number, and optional log path; offers to import a shared `secret.key`; creates a Windows Firewall inbound rule for UDP `8088` if running elevated; and offers to register a self-healing scheduled task (`LabManagerListener`) that starts the listener at logon and restarts it on failure.

`get_agent_data()` collects hostname, current user, bench number, CPU/RAM/disk usage, per-partition storage, OS platform/version/uptime, IP (LAN + resolved) and MAC address, and — via `winreg`/`wmic`/PowerShell calls — CPU name, BIOS serial number, motherboard model, GPU name, and physical disk media type.

**`check.py`**
- Chocolatey detection/installation flow (prompts to install via a PowerShell bootstrap script if missing).
- Generic `check_tool_availability()` / `is_module_installed()` / `is_app_installed()` / `is_choco_package_installed()` helpers.
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
- `hide_file()` / `unhide_file()` — toggle the Windows hidden file attribute, used to keep the identity file out of casual view between accesses.

**`logger.py` — `LogHandler` (singleton: `log_manager`)**
Configures a single file-based logger (`logs/lab.log`) with timestamped, leveled entries. Provides `analyze_logs()` (colorized tail view), `log_summary()` (counts by severity), and `clear_system_logs()` (wipe with confirmation).

**`settings.py`**
Defines `DEFAULT_SETTINGS` (see [Configuration](#configuration)) and provides load/save/init for `settings.json`, plus interactive editors for string, numeric (bounded), boolean, and list-type settings, driven from the Settings menu.

**`database.py`**
Thin SQLite wrapper (`lab_manager.db`) with a `devices` table (IP, hostname, port, status, last-seen) and a `settings` table. Provides `save_device`, `get_device`, `get_all_saved_devices`, initializing the schema on import.

**`drive_manager.py`**
Uses `ctypes` calls into `kernel32` to enumerate Windows logical drives, filter by fixed/removable type, and report volume label, type, and free/total space in GB.

**`report.py`**
Builds a branded, multi-section PDF (`FPDF` subclass with custom header/footer) containing an executive KPI summary and a per-device inventory breakdown (status badge, network info, CPU/RAM/disk/OS detail), color-coded by health status (healthy/warning/critical).

**`update.py`**
Compares the running `APP_VERSION` (`config.py`) against the latest tag on the project's GitHub Releases page; if newer, prints release notes and version info and offers to open the download page in a browser.

**`help.py`**
Ensures a `help/` folder exists and displays `help/readme.txt` inside the console, highlighting lines starting with `>>` as headers.

**`progress_bar.py`**
A minimal single-line CLI progress bar (`[####----] 42.0%`) used by the file sorter and venv update flows.

---

## Security

The agent protocol has moved past the "TODO" stage described in earlier versions of this project — remote commands are now encrypted and gated, though several hardening items remain.

**In place today:**

- All UDP traffic between the console and the listener is encrypted with a Fernet symmetric key stored in the hidden, per-device identity file, which is itself protected by an operator password (PBKDF2-HMAC-SHA256, salted).
- Destructive commands (`SHUTDOWN`, `RESTART`, `LOGOUT`, `ABORT`, `KILL`) are rejected by the listener unless an operator has explicitly sent `ENABLE_REMOTE` within the last 1–60 minutes; the window auto-expires and can be closed early with `DISABLE_REMOTE`.
- The identity file's Windows hidden attribute is toggled on around each read/write to reduce casual exposure.
- The shared key is distributed out-of-band (export to a `secret.key` file, e.g. via USB) rather than transmitted over the network.

**Remaining considerations:**

- Any host that possesses the shared Fernet key can issue commands to a listener; key distribution/rotation discipline is the primary control, not per-message individual authentication.
- Sensitive telemetry (serial numbers, MAC addresses, usernames) is collected; treat inventory data per your institution's data-handling policies.
- `core/plem.py`'s `execute_command()` runs with `shell=True` when given a string command (as opposed to a list); avoid feeding it untrusted input.
- The listener and console both request administrator/elevated privileges — restrict who can run the admin console and who has access to the shared key.

---

## Known Issues

- **Unit tests and integration tests** are not yet available.
- **`settings.json`'s `LISTENER.secret_key`** field is a legacy placeholder and is not the key actually used for encryption (see [Configuration](#configuration)); this can be confusing when auditing configuration.
- **PLEM is disconnected from the main dashboard** — menu option `[1]` only prints instructions to run `plem.bat` separately, rather than invoking `core/plem.py` in-process.
- **`handle_syscheck()`** renders its sub-menu header but does not yet wire up any of the three listed choices.

---

## Changelog

- **v2.1.3** (current) — Encrypted agent protocol
  - Introduced `utils/identity.py` and a Fernet-encrypted, password-protected identity file shared between console and listener.
  - Reworked `utils/listener.py`: encrypted `INFO`/`PING` replies, time-boxed `ENABLE_REMOTE`/`DISABLE_REMOTE` gating for destructive commands, first-time setup wizard, Windows Firewall rule creation, and a self-healing scheduled task for auto-start/restart.
  - Added `utils/update.py` for GitHub Releases-based update checks, surfaced via the `[U]` menu option.
  - Added standalone `core/plem.py` (Py-Lab Environment Manager) for YAML-driven provisioning of new machines.
- **v1.1** — Stability & correctness fixes
  - Fixed Python 2 exception syntax in `main.py`.
  - Fixed menu routing for option 7.
  - Fixed SQL PRIMARY KEY syntax and improved DB connection handling.
  - Fixed ping timeout logic and improved error handling in network utilities.
  - Ensured PDF reports are written to `reports/` and improved direct invocation behavior.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Run tests locally (none included yet — please add tests for your changes).
3. Submit a pull request with a clear description and changelog entry.

Please follow the existing code style and include unit tests for core logic where possible.

---

## License & Acknowledgements

This project was created as a lab management utility.