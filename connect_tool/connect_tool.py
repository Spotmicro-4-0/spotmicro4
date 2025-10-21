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
import subprocess
import sys
import traceback
from pathlib import Path

import labels as LABELS

# ------------------------------------------------------------------
# Constants (single source of truth)
# ------------------------------------------------------------------
PROJECT_DIR = "spotmicroai"  # Remote deployment folder
SRC_FOLDER_NAME = "src"  # Local source folder
CONFIG_FILENAME = "spotmicroai.json"  # Project config to copy
REMOTE_VENV_DIR = "venv"  # Virtual environment folder
CONFIG_FILE_NAME = "connect_config.json"  # Local saved setup metadata
SSH_KEY_FILE = "id_rsa"  # Default SSH key file
SSH_CONNECT_TIMEOUT = 30
SSH_OPTS = "-o StrictHostKeyChecking=no"
APT_PACKAGES = "python3 python3-pip python3-venv python3-dev i2c-tools python3-smbus"
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
]
TOTAL_STEPS = 9
VERSION = "SpotmicroAI Setup Tool"
USE_COLORS = True


# ------------------------------------------------------------------
# Console colors
# ------------------------------------------------------------------
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


if not USE_COLORS:
    for attr in vars(Colors):
        if not attr.startswith("__"):
            setattr(Colors, attr, "")


