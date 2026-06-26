import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor
import os, socket
from colorama import Fore, Style
from utils.logger import log_manager
from utils.execute import clear_shell
from utils.database import save_device, get_device

logger = log_manager.get_logger("NetworkManager")

def ping_ip(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '500', ip]
    response = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ip if response.returncode == 0 else None

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        try:
            output = subprocess.check_output(['nbtstat', '-A', ip], 
                                           stderr=subprocess.DEVNULL, 
                                           universal_newlines=True)
            for line in output.splitlines():
                if "<00>" in line and "GROUP" not in line:
                    return line.split()[0].strip()
        except:
            return "Unknown Device"
    return "Unknown Device"

def get_and_save_port(ip, start_port=8088, max_attempts=5):
    found_port = None
    for i in range(max_attempts):
        current_port = start_port + i
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(.2)
        res = s.connect_ex((ip, current_port))
        if res == 0:
            logger.info(f"Successfully found {ip} on {current_port}")
            found_port = current_port
            s.close()
            break
        s.close()
    save_device(ip, f'Device-{ip.split('.')[-1]}', found_port, 'ONLINE')
    logger.info(f"Saved {ip} with port {found_port} to database.")

def scan_entire_lan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
        base_ip = ".".join(my_ip.split('.')[:-1])
        s.close()
    except OSError as e:
        print(f"{Fore.RED}Connection failed.{Style.RESET_ALL}")
        logger.error(f"Error connecting to socket: {e}")
        clear_shell()
        return
    print(f"\n{Fore.CYAN}[SCAN] Your IP: {my_ip}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[SCAN] Scanning LAN: {base_ip}.1 to {base_ip}.254...{Style.RESET_ALL}\n")

    active_devices = []
    ips_to_scan = [f"{base_ip}.{i}" for i in range(1, 255)]
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(ping_ip, ips_to_scan)

    for ip in results:
        if ip:
            get_and_save_port(ip)
            tag = f"{Fore.YELLOW}(YOU){Fore.RESET}" if ip == my_ip else ""
            print(f"  {Fore.GREEN}●{Style.RESET_ALL} {ip.ljust(15)} {tag.ljust(15)} ---> {get_hostname(ip).ljust(10)}")
            active_devices.append(ip)

    print(f"\n{Fore.YELLOW}Total Devices Active: {len(active_devices)}{Style.RESET_ALL}")
    return active_devices

def broadcast_message(active_list, msg, port=8088):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for ip in active_list:
        try:
            print(f"Sending message to {ip}...")
            s.sendto(msg.encode('utf-8'), (ip, port))
        except Exception as e:
            print(f"{Fore.YELLOW}Failed to send message to {ip}: {e}{Style.RESET_ALL}")
            logger.exception(f'Error sending message to {ip}: {e}')
    s.close()

def broadcast_msg(ip, msg, port=8088):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        print(f"Sending message to {ip}...")
        s.sendto(msg.encode('utf-8'), (ip, port))
    except Exception as e:
        print(f"{Fore.YELLOW}Failed to send message to {ip}{Style.RESET_ALL}")
        logger.exception(f'Error sending message to {ip}: {e}')
        return
    s.close()

def sendmsg(ip, msg):
    res = get_device(ip)
    if res is None:
        print(f"{Fore.YELLOW} No port configuration found for {ip} in database. Run a scan first!{Style.RESET_ALL}")
        return
    assigned_port = res[0]
    print(f"[DATABASE] Retrieved Port {assigned_port} for target {ip}")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        print(f"Sending message to {ip}...")
        s.sendto(msg.encode('utf-8'), (ip, assigned_port))
        print(f"Sent message to {ip}:{assigned_port}")
    except Exception as e:
        print(f"{Fore.YELLOW}Failed to send message to {ip}{Style.RESET_ALL}")
        logger.exception(f'Error sending message to {ip}: {e}')
        return
    finally:
        s.close()

def create_message(ip):
    if ip:
        message = input(f"{Fore.GREEN}\nEnter message: {Style.RESET_ALL}")
        broadcast_msg(ip, message)
        print("Broadcast complete!")
        return
    active_ips = scan_entire_lan()
    if not active_ips:
        print("No devices found.")
        return
    print(active_ips)
    msg = input(f"{Fore.GREEN}\nEnter message to broadcast: {Style.RESET_ALL}")
    for ip in active_ips:
        #sendmsg(ip, msg)
        broadcast_message(active_ips, msg, 8088)
    print("Broadcast complete!")