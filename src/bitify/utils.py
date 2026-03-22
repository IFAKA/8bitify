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

CONFIG_DIR = os.path.expanduser("~/.8bitify")
VENV_DIR = os.path.join(CONFIG_DIR, "venv")
MANIFEST_FILE = os.path.join(CONFIG_DIR, ".installed_dependencies")


def get_venv_python():
    """Returns the path to the Python executable inside the managed venv."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def get_venv_bin(name):
    """Returns the path to a binary (e.g. 'demucs') inside the managed venv."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", name + ".exe")
    return os.path.join(VENV_DIR, "bin", name)


def ensure_venv():
    """Creates the managed venv at ~/.8bitify/venv if it doesn't already exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(get_venv_python()):
        logging.info(f"Creating managed venv at {VENV_DIR}")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        logging.info("Venv created successfully.")


def log_installed_dependency(package_name):
    """
    Logs an installed package to the manifest file for safe uninstallation.
    """
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(MANIFEST_FILE, "a") as f:
        f.write(f"{package_name}\n")
    logging.info(f"Logged dependency: {package_name}")


def check_and_install_demucs():
    """
    Checks if demucs is installed in the managed venv.
    If not, creates the venv and installs torch + demucs into it.
    This avoids touching the system/Homebrew Python environment (PEP 668).
    """
    if os.path.exists(get_venv_bin("demucs")):
        logging.info("Demucs already installed in managed venv.")
        return True

    print("--- 8bitify High Quality Mode Setup ---")
    print("AI Source Separation (Demucs) is required but not found.")
    print(f"Setting up a managed environment at: {VENV_DIR}")

    try:
        # Step 1 – create the isolated venv
        ensure_venv()
        venv_python = get_venv_python()

        # Step 2 – upgrade pip inside the venv (quiet)
        subprocess.check_call(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip", "-q"]
        )

        # Step 3 – install torch (CPU-only wheel; much smaller & always available)
        venv_python = get_venv_python()
        try:
            result = subprocess.run(
                [venv_python, "-c", "import torch"],
                capture_output=True
            )
            if result.returncode == 0:
                logging.info("Torch already present in venv.")
            else:
                print("Installing PyTorch (CPU)... (this may take a few minutes)")
                subprocess.check_call([
                    venv_python, "-m", "pip", "install",
                    "torch", "--index-url", "https://download.pytorch.org/whl/cpu",
                    "-q"
                ])
                log_installed_dependency("torch")
        except Exception as e:
            logging.warning(f"Torch check failed, attempting install: {e}")
            subprocess.check_call([
                venv_python, "-m", "pip", "install",
                "torch", "--index-url", "https://download.pytorch.org/whl/cpu",
                "-q"
            ])
            log_installed_dependency("torch")

        # Step 4 – install demucs and torchcodec (needed for audio save)
        print("Installing Demucs...")
        subprocess.check_call([venv_python, "-m", "pip", "install", "demucs", "torchcodec", "-q"])
        log_installed_dependency("demucs")
        log_installed_dependency("torchcodec")

        print("✅ Setup complete! Dependencies installed in managed environment.")
        logging.info("Demucs installed successfully in managed venv.")
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
