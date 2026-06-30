import subprocess, shutil, time, os, json
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style
from utils.settings import load_settings
from utils.logger import log_manager
from core.network import NetworkHandler
from config import REPORT_DIR

init(autoreset=True)
magenta = Fore.MAGENTA
reset = Style.RESET_ALL

networkhandler = NetworkHandler()
logger = log_manager.get_logger("Inventory")
settings = load_settings()
software_dict = settings.get("SOFTWARE_CHECKS")

print(f"\n    {magenta}Checking for reports folder...")
if not os.path.exists(REPORT_DIR):
    os.mkdir(REPORT_DIR)
    logger.info("Created `reports` folder.")
time.sleep(.5)
print(f"\n    {magenta}Found `reports` folder within base directory.{reset}")
print(f"    {REPORT_DIR}")

def check_software(name, info : dict):
    result = {
        "name" : name,
        "installed" : False,
        "path" : None,
        "version" : None
    }

    for cmd in info["command"]:
        p = shutil.which(cmd)
        if p:
            result["installed"] = True
            result["path"] = p
            break
    for path in info["paths"]:
        p = Path(path)
        if p.exists():
            result["installed"] = True
            result["path"] = p
            break
    if result["installed"] and info["version_flag"]:
        try:
            output = subprocess.check_output([result["path"], info["version_flag"]], stderr=subprocess.STDOUT, text=True, timeout=5)
            result["version"] = output.strip().split("\n")
        except Exception as e:
            result["version"] = "Unknown"
            logger(f"Unknown error: {e}")
        return result

def scan_software():
    results = []
    for name, info in software_dict.items():
        result = check_software(name, info)
        results.append(result)
    return results

def print_clean_report(staging_file_path):
    if not os.path.exists(staging_file_path) or os.path.getsize(staging_file_path) == 0:
        print(f"{Fore.RED}[-] No telemetry data found in staging file.")
        return

    with open(staging_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_node = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("=== Node Source:"):
            current_node = line.replace("===", "").strip()
            print(f"\n{Fore.CYAN}{Style.BRIGHT}  {current_node}")
            print(f"  {Fore.CYAN}" + "─" * 50)
            continue
        if line.startswith("---"):
            continue
        try:
            json_str = line
            if not json_str.startswith("{"):
                json_str = "{" + json_str
            if not json_str.endswith("}"):
                if json_str.endswith("."):
                    json_str += "0"
                json_str += "}"
            data = json.loads(json_str)
            print(f"  {Fore.WHITE}Hostname     : {Fore.GREEN}{data.get('hostname', 'N/A')}")
            print(f"  {Fore.WHITE}OS Version   : {Fore.GREEN}{data.get('os', 'N/A')} {data.get('release', '')}")
            print(f"  {Fore.WHITE}Active User  : {Fore.YELLOW}{data.get('current_user', 'N/A')}")
            use_pct = data.get('disk_use_percent', 0)
            disk_color = Fore.GREEN
            if use_pct > 90:
                disk_color = Fore.RED
            elif use_pct > 75:
                disk_color = Fore.LIGHTYELLOW_EX

            print(f"  {Fore.WHITE}Storage Disk : {disk_color}{data.get('disk_free_gb', 0)} GB Free / {data.get('disk_total_gb', 0)} GB Total ({use_pct}%)")
        except Exception as e:
            print(f"  {Fore.LIGHTBLACK_EX}Raw Data: {line}")
    print(f"\n  {Fore.CYAN}" + "-" * 50)

def gen_comp_result(results):
    installed_count = sum(1 for s in results if s["installed"])
    total = len(results)
    missing = [s["name"] for s in results if not s["installed"]]

    report = {
        "missing_count" : len(missing),
        "total_checked" : total,
        "installed" : installed_count,
        "missing_software" : missing,
        "comp_percentage" : round((installed_count / total) * 100, 2) if total > 0 else 0
    }

    return report

def gen_soft_report():
    print("\n=== Software Inventory Scan ===\n")
    results = scan_software()
    for item in results:
        status = "-> Installed" if item["installed"] else "-> Missing"
        version = f" | {item['version']}" if item.get("version") else ""
        path = f" | {item['path']}" if item.get("path") else ""
        print(f"{item['name']:<20} {status}{version}{path}")
    report = gen_comp_result(results)
    print("\n" + "=" * 50)
    print(f"Compliance: {report['comp_percentage']}% "
          f"({report['installed']}/{report['total_checked']} tools found)")
    if report["missing_software"]:
        print(f"\nMissing: {', '.join(report['missing_software'])}")
    else:
        print("\nAll required software is present.")
    return report

def gen_sys_report_on_lan():
    devices = networkhandler.scan_entire_lan()
    for ip in devices:
        if networkhandler.get_my_ip() == ip:
            continue
        networkhandler.broadcast_msg(ip, "INFO")
    print(f"-> Reading metrics...")
    time.sleep(4)

def generate_lan_system_report(port=8088):
    """
    Sends 'INFO' request to target lab PCs via UDP,
    listens for responses, and logs them to a separate text file.
    """
    target_ips = networkhandler.scan_entire_lan()
    wait_timeout = len(target_ips) * 5
    report_dir = REPORT_DIR / "inventory.tmp"
    if report_dir.exists():
        os.remove(report_dir)
        print(f"Deleted old inventory entries.")
    print(f"[+] Initializing LAN System Report pipeline...")
    print(f"[+] Broadcast target port: {port} | Listening window: {wait_timeout}s")
    for ip in target_ips:
        try:
            networkhandler.broadcast_msg(ip, "INFO")
        except Exception as e:
            print(f"[-] Failed to drop query frame to {ip}.")
            logger.error(f"Failed to drop query frame to {ip}: {e}.")
    print(f"[-] Queries dispatched. Awaiting client telemetry packets...")
    time.sleep(wait_timeout)
    print("\n" + "="*50)
    print("      FOCIT LAB MANAGER CENTRAL SYSTEM REPORT     ")
    print(f"      Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    if report_dir.exists() and report_dir.stat().st_size > 0:
        print_clean_report(report_dir)
    else:
        print("[-] No responses logged by background listener within the window.")
        print("    Ensure lab agents are alive and firewall rules are active.")
    print("="*50)    
    