# ------------------------------------------------------------------
# Setup Tool
# ------------------------------------------------------------------
class SetupTool:
    def __init__(self, args=None):
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / CONFIG_FILE_NAME
        self.config = {}
        self.args = args or argparse.Namespace()
        self.current_password = None

    # ------------------------------------------------------------------
    # Printing helpers
    # ------------------------------------------------------------------
    def print_info(self, msg):
        print(f"{Colors.GREEN}{LABELS.INFO_PREFIX}{Colors.NC} {msg}")

    def print_warn(self, msg):
        print(f"{Colors.YELLOW}{LABELS.WARN_PREFIX}{Colors.NC} {msg}")

    def print_err(self, msg):
        print(f"{Colors.RED}{LABELS.ERROR_PREFIX}{Colors.NC} {msg}")

    def print_step(self, n, msg):
        prefix = LABELS.STEP_PREFIX.format(n=n, TOTAL_STEPS=TOTAL_STEPS)
        print(f"{Colors.BLUE}{prefix}{Colors.NC} {msg}")

    # ------------------------------------------------------------------
    # Config handling
    # ------------------------------------------------------------------
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                return True
            except Exception as e:
                self.print_warn(LABELS.ERR_INVALID_CONFIG.format(e=e))
        return False

    def save_config(self):
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
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path")
        base = f"ssh -o ConnectTimeout={SSH_CONNECT_TIMEOUT} {SSH_OPTS}"
        return f'{base} -i "{key}" {host}' if key else f"{base} {host}"

    def _scp_prefix(self):
        key = self.config.get("ssh_key_path")
        return f'scp -i "{key}" {SSH_OPTS}' if key else f"scp {SSH_OPTS}"

    def _run_remote(self, cmd, desc=None, capture=False):
        if desc:
            self.print_info(desc)
        full = f'{self._ssh_prefix()} "{cmd}"'
        try:
            result = subprocess.run(full, shell=True, capture_output=capture, text=True, timeout=300, check=False)
            if result.returncode != 0 and result.stderr:
                self.print_warn(result.stderr.strip())
            if capture:
                return result.stdout.strip() if result.returncode == 0 else None
            return result.returncode == 0
        except Exception as e:
            self.print_err(LABELS.ERR_SSH_COMMAND_FAILED.format(e=e))
            return None if capture else False

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------
    def ask(self, prompt, default=None, secret=False):
        p = f"{prompt} [{default}]: " if default else f"{prompt}: "
        val = getpass.getpass(p) if secret else input(p).strip()
        return val or default

    def confirm(self, prompt, default=True):
        default_str = "Y/n" if default else "y/N"
        val = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not val:
            return default
        return val in ("y", "yes")

    # ------------------------------------------------------------------
    # Setup steps
    # ------------------------------------------------------------------
    def collect_initial_config(self):
        print("\n" + LABELS.UI_SEPARATOR)
        self.print_info(LABELS.UI_INITIAL_SETUP_HEADER)
        print(LABELS.UI_SEPARATOR)
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
        self.print_info(LABELS.SUBSTEP_TESTING_SSH)
        out = self._run_remote('echo "SSH test successful"', capture=True)
        if isinstance(out, str) and "SSH test successful" in out:
            self.print_info(LABELS.MSG_SSH_CONNECTION_VERIFIED)
            return True
        self.print_err(LABELS.ERR_SSH_TEST_FAILED)
        return False

    def generate_ssh_keys(self):
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
        self.print_step(1, LABELS.STEP_SYSTEM_UPDATE)
        cmds = [
            ("sudo apt update", LABELS.SUBSTEP_UPDATING_PACKAGES),
            ("sudo apt upgrade -y", LABELS.SUBSTEP_UPGRADING_PACKAGES),
        ]
        return all(self._run_remote(c, d) for c, d in cmds)

    def enable_i2c(self):
        self.print_step(2, LABELS.STEP_ENABLE_I2C)
        return all(self._run_remote(c) for c in ENABLE_I2C_CMDS)

    def create_project_directory(self):
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
        self.print_step(4, LABELS.STEP_INSTALL_PYTHON_DEPS)
        return self._run_remote(f"sudo apt install -y {APT_PACKAGES}")

    def create_virtual_environment(self):
        self.print_step(5, LABELS.STEP_CREATE_VENV)
        cmds = [
            f"cd ~/{PROJECT_DIR} && python3 -m venv {REMOTE_VENV_DIR}",
            f"cd ~/{PROJECT_DIR} && source {REMOTE_VENV_DIR}/bin/activate && pip install --upgrade pip",
        ]
        return all(self._run_remote(c) for c in cmds)

    def copy_project_files(self):
        self.print_step(6, LABELS.STEP_COPY_FILES)
        src_dir = self.script_dir.parent / SRC_FOLDER_NAME
        if not src_dir.exists():
            self.print_err(LABELS.ERR_MISSING_SOURCE_DIR.format(src_dir=src_dir))
            return False
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path", "")
        exclude_args = " ".join([f'--exclude=\"{x}\"' for x in RSYNC_EXCLUDES])
        rsync_cmd = (
            f'rsync -avz --delete {exclude_args} '
            f'-e "ssh -i \'{key}\' {SSH_OPTS}" '
            f'"{src_dir}/" "{host}:~/{PROJECT_DIR}/"'
        )
        self.print_info(LABELS.MSG_TRANSFERRING_FILES)
        result = subprocess.run(rsync_cmd, shell=True, check=False)
        if result.returncode == 0:
            self.print_info(LABELS.MSG_FILES_COPIED)
            return True
        self.print_err(LABELS.ERR_FILE_COPY_FAILED)
        return False

    def install_python_packages(self):
        self.print_step(7, LABELS.STEP_INSTALL_PACKAGES)
        return self._run_remote(
            f"cd ~/{PROJECT_DIR} && source {REMOTE_VENV_DIR}/bin/activate && pip install -r requirements.txt"
        )

    def _post_deploy_finalize(self):
        self._run_remote(
            f"cd ~/{PROJECT_DIR} && find . -name '*.sh' -exec chmod +x {{}} \\;",
            desc=LABELS.MSG_EXEC_PERMISSIONS_SET,
        )
        json_file = self.script_dir.parent / SRC_FOLDER_NAME / CONFIG_FILENAME
        if json_file.exists():
            scp_cmd = f'{self._scp_prefix()} "{json_file}" {self.config["username"]}@{self.config["hostname"]}:~/'
            subprocess.run(scp_cmd, shell=True, check=False)
            self.print_info(LABELS.MSG_CONFIG_FILE_COPIED)
        else:
            self.print_warn(LABELS.WARN_CONFIG_FILE_NOT_FOUND.format(config_filename=CONFIG_FILENAME))

    def set_permissions_and_copy_config(self):
        self.print_step(8, LABELS.STEP_FINALIZE)
        self._post_deploy_finalize()
        return True

    def launch_setup_app(self):
        self.print_step(9, LABELS.STEP_LAUNCH_APP)
        cmd = f"cd ~/{PROJECT_DIR} && bash setup_app.sh"
        self.print_info(LABELS.MSG_LAUNCHING_SETUP_APP)
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path")
        base = f"ssh -t -o ConnectTimeout={SSH_CONNECT_TIMEOUT} {SSH_OPTS}"
        ssh_prefix = f'{base} -i "{key}" {host}' if key else f"{base} {host}"
        full = f'{ssh_prefix} "{cmd}"'
        try:
            result = subprocess.run(full, shell=True, timeout=3600, check=False)
            return result.returncode == 0
        except Exception as e:
            self.print_err(LABELS.ERR_SSH_COMMAND_FAILED.format(e=e))
            return False

    def sync_code_changes(self):
        src_dir = self.script_dir.parent / SRC_FOLDER_NAME
        if not src_dir.exists():
            self.print_err(LABELS.ERR_SOURCE_DIR_NOT_FOUND.format(src_dir=src_dir))
            return False
        host = f"{self.config['username']}@{self.config['hostname']}"
        key = self.config.get("ssh_key_path", "")
        exclude_args = " ".join([f'--exclude=\"{x}\"' for x in RSYNC_EXCLUDES])
        rsync_cmd = (
            f'rsync -avz --delete {exclude_args} '
            f'-e "ssh -i \'{key}\' {SSH_OPTS}" '
            f'"{src_dir}/" "{host}:~/{PROJECT_DIR}/"'
        )
        result = subprocess.run(rsync_cmd, shell=True, check=False)
        if result.returncode == 0:
            self.print_info(LABELS.MSG_FILES_SYNCED)
            self._post_deploy_finalize()
            return self.launch_setup_app()
        self.print_err(LABELS.ERR_SYNC_FAILED)
        return False

    # ------------------------------------------------------------------
    # Flow control
    # ------------------------------------------------------------------
    def run_complete_setup(self):
        steps = [
            (self.perform_system_update, LABELS.STEP_SYSTEM_UPDATE),
            (self.enable_i2c, LABELS.STEP_ENABLE_I2C),
            (self.create_project_directory, LABELS.STEP_CREATE_PROJECT_DIR),
            (self.install_python_and_dependencies, LABELS.STEP_INSTALL_PYTHON_DEPS),
            (self.create_virtual_environment, LABELS.STEP_CREATE_VENV),
            (self.copy_project_files, LABELS.STEP_COPY_FILES),
            (self.install_python_packages, LABELS.STEP_INSTALL_PACKAGES),
            (self.set_permissions_and_copy_config, LABELS.STEP_FINALIZE),
            (self.launch_setup_app, LABELS.STEP_LAUNCH_APP),
        ]
        for func, name in steps:
            if not func():
                self.print_err(LABELS.ERR_SETUP_FAILED_AT_STEP.format(name=name))
                return False
        self.config["setup_completed"] = True
        self.save_config()
        self.print_info(LABELS.MSG_SETUP_COMPLETED)
        return True

    def run(self):
        try:
            if getattr(self.args, "clean", False) and self.config_file.exists():
                self.config_file.unlink()
                self.print_info(LABELS.MSG_CONFIG_CLEARED)

            cfg_exists = self.load_config()
            if not cfg_exists:
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
                    self.print_info(LABELS.MSG_SYNCING_CHANGES)
                    return self.sync_code_changes()
                else:
                    pwd = self.ask(LABELS.PROMPT_PASSWORD, secret=True)
                    self.current_password = pwd

            return self.run_complete_setup()

        except KeyboardInterrupt:
            self.print_warn(LABELS.WARN_INTERRUPTED)
            return False
        except Exception as e:
            self.print_err(LABELS.ERR_UNEXPECTED_ERROR.format(e=e))
            traceback.print_exc()
            return False


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=LABELS.CLI_DESCRIPTION)
    parser.add_argument("--clean", action="store_true", help=LABELS.CLI_CLEAN_HELP)
    parser.add_argument("--deploy", action="store_true", help=LABELS.CLI_DEPLOY_HELP)
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()
    setup = SetupTool(args)
    ok = setup.sync_code_changes() if args.deploy else setup.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
