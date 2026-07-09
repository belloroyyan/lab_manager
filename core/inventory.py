import subprocess, shutil, time, os, json, re
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from colorama import init, Fore, Style
from utils.settings import load_settings
from utils.logger import log_manager
from core.network import NetworkHandler
from utils.report import create_lab_report
from config import REPORT_DIR

init(autoreset=True)
magenta = Fore.MAGENTA
yellow = Fore.YELLOW
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
            output = subprocess.check_output([result["path"], info["version_flag"]], stderr=subprocess.STDOUT, text=True, timeout=10)
            result["version"] = output.strip().split("\n")[0]
        except Exception as e:
            result["version"] = "Unknown"
            logger.error(f"Unknown error: {e}")
        return result

def scan_software():
    results = []
    for name, info in software_dict.items():
        result = check_software(name, info)
        results.append(result)
    return results

def parse_node_block(raw_data: str) -> dict:
    blocks = raw_data.split("----------------------------------------")
    parsed_agents = {}
    for block in blocks:
        cleaned_block = block.strip()
        if not cleaned_block:
            continue
        try:
            json_string = f"{{{cleaned_block}}}"
            agent_data = json.loads(json_string)
            parsed_agents[agent_data["agent_id"]] = agent_data
        except json.JSONDecodeError as e:
            print(f"Failed to parse a block: {e}")
    return parsed_agents

def print_clean_report(data: dict):
    if not isinstance(data, dict):
        print(f"{Fore.RED}[-] Invalid data type. Expected dictionary.")
        return
    issues = {"critical" : 0, "warning" : 0, "note" : []}
    cyan = Fore.CYAN
    green = Fore.GREEN
    yellow = Fore.YELLOW
    red = Fore.RED
    reset = Style.RESET_ALL

    agent_id = data.get("agent_id", "N/A")
    hostname = data.get("hostname", "N/A")
    current_user = data.get("current_user", "Unknown")
    timestamp = data.get("timestamp", "N/A")
    cpu_name = data.get("cpu_name", "Unknown")
    cpu_model = data.get("model", "Unknown")
    serial_no = data.get("serial_number", "N/A")
    motherboard = data.get("motherboard", "N/A")
    cpu_usage = data.get("current_usage_percent", 0)
    cores_phys = data.get("cores_physical", "?")
    cores_log = data.get("cores_logical", "?")
    gpu = data.get("gpu", "?")
    ram_total = data.get("ram_total_gb", 0)
    ram_avail = data.get("ram_available_gb", 0)
    ram_pct = data.get("ram_used_percent", 0)
    storage = data.get("storage", [])
    drive_type = data.get("drive_type", "?")
    platform = data.get("platform", "N/A")
    release = data.get("release", "")
    version = data.get("version", "N/A")
    mac_address = data.get("mac_address", "Unknown")
    uptime_sec = data.get("uptime_seconds", 0)

    print(f"\n{yellow}  {'-'*48}{reset}")

    print(f"\n  {cyan}Host:{reset} {hostname}   |   {cyan}Agent:{reset} {agent_id}")
    print(f"  {cyan}Logged in User:{reset} {current_user}   |   {cyan}Timestamp:{reset} {timestamp}")

    print(f"\n  {cyan}CPU:{reset} {cpu_model}")
    print(f"     Name     : {cpu_name}")
    print(f"     Usage     : {cpu_usage}%   ({cores_phys} physical / {cores_log} logical)")
    
    print(f"\n  {cyan}Hardware:{reset} Motherboard (S/N: {motherboard})")
    print(f"     Serial Number     : {serial_no}")
    print(f"     GPU     : {gpu}")
    print(f"     MAC Address : {mac_address}")

    ram_color = red if ram_pct >= 85 else (yellow if ram_pct >= 70 else green)
    print(f"\n  {cyan}RAM:{reset} {ram_avail} GB free / {ram_total} GB total "
          f"({ram_color}{ram_pct}% used{reset})")
    if ram_color == red:
        issues["critical"] += 1
        issues["note"].append(f"[!] Action Required: Clear storage space on Host: {hostname}")
    elif ram_color == yellow:
        issues["warning"] += 1
    print(f"\n  {cyan}Storage ({Style.BRIGHT}Type --> {drive_type}):{reset}")
    for drive in storage:
        use = drive.get("used_percent", 0)
        disk_color = red if use >= 90 else (yellow if use >= 75 else green)
        print(f"     {drive.get('device', 'N/A')}: "
              f"{drive.get('free_gb', 0)} GB free / {drive.get('total_gb', 0)} GB total "
              f"({disk_color}{use}% used{reset})")
        if disk_color == red:
            issues["critical"] += 1
            issues["note"].append(f"[!] Action Required: Free virtual memory of disk on Host: {hostname}")
        elif disk_color == yellow:
            issues["warning"] += 1
    uptime = str(timedelta(seconds=int(uptime_sec)))
    print(f"\n  {cyan}OS:{reset} {platform} {release} (v{version})")
    print(f"     Uptime    : {uptime}")

    return issues

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

def generate_lan_system_report(port=8088):
    target_ips = networkhandler.scan_entire_lan()
    if not target_ips:
        print(f"{Fore.YELLOW}Failed to scan LAN.{Style.RESET_ALL}")
        return
    wait_timeout = len(target_ips) * 2
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
        with open(report_dir, "r", encoding="utf-8") as f:
            data = f.read()
        clean_data = parse_node_block(data)
        print(f"Connected devices on LAN: {len(target_ips)} | Devices responded: {len(clean_data.values())}")
        data = {}
        data["devices"] = []
        data["status"] = [len(target_ips), len(clean_data.values())]
        data["critical"] = 0
        data["security"] = 0
        for i, device in clean_data.items():
            issues = print_clean_report(device)
            if not issues.values():
                print(f"\n  No issues detected for {device["agent_id"]}")
                device["status"] = "HEALTHY"
            else:
                print(f"\n  [{Fore.RED}Critical issues{Style.RESET_ALL} = {issues["critical"]} |{yellow} Warnings {reset}= {issues["warning"]}]")
                device["note"] = issues["note"]
                device["uptime"] = str(timedelta(seconds=int(device.get("uptime_seconds"))))
                device["status"] = "CRITICAL" if issues["critical"] else "WARNING"
                data["critical"] += issues["critical"]
                data["security"] += issues["warning"]
            data["devices"].append(device)
    else:
        print("[-] No responses logged by background listener within the window.")
        print("    Ensure lab agents are alive and firewall rules are active.")
        print("="*50)
        return
    print("\n")
    print("="*50)
    choice = input(f"\n{Fore.GREEN}Generate a PDF on the above report? (y/n): {Style.RESET_ALL}")
    if choice == "y":
        create_lab_report(data=data)
    