import sqlite3, time
from config import PROJECT_ROOT
from colorama import init, Style, Fore
from utils.check import should_create_files
from utils.logger import log_manager

logger = log_manager.get_logger("Database")
db_path = PROJECT_ROOT / 'lab_manager.db'
init(autoreset=True)
magenta = Fore.MAGENTA
reset = Style.RESET_ALL

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                    ip_address TEXT PRIMARY KEY,
                    hostname TEXT,
                    port_no INTEGER,
                    status TEXT,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    except sqlite3.OperationalError as e:
        print("Failed to initiate database.")
        logger.error(f"Error creating table: {e}")
    conn.commit()
    conn.close()

def save_device(ip, hostname, port_no, status):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO devices (ip_address, hostname, port_no, status)
            VALUES (?, ?, ?, ?)
            ''', (ip, hostname, port_no, status))
    except sqlite3.OperationalError as e:
        print("Failed to insert new values.")
        logger.error(f"Error inserting new device: {e}")
    conn.commit()
    conn.close()

def get_device(ip):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT port_no FROM devices WHERE ip_address = ?
            ''', (ip,))
        result = cursor.fetchone()
        return result
    except sqlite3.OperationalError as e:
        print("Failed to retrieve data.")
        logger.error(f"Error retrieving port: {e}")
        return None
    finally:
        conn.close()

def get_all_saved_devices():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, hostname, port_no, status FROM devices")
    rows = cursor.fetchall()
    conn.close()
    return rows

print(f"\n    {magenta}Inititating database...")
if should_create_files():
    init_db()
time.sleep(.5)