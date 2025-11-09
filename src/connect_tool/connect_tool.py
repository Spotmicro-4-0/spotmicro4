#!/usr/bin/env python3
"""
SpotmicroAI Setup Tool
----------------------
Automates initial setup and code deployment to a Raspberry Pi.
Performs full installation or incremental synchronization using rsync.
"""

import argparse
import getpass
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

import labels as LABELS
import connect_tool_labels as TOOL_LABELS

# ------------------------------------------------------------------
# Constants (single source of truth)
# ------------------------------------------------------------------
PROJECT_DIR = "spotmicroai"  # Remote deployment folder
SRC_FOLDER_NAME = "src"  # Local source folder
REMOTE_VENV_DIR = ".venv"  # Virtual environment folder
CONFIG_FILE_NAME = "connect_config.json"  # Local saved setup metadata
SSH_KEY_FILE = "id_rsa"  # Default SSH key file
SSH_CONNECT_TIMEOUT = 30
SSH_OPTS = "-o StrictHostKeyChecking=no"
APT_PACKAGES = (
    "python3 python3-pip python3-venv python3-dev build-essential pkg-config "
    "i2c-tools python3-smbus python3-smbus2 python3-rpi.gpio "
    "python3-numpy python3-scipy libatlas-base-dev python3-rpi.gpio"
)
ENABLE_I2C_CMDS = [
    "sudo raspi-config nonint do_i2c 0",
    "sudo grep -q 'dtparam=i2c_arm=on' /boot/firmware/config.txt "
    "|| echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/firmware/config.txt",
]
RSYNC_EXCLUDES = [
    "*.pyc",
    "*/__pycache__/",
    ".git/",
    ".venv/",
    "*/.venv/",
    "venv/",
    "*/venv/",
    "*.log",
    "logs/",
    ".pytest_cache/",
    ".mypy_cache/",
    "spotmicroai.json",
]
TOTAL_STEPS = 9
VERSION = "SpotmicroAI Setup Tool"
USE_COLORS = True
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB - rotate when log exceeds this size
MAX_LOG_BACKUPS = 3  # Keep up to 3 rotated backups


# ------------------------------------------------------------------
# Console colors
# ------------------------------------------------------------------
class Colors:
    """Console color codes for terminal output."""

    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'


if not USE_COLORS:
    for attr in vars(Colors):
        if not attr.startswith("__"):
            setattr(Colors, attr, "")


