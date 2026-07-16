import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor
import os, socket
from colorama import Fore, Style
from utils.logger import log_manager
from utils.execute import clear_shell
from utils.database import save_device, get_device
from utils.settings import load_settings, save_settings

logger = log_manager.get_logger("NetworkHandler")

class NetworkHandler():
    def __init__(self):
        pass

    def ping_ip(self, ip):
        config = load_settings()
        ping_timeout = config["NETWORK"]["ping_timeout"]
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', ping_timeout if ping_timeout else '500', ip]
        response = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ip if response.returncode == 0 else None

    def get_hostname(self, ip):
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

    def change_default_port(self):
        print("\n--- Network Configuration Settings ---")
        config = load_settings()
        current_port = config["NETWORK"]["default_port"]
        print(f"Current active listening port: {Fore.CYAN}{current_port}{Style.RESET_ALL}")
        try:
            new_port_str = input(f"{Fore.GREEN}{Style.BRIGHT}\nEnter new port number (or press Enter to cancel): {Style.RESET_ALL}")
            if not new_port_str.strip():
                print("Port change cancelled.")
                return
            new_port = int(new_port_str)
            if not (1024 <= new_port <= 65535):
                print(f"{Fore.YELLOW}[ERROR] Please choose a safe user port between 1024 and 65535.{Style.RESET_ALL}")
                return
            config["NETWORK"]["default_port"] = new_port
            save_settings(config)
            print(f"[SUCCESS] Default port changed to {new_port}. Restart the server to apply.")
            
        except ValueError:
            print("[ERROR] Invalid input. Port must be a valid integer number.")

    def get_and_save_port(self, ip, start_port=8088, max_attempts=5):
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

    def get_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 0))
            my_ip = s.getsockname()[0]
            return my_ip
        except Exception as e:
            print(f"{Fore.RED}Connection failed. {Style.RESET_ALL}{e}")

    def scan_entire_lan(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            base_ip = ".".join(my_ip.split('.')[:-1])
            s.close()
        except OSError as e:
            print(f"{Fore.RED}Connection failed.{Style.RESET_ALL}")
            logger.error(f"Error connecting to socket: {e}")
            return
        print(f"\n{Fore.CYAN}[SCAN] Your IP: {my_ip}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[SCAN] Scanning LAN: {base_ip}.1 to {base_ip}.254...{Style.RESET_ALL}\n")

        active_devices = []
        ips_to_scan = [f"{base_ip}.{i}" for i in range(1, 255)]
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(self.ping_ip, ips_to_scan)

        for ip in results:
            if ip:
                self.get_and_save_port(ip)
                tag = f"{Fore.YELLOW}(YOU){Fore.RESET}" if ip == my_ip else ""
                print(f"  {Fore.GREEN}{Style.BRIGHT}●{Style.RESET_ALL} {ip.ljust(15)} {tag.ljust(15)} ---> {self.get_hostname(ip).ljust(10)}")
                active_devices.append(ip)

        print(f"\n{Fore.YELLOW}Total Devices Active: {len(active_devices)}{Style.RESET_ALL}")
        return active_devices

    def broadcast_message(self, active_list, msg, port=8088):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for ip in active_list:
            try:
                print(f"-> Sending message to {ip}...")
                s.sendto(msg.encode('utf-8'), (ip, port))
            except Exception as e:
                print(f"{Fore.YELLOW}Failed to send message to {ip}{Style.RESET_ALL}")
                logger.exception(f'Error sending message to {ip}: {e}')
        s.close()

    def broadcast_msg(self, ip, msg, port=8088):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            print(f"-> Sending message to {ip}...")
            s.sendto(msg.encode('utf-8'), (ip, port))
        except Exception as e:
            print(f"{Fore.YELLOW}Failed to send message to {ip}{Style.RESET_ALL}")
            logger.exception(f'Error sending message to {ip}: {e}')
            return
        s.close()

    def sendmsg(self, ip, msg):
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

    def create_message(self, ip):
        if ip:
            message = input(f"{Fore.GREEN}{Style.BRIGHT}\nEnter message: {Style.RESET_ALL}")
            self.broadcast_msg(ip, message)
            print("Broadcast complete!")
            return
        active_ips = self.scan_entire_lan()
        if not active_ips:
            print("No devices found.")
            return
        msg = input(f"{Fore.GREEN}{Style.BRIGHT}\nEnter message to broadcast: {Style.RESET_ALL}")
        self.broadcast_message(active_ips, msg, 8088)
        print("Broadcast complete!")