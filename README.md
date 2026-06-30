# 🧪 Lab Manager Engine v2.0

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

Lab Manager v2.0 is an enterprise-grade administration utility engineered to automate the configuration, management, and recovery of Computing Lab environments at FOCIT, UNIOSUN. Upgraded with asynchronous multi-threading, asynchronous UDP discovery loops, and dynamic pattern matching, it streamlines software deployments, audits network subnets, and manages local storage layers to keep lab workstations operating at peak efficiency.

---

## Functionality & Modules

### 1. Decoupled UDP Network Discovery & Inventory Reporting

Built across `core/network.py` and handled concurrently by `utils/listener.py`, this module features a highly resilient, non-blocking hardware connectivity and telemetry mapping loop.

* **Shared-State Architecture:** Rather than binding conflicting ports on the same machine, the inventory sub-module acts purely as an event **Trigger & Viewer**. It broadcasts an `"INFO"` UDP command packet to target lab subnets and waits.
* **Background Telemetry Aggregation:** The always-on central `utils/listener.py` background daemon intercepts the incoming workstation UDP metric streams, strips corrupted packet frames, automatically patches truncated strings, and appends the formatted data live into a single staging cache file (`utils/network_inventory.tmp`).
* **Visual Console Parsing:** When the main inventory runtime wakes up, it reads the shared staging file, evaluates disk usages (triggering **Red Alerts** for stations exceeding 90% capacity), and renders an aligned system topology dashboard utilizing `colorama`.

### 2. Automated Storage Optimization & Active Cleanup Suite

Driven by the standalone `cleanup.py` engine, this diagnostic utility provides automated maintenance tools to address storage bottlenecks on cluttered workstations.

* **Granular Disk Visualizations:** Uses recursive size summation (`rglob('*')`) to locate data-heavy directories. It prints real-time console graphs displaying the relative weight distribution (in MBs) of directories next to responsive percentage indicators.
* **Cache Purging & Win32 Recycle Bin Emptying:** Employs `tempfile` abstractions to automatically locate system directories and wipe temp files safely using `shutil.rmtree`. If administrative bindings are present, it links directly to the `winshell` Windows API layer to force silent, non-blocking purges of the Recycle Bin.
* **Large File Isolation:** Evaluates user-defined thresholds (e.g., isolating everything $\ge$ 100 MB) and routes large or dormant files into a secure local `large_files_review` folder using atomic moves or copies to avoid disk fragmentation.

### 3. Non-Recursive Surface Sorter Engine

Located within `core/file_sorter.py`, this is a highly optimized flat-file grouping utility specifically written to organize scattered video assets without nested directory traversal.

* **Surface-Level Skimming:** Utilizing `pathlib.Path.iterdir()`, the script looks explicitly at the immediate folder layer, safely ignoring existing subdirectories to save storage disk I/O cycles.
* **Regex Token Extraction:** Uses a customized regular expression pattern (`re.compile`) to match common media tracking tags. It cleanly extracts titles from patterns containing full season listings (`S01E03`), standalone episode identifiers (`E05`, `e12`), or classic structures (`2x14`).
* **Atomic Remapping:** Once titles are filtered and formatted to Title Case, files are safely and dynamically moved into fresh, dedicated series folders using `shutil.move`.

### 4. Smart Backup, Git, & Venv Pipelines

A specialized disaster recovery and machine provisioning mechanism designed to make workstation projects highly portable.

* **Smart Compression (`core/backup.py`):** Recursively backs up active project source files while reading your configuration settings to exclude heavy, non-essential data bloat. It strips dependencies and hidden files automatically.
* **Workspace Replication (`core/git.py` & `core/venv.py`):** Automatically interfaces with remote repositories to handle cloning operations, while the virtual environment module dynamically provisions isolated Python sandboxes on completely fresh systems.

### 5. Integrated Utilities Framework

The `utils/` directory serves as the shared services backend for the entire ecosystem:

