import os
import sys
import shutil
import subprocess
import platform
import datetime
import traceback
import logging

# Set up logging
logging.basicConfig(
    filename="8bitify_crash.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MANIFEST_FILE = os.path.expanduser("~/.8bitify/.installed_dependencies")
CONFIG_DIR = os.path.expanduser("~/.8bitify")

def log_installed_dependency(package_name):
    """
    Logs an installed package to the manifest file for safe uninstallation.
    """
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    with open(MANIFEST_FILE, "a") as f:
        f.write(f"{package_name}\n")
    logging.info(f"Logged dependency: {package_name}")

def check_and_install_demucs():
    """
    Checks if demucs is installed. If not, installs it and logs it.
    """
    if shutil.which("demucs"):
        logging.info("Demucs already installed.")
        return True

    print("--- 8bitify High Quality Mode Setup ---")
    print("AI Source Separation (Demucs) is required but not found.")
    print("Installing 'demucs' and 'torch' via pip... (This may take a minute)")
    
    try:
        # Check for torch first (heavy dependency)
        try:
            import torch
            logging.info("Torch already installed.")
        except ImportError:
            print("Installing PyTorch...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch"])
            log_installed_dependency("torch")

        print("Installing Demucs...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "demucs"])
        log_installed_dependency("demucs")
        
        print("Setup Complete! Dependencies logged for safe uninstallation.")
        return True
    except subprocess.CalledProcessError as e:
        print_agent_error_report(e, "Dependency Installation")
        return False
    except Exception as e:
        print_agent_error_report(e, "Dependency Installation")
        return False

def print_agent_error_report(exception, stage="Unknown"):
    """
    Prints a standardized error report for AI Agents.
    """
    timestamp = datetime.datetime.now().isoformat()
    os_info = f"{platform.system()} {platform.release()}"
    python_version = sys.version.split()[0]
    
    error_type = type(exception).__name__
    error_msg = str(exception)
    stack_trace = "".join(traceback.format_tb(exception.__traceback__))
    
    # Get last lines of log
    log_context = ""
    if os.path.exists("8bitify_crash.log"):
        with open("8bitify_crash.log", "r") as f:
            log_context = "".join(f.readlines()[-20:])

    report = f"""
--- BITIFY AGENT REPORT ---
[CONTEXT]
Timestamp: {timestamp}
OS: {os_info}
Python: {python_version}
Stage: {stage}

[ERROR]
Type: {error_type}
Message: {error_msg}

[STACK TRACE]
{stack_trace}

[LOGS (Last 20 lines)]
{log_context}
---------------------------
> ACTION REQUIRED: Copy the block above and paste it to your AI Agent to fix this issue.
"""
    print(report, file=sys.stderr)
    logging.error(f"Agent Report Generated for {stage}: {error_msg}")
