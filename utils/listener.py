from colorama import Fore, Style
#from utils.logger import log_manager
import socket
from tkinter import Tk, messagebox
import threading
import subprocess

#logger = log_manager.get_logger("PortListener")
ERROR = Fore.RED
WARNING = Fore.YELLOW
RESET = Style.RESET_ALL

def start_listener(port=8088, max_attempts=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(max_attempts):
        current_port = port + i
        try:
            s.bind(('', current_port))
            print(f"Successfully binded to port {current_port}")
            print(f"Agent is listening for messages on port {current_port}...")
            cmd = input("")
            while not cmd:
                data, addr = s.recvfrom(1024)
                msg = data.decode('utf-8')
                if msg == 'SHUTDOWN':
                    print(f"{WARNING}Received remote shutdown signal!")
                    subprocess.run(['shutdown', '/s', '/t', '30'])
                    return
                root = Tk()
                root.withdraw()
                messagebox.showinfo("LAB MANAGER MESSAGE", f"From: {addr}\n\nMessage: {msg}")
                root.destroy()
            s.close()
            return
        except OSError:
            print(f"Port {current_port} is taken, checking next door...")
            continue
    print("[ERROR] Could not find any free ports. Exiting.")
    s.close()

start_listener(8088)