* **Storage & Shell (`database.py`, `drive_manager.py`, `shell.py`):** Interacts with local databases for tracking states, targets active storage drives, and executes low-level administrative shell tasks safely.
* **Runtime Execution (`execute.py`, `settings.py`, `check.py`):** Coordinates centralized multi-threaded routing arrays, handles configuration constraints from `settings.json`, and verifies system environment integrity.
* **Background Monitoring (`listener.py`, `logger.py`, `progress_bar.py`):** Spawns quiet thread listeners for environmental events, formats system log traces, and renders fluid command-line status graphics during long I/O operations.

---

## System Topology

```text
lab_manager/
│
├── core/
│   ├── __init__.py
│   ├── backup.py        # Project compression & data exclusion filters
│   ├── file_sorter.py   # Flat-file media regex tokenization & batch routing
│   ├── git.py           # Remote repository cloning automation mechanics
│   ├── network.py       # Multi-threaded ping sweeps & subnet auditing
│   └── venv.py          # Automated virtual environment replication pipeline
│   └── cleanup.py       # Workstation storage audit, temp cleaner & asset review engine
│   └── inventory.py       # Network telemetry broadcaster, scheduler, and console dashboard viewer
│
├── ui/
│   ├── __init__.py
│   ├── menu.py          # Primary user interface CLI menus
│   └── handler.py       # Input evaluation & isolated setting modifiers
│
├── utils/
│   ├── __init__.py
│   ├── check.py         # Integrity assertions & environment checking
│   ├── database.py      # Database engine tracking & metrics logging
│   ├── drive_manager.py # Physical storage allocation & drive monitoring
│   ├── execute.py       # Centralized command routing thread coordinator
│   ├── help.py          # On-demand instruction dictionaries & manuals
│   ├── listener.py      # Background UDP telemetry event monitoring loop
│   ├── logger.py        # Diagnostic transaction writing pipeline
│   ├── progress_bar.py  # Custom CLI structural progress rendering utilities
│   ├── settings.py      # Environment variables & run state profiles
│   └── shell.py         # Elevated system instruction wrapper interface
│
├── build.bat            # Automated PyInstaller compilation script
├── main.py              # Application runtime bootstrapper
├── main.exe             # Precompiled runnable administrative binary executable
├── config.py            # Key static variables & relative path storage
└── settings.json        # Dynamic runtime configuration JSON schema settings

```

---

## Getting Started

### Prerequisites

* Windows 10 / 11
* Python 3.14+ (Recommended)
* Administrative Privileges (Required for executing system repairs, running disk sweeps, purging protected paths, opening firewall rules, raw socket listening, and software provisioning)

### Installation & Local Usage

1. Clone the repository workspace files into your local directory.
2. Install the necessary external dependencies via your command prompt:
```bash
pip install colorama requests beautifulsoup4 winshell

```


3. Launch the interactive administrative terminal dashboard directly from source:
```bash
python main.py

```



---

## Production Binary Compilation (`build.bat`)

The root environment includes an automated compilation script (`build.bat`) to package your scripts into a single, standalone Windows executable (`main.exe`).

**CRITICAL DEVELOPER NOTE BEFORE COMPILING:**
The script links directly against global roaming user dependencies. Open `build.bat` in a text editor and update the `%ROAMING_LIBS%` environment path to match your specific Windows username directory:

```bat
:: Change "YOUR_USERNAME" to match your active Windows profile name
set ROAMING_LIBS="C:\Users\YOUR_USERNAME\AppData\Roaming\Python\Python314\site-packages"

```

Once modified, execute the compilation pipeline by double-clicking or running:

```cmd
build.bat

```

The compiled, optimized standalone file will be exported directly into your local `\dist` folder.

---

## Built With

* **Python 3.14** - Core runtime logic, storage manipulation, optimized regular expressions, concurrent worker pools, and UDP socket architectures.
* **PyInstaller** - Executable binary packaging and asset dependency wrapping.
* **Windows API / Netsh** - Native Shell shell calls, administrative elevation checks, and firewall port configurations.

## 👤 Developer

**Bello Royyan A.** UNIOSUN Software Engineering

Supporting FOCIT lab infrastructure since 2025.

## 📄 License

This project is proprietary and developed exclusively for official use at Osun State University (UNIOSUN). © 2026 Bello Royyan A. All rights reserved.
