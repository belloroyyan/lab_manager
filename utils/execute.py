from utils.logger import log_manager
import subprocess

logger = log_manager.get_logger("ExecuteWrapper")

def execute_task(command, task_name):
    print(f"\n>>> Starting Task: {task_name}")
    logger.info(f"Executing: {' '.join(command) if isinstance(command, list) else command}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        for line in process.stdout:
            print(f"  [STDOUT]: {line.strip()}")
        process.wait()
        if process.returncode == 0:
            logger.info(f"Task '{task_name}' completed successfully.")
            return True
        else:
            error_output = process.stderr.read() if process.stderr else ""
            logger.error(f"Task '{task_name}' failed with code {process.returncode}")
            if error_output:
                logger.error(f"Error Message: {error_output}")
            print(f"\033[91mError in {task_name}! Check the log for details.\033[0m")
            return False
    except Exception as e:
        logger.exception(f"Unexpected crash during task: {task_name}. Error details: {e}")
        return False
    
def execute_file(command, command_type="System"):
    print(f"\n--- Running {command_type} Command ---")
    
    is_list = isinstance(command, list)
    command_str = ' '.join(command) if is_list else command
    print(f"Executing: {command_str}")

    try:
        subprocess.run(command, shell=not is_list, check=True, text=True, capture_output=False)
        print(f"--- {command_type} Command Successful ---")
    except subprocess.CalledProcessError as e:
        print(f"\n!!! {command_type} Execution Failed for command: '{e.cmd}'")
        print(f"Return Code: {e.returncode}")
        logger.error(f"System Check command failed. Error details: {e}")
        return
    except FileNotFoundError as e:
        print(f"!!! Error: Command/Tool not found. Make sure system tools are installed.")
        logger.exception(f"System Tool not available. Error details: {e}")
        return

def clear_shell():
    input("\nPress ENTER key to continue...")
    subprocess.run(["cls"], shell=True)

def clear_shell_wi():
    subprocess.run(["cls"], shell=True)