# ------------------------------------------------------------------
# Setup Tool
# ------------------------------------------------------------------
class SetupTool:
    """Tool for automating setup and deployment of SpotmicroAI to Raspberry Pi."""

    def __init__(self, args=None):
        """Initialize the setup tool with command line arguments."""
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / CONFIG_FILE_NAME
        self.config = {}
        self.args = args or argparse.Namespace()
        self.current_password = None
        # Setup logging
        self.log_file = self.script_dir / "setup.log"
        self.log_handle = None

    # ------------------------------------------------------------------
    # Printing helpers
    # ------------------------------------------------------------------
    def print_info(self, msg):
        """Print an informational message in green."""
        print(f"{Colors.GREEN}{LABELS.INFO_PREFIX}{Colors.NC} {msg}")

    def print_warn(self, msg):
        """Print a warning message in yellow."""
        print(f"{Colors.YELLOW}{LABELS.WARN_PREFIX}{Colors.NC} {msg}")

    def print_err(self, msg):
        """Print an error message in red."""
        print(f"{Colors.RED}{LABELS.ERROR_PREFIX}{Colors.NC} {msg}")

    def print_step(self, n, msg):
        """Print a step message with step number in blue."""
        prefix = LABELS.STEP_PREFIX.format(n=n, TOTAL_STEPS=TOTAL_STEPS)
        print(f"{Colors.BLUE}{prefix}{Colors.NC} {msg}")

    def print_input(self, msg):
        """Print an input prompt in magenta."""
        print(f"{Colors.MAGENTA}[INPUT]{Colors.NC} {msg}", end=" ", flush=True)

    def _log(self, msg):
        """Write message to log file."""
        try:
            if not self.log_handle:
                self._rotate_log_if_needed()
                self.log_handle = open(self.log_file, "a", encoding="utf-8")
            self.log_handle.write(msg + "\n")
            self.log_handle.flush()
        except Exception as e:
            print(f"{TOOL_LABELS.MSG_LOG_WRITE_FAILED.format(e=e)}", file=sys.stderr)

    def _rotate_log_if_needed(self):
        """Rotate log file if it exceeds MAX_LOG_SIZE."""
        if not self.log_file.exists():
            return

        try:
            if self.log_file.stat().st_size > MAX_LOG_SIZE:
                # Close current handle if open
                if self.log_handle:
                    self.log_handle.close()
                    self.log_handle = None

                # Rotate existing backups: setup.log.2 -> setup.log.3, etc.
                for i in range(MAX_LOG_BACKUPS - 1, 0, -1):
                    old = self.log_file.parent / f"{self.log_file.name}.{i}"
                    new = self.log_file.parent / f"{self.log_file.name}.{i + 1}"
                    if old.exists():
                        if new.exists():
                            new.unlink()
                        old.rename(new)

                # Move current log to setup.log.1
                backup = self.log_file.parent / f"{self.log_file.name}.1"
                if backup.exists():
                    backup.unlink()
                self.log_file.rename(backup)
        except Exception as e:
            print(f"{TOOL_LABELS.MSG_LOG_ROTATE_FAILED.format(e=e)}", file=sys.stderr)

    def _close_log(self):
        """Close the log file."""
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None

    def _hide_cursor(self):
        """Hide the terminal cursor."""
        print("\033[?25l", end="", flush=True)

    def _show_cursor(self):
        """Show the terminal cursor."""
        print("\033[?25h", end="", flush=True)

    # ------------------------------------------------------------------
    # Spinner animation
    # ------------------------------------------------------------------
    def show_spinner(self, process, delay=0.15):
        """Display a spinner while a process is running."""
        spinner_chars = ["⠋", "⠙", "⠸", "⢰", "⣠", "⣄", "⡆", "⠇"]
        while process.poll() is None:
            for char in spinner_chars:
                if process.poll() is not None:
                    break
                print(f"\r{char} ", end="", flush=True)
                time.sleep(delay)
        print("\r      \r", end="", flush=True)

    # ------------------------------------------------------------------
    # Config handling
    # ------------------------------------------------------------------
    def load_config(self):
        """Load configuration from the config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                return True
            except Exception as e:
                self.print_warn(LABELS.ERR_INVALID_CONFIG.format(e=e))
        return False

    def save_config(self):
        """Save current configuration to the config file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            self.print_info(LABELS.MSG_CONFIG_SAVED.format(config_file=self.config_file))
            return True
        except Exception as e:
            self.print_err(LABELS.ERR_SAVE_CONFIG_FAILED.format(e=e))
            return False

    # ------------------------------------------------------------------
    # SSH helpers
    # ------------------------------------------------------------------
    def _ssh_prefix(self):
        """Generate SSH command prefix with authentication."""
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path")
        base = f"ssh -o ConnectTimeout={SSH_CONNECT_TIMEOUT} {SSH_OPTS}"
        return f'{base} -i "{key}" {host}' if key else f"{base} {host}"

    def _scp_prefix(self):
        """Generate SCP command prefix with authentication."""
        key = self.config.get("ssh_key_path")
        return f'scp -i "{key}" {SSH_OPTS}' if key else f"scp {SSH_OPTS}"

    def _run_remote(self, cmd, desc=None, capture=False):
        """Execute a command on the remote Raspberry Pi."""
        if desc:
            self.print_info(desc)
        full = f'{self._ssh_prefix()} "{cmd}"'
        try:
            process = subprocess.Popen(full, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            spinner_thread = threading.Thread(target=self.show_spinner, args=(process,), daemon=True)
            spinner_thread.start()
            stdout, stderr = process.communicate()
            spinner_thread.join(timeout=1)

            # Log output to file
            if stdout:
                self._log(f"[STDOUT] {stdout.strip()}")
            if stderr and process.returncode != 0:
                self._log(f"[STDERR] {stderr.strip()}")

            if process.returncode != 0 and stderr:
                self.print_warn(stderr.strip())
            if capture:
                return stdout.strip() if process.returncode == 0 else None
            return process.returncode == 0
        except Exception as e:
            self.print_err(LABELS.ERR_SSH_COMMAND_FAILED.format(e=e))
            self._log(f"[ERROR] {LABELS.ERR_SSH_COMMAND_FAILED.format(e=e)}")
            return None if capture else False

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------
    def ask(self, prompt, default=None, secret=False):
        """Prompt user for input, optionally with a default value."""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        self.print_input(full_prompt)
        # For secret input, getpass doesn't show a prompt (we already printed it)
        # For regular input, use empty prompt since we already printed it
        val = getpass.getpass("") if secret else input("")
        return val if val else default

    def confirm(self, prompt, default=True):
        """Prompt user for yes/no confirmation."""
        default_str = "Y/n" if default else "y/N"
        full_prompt = f"{prompt} [{default_str}]:"
        self.print_input(full_prompt)
        val = input("").strip().lower()
        if not val:
            return default
        return val in ("y", "yes")

    # ------------------------------------------------------------------
    # Setup steps
    # ------------------------------------------------------------------
    def collect_initial_config(self):
        """Collect initial configuration from user input."""
        self.print_info(LABELS.UI_INITIAL_SETUP_HEADER)
        self.print_info(LABELS.UI_ACCEPT_DEFAULTS)
        hostname = self.ask(LABELS.PROMPT_HOSTNAME, "spotmicroai.local")
        username = self.ask(LABELS.PROMPT_USERNAME, "pi")
        password = self.ask(LABELS.PROMPT_PASSWORD, secret=True)
        if not all([hostname, username, password]):
            self.print_err(LABELS.ERR_MISSING_REQUIRED)
            return False
        self.config = {
            "hostname": hostname,
            "username": username,
            "password_provided": True,
            "setup_completed": False,
        }
        self.current_password = password
        return self.save_config()

    def test_ssh_connection(self):
        """Test SSH connection to the Raspberry Pi."""
        self.print_info(LABELS.SUBSTEP_TESTING_SSH)
        out = self._run_remote('echo "SSH test successful"', capture=True)
        if isinstance(out, str) and "SSH test successful" in out:
            self.print_info(LABELS.MSG_SSH_CONNECTION_VERIFIED)
            return True
        self.print_err(LABELS.ERR_SSH_TEST_FAILED)
        return False

    def generate_ssh_keys(self):
        """Generate SSH key pair for authentication."""
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(exist_ok=True)
        keyfile = ssh_dir / SSH_KEY_FILE
        if keyfile.exists():
            return True
        cmd = f'ssh-keygen -t rsa -b 4096 -f "{keyfile}" -N "" -q'
        ok = subprocess.run(cmd, shell=True, check=False).returncode == 0
        self.print_info(LABELS.MSG_SSH_KEY_GENERATED if ok else LABELS.ERR_SSH_KEY_GEN_FAILED)
        return ok

    def copy_ssh_key_to_pi(self):
        """Copy SSH public key to Raspberry Pi for passwordless authentication."""
        pubkey = Path.home() / ".ssh" / f"{SSH_KEY_FILE}.pub"
        if not pubkey.exists():
            self.print_err(LABELS.ERR_PUBLIC_KEY_NOT_FOUND)
            return False
        with open(pubkey, "r", encoding="utf-8") as f:
            keydata = f.read().strip()
        cmd = (
            f'mkdir -p ~/.ssh && chmod 700 ~/.ssh && '
            f'echo "{keydata}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
        )
        if self._run_remote(cmd, desc=LABELS.SUBSTEP_INSTALLING_SSH_KEY):
            self.print_info(LABELS.MSG_SSH_KEY_INSTALLED)
            self.config["ssh_key_path"] = str(Path.home() / ".ssh" / SSH_KEY_FILE)
            self.current_password = None
            self.save_config()
            return True
        return False

    def perform_system_update(self):
        """Update system packages on the Raspberry Pi."""
        self.print_step(1, LABELS.STEP_SYSTEM_UPDATE)
        cmds = [
            ("sudo apt update", LABELS.SUBSTEP_UPDATING_PACKAGES),
            ("sudo apt upgrade -y", LABELS.SUBSTEP_UPGRADING_PACKAGES),
        ]
        return all(self._run_remote(c, d) for c, d in cmds)

    def enable_i2c(self):
        """Enable I2C interface on the Raspberry Pi."""
        self.print_step(2, LABELS.STEP_ENABLE_I2C)
        return all(self._run_remote(c) for c in ENABLE_I2C_CMDS)

    def create_project_directory(self):
        """Create the project directory on the Raspberry Pi."""
        self.print_step(3, LABELS.STEP_CREATE_PROJECT_DIR)
        out = self._run_remote(f"test -d ~/{PROJECT_DIR} && echo EXISTS || echo NOT_EXISTS", capture=True)
        if out == "EXISTS":
            self.print_warn(LABELS.WARN_EXISTING_DIR_FOUND.format(project_dir=PROJECT_DIR))
            if self.confirm(LABELS.PROMPT_REMOVE_DIR, True):
                self._run_remote(f"rm -rf ~/{PROJECT_DIR}")
            else:
                self.print_err(LABELS.ERR_CANNOT_PROCEED_EXISTING_DIR)
                return False
        return self._run_remote(f"mkdir -p ~/{PROJECT_DIR} && cd ~/{PROJECT_DIR} && pwd")

    def install_python_and_dependencies(self):
        """Install Python and required system dependencies."""
        self.print_step(4, LABELS.STEP_INSTALL_PYTHON_DEPS)
        return self._run_remote(f"sudo apt install -y {APT_PACKAGES}")

    def create_virtual_environment(self):
        """Create and setup Python virtual environment."""
        self.print_step(5, LABELS.STEP_CREATE_VENV)
        cmds = [
            # Create venv with system site packages visible
            f"python3 -m venv --system-site-packages ~/{REMOTE_VENV_DIR}",
            # Activate and upgrade pip inside the venv
            f"source ~/{REMOTE_VENV_DIR}/bin/activate && pip install --upgrade pip",
        ]
        return all(self._run_remote(c) for c in cmds)

    def copy_project_files_initial_setup(self):
        """Copy project files to the Raspberry Pi during initial setup.

        This is part of the complete 9-step setup process. It transfers the spotmicroai/
        folder to ~/spotmicroai on the Pi without additional post-processing.
        """
        self.print_step(6, LABELS.STEP_COPY_FILES)
        src_dir = self.script_dir.parent / PROJECT_DIR
        if not src_dir.exists():
            self.print_err(LABELS.ERR_MISSING_SOURCE_DIR.format(src_dir=src_dir))
            return False
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path", "")
        exclude_args = " ".join([f'--exclude=\"{x}\"' for x in RSYNC_EXCLUDES])
        rsync_cmd = (
            f'rsync -az --delete --quiet {exclude_args} '
            f'-e "ssh -i \'{key}\' {SSH_OPTS}" '
            f'"{src_dir}/" "{host}:~/{PROJECT_DIR}/"'
        )
        self.print_info(LABELS.MSG_TRANSFERRING_FILES)
        result = subprocess.run(
            rsync_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        if result.stdout:
            self._log(f"[RSYNC] {result.stdout.strip()}")
        if result.stderr:
            self._log(f"[RSYNC ERROR] {result.stderr.strip()}")
        if result.returncode == 0:
            self.print_info(LABELS.MSG_FILES_COPIED)
            return True
        self.print_err(LABELS.ERR_FILE_COPY_FAILED)
        return False

    def install_python_packages(self):
        """Install Python packages from requirements.txt (prefer system wheels, no builds)."""
        self.print_step(7, LABELS.STEP_INSTALL_PACKAGES)
        cmd = (
            f"cd ~/{PROJECT_DIR} && "
            f"source ~/{REMOTE_VENV_DIR}/bin/activate && "
            # rely on --system-site-packages venv; avoid source builds
            f"PIP_NO_BUILD_ISOLATION=1 PIP_ONLY_BINARY=:all: "
            f"pip install --no-cache-dir -r requirements.txt"
        )
        return self._run_remote(cmd)

    def _post_deploy_finalize(self):
        """Set executable permissions on shell scripts after deployment."""
        self.print_step(8, LABELS.STEP_FINALIZE)
        self._run_remote(
            f"cd ~/{PROJECT_DIR} && find . -name '*.sh' -exec chmod +x {{}} \\;",
            desc=LABELS.MSG_EXEC_PERMISSIONS_SET,
        )
        return True

    def launch_config_app(self):
        """Launch the configuration application on the Raspberry Pi."""
        self.print_step(9, LABELS.STEP_LAUNCH_APP)
        cmd = f"cd ~/{PROJECT_DIR} && bash spot_config.sh"
        self.print_info(LABELS.MSG_LAUNCHING_CONFIG_APP)
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path")
        base = f"ssh -t -o ConnectTimeout={SSH_CONNECT_TIMEOUT} {SSH_OPTS}"
        ssh_prefix = f'{base} -i "{key}" {host}' if key else f"{base} {host}"
        full = f'{ssh_prefix} "{cmd}" 2>/dev/null'
        try:
            result = subprocess.run(full, shell=True, timeout=3600, check=False)
            return result.returncode == 0
        except Exception as e:
            self.print_err(LABELS.ERR_SSH_COMMAND_FAILED.format(e=e))
            return False

    def sync_code_changes_after_setup(self):
        """Sync code changes to the Raspberry Pi after initial setup is complete.

        This is called when the robot has already been fully configured and we just
        need to deploy updated code. It transfers the spotmicroai/ folder and refreshes
        permissions and the menu app.
        """
        src_dir = self.script_dir.parent / PROJECT_DIR
        if not src_dir.exists():
            self.print_err(LABELS.ERR_SOURCE_DIR_NOT_FOUND.format(src_dir=src_dir))
            return False

        self.print_info(LABELS.MSG_SYNCING_CHANGES)
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path", "")
        exclude_args = " ".join([f'--exclude=\"{x}\"' for x in RSYNC_EXCLUDES])
        rsync_cmd = (
            f'rsync -az --delete --quiet {exclude_args} '
            f'-e "ssh -i \'{key}\' {SSH_OPTS}" '
            f'"{src_dir}/" "{host}:~/{PROJECT_DIR}/"'
        )
        result = subprocess.run(
            rsync_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        if result.stdout:
            self._log(f"[RSYNC] {result.stdout.strip()}")
        if result.stderr:
            self._log(f"[RSYNC ERROR] {result.stderr.strip()}")
        if result.returncode == 0:
            self.print_info(LABELS.MSG_FILES_SYNCED)
            self._post_deploy_finalize()
            if not getattr(self.args, "skip_menu", False):
                return self.launch_config_app()
            return True
        self.print_err(LABELS.ERR_SYNC_FAILED)
        return False

    # ------------------------------------------------------------------
    # Flow control
    # ------------------------------------------------------------------
    def run_complete_setup(self):
        """Execute the complete setup process."""
        steps = [
            (self.perform_system_update, LABELS.STEP_SYSTEM_UPDATE),
            (self.enable_i2c, LABELS.STEP_ENABLE_I2C),
            (self.create_project_directory, LABELS.STEP_CREATE_PROJECT_DIR),
            (self.install_python_and_dependencies, LABELS.STEP_INSTALL_PYTHON_DEPS),
            (self.create_virtual_environment, LABELS.STEP_CREATE_VENV),
            (self.copy_project_files_initial_setup, LABELS.STEP_COPY_FILES),
            (self.install_python_packages, LABELS.STEP_INSTALL_PACKAGES),
            (self._post_deploy_finalize, LABELS.STEP_FINALIZE),
        ]
        # Only add the menu launch step if not skipping
        if not getattr(self.args, "skip_menu", False):
            steps.append((self.launch_config_app, LABELS.STEP_LAUNCH_APP))

        for func, name in steps:
            if not func():
                self.print_err(LABELS.ERR_SETUP_FAILED_AT_STEP.format(name=name))
                return False
        self.config["setup_completed"] = True
        self.save_config()
        self.print_info(LABELS.MSG_SETUP_COMPLETED)
        return True

    def run(self):
        """Main execution flow for the setup tool."""
        try:
            self._hide_cursor()
            if getattr(self.args, "reset", False) and self.config_file.exists():
                self.config_file.unlink()
                self.print_info(LABELS.MSG_CONFIG_CLEARED)

            cfg_exists = self.load_config()
            if not cfg_exists:
                self.print_warn(LABELS.WARN_NO_PREVIOUS_CONFIG)
                if not self.confirm(LABELS.PROMPT_FIRST_TIME_SETUP, True):
                    return False
                if not self.collect_initial_config():
                    return False
                if not self.test_ssh_connection():
                    return False
                if self.confirm(LABELS.PROMPT_SSH_KEY_AUTH, True):
                    if self.generate_ssh_keys():
                        self.copy_ssh_key_to_pi()
            else:
                self.print_info(LABELS.MSG_CONFIG_FOUND)
                if self.config.get("setup_completed"):
                    return self.sync_code_changes_after_setup()
                else:
                    pwd = self.ask(LABELS.PROMPT_PASSWORD, secret=True)
                    self.current_password = pwd

            return self.run_complete_setup()

        except KeyboardInterrupt:
            self.print_warn(LABELS.WARN_INTERRUPTED)
            self._close_log()
            self._show_cursor()
            return False
        except Exception as e:
            self.print_err(LABELS.ERR_UNEXPECTED_ERROR.format(e=e))
            traceback.print_exc()
            self._close_log()
            self._show_cursor()
            return False
        finally:
            self._close_log()
            self._show_cursor()


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
def main():
    """Parse command line arguments and run the setup tool."""
    parser = argparse.ArgumentParser(description=LABELS.CLI_DESCRIPTION)
    parser.add_argument("--reset", action="store_true", help=LABELS.CLI_CLEAN_HELP)
    parser.add_argument("--skip-menu", action="store_true", help="Skip launching the config app UI")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    setup = SetupTool(args)
    ok = setup.run()
    if not ok:
        print(TOOL_LABELS.MSG_LOG_PATH)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
