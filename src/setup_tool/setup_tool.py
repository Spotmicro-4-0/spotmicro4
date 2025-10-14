#!/usr/bin/env python3
"""
SpotmicroAI Setup Tool

This tool handles the initial setup and configuration of the Raspberry Pi for SpotmicroAI.
It guides the user through SSH setup, system configuration, and file deployment.
"""

import argparse
import getpass
import json
import subprocess
import sys
import os
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""

    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class SetupTool:
    """Manages the setup process for SpotmicroAI"""

    def __init__(self, args=None):
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / "setup_config.json"
        self.config = {}
        self.args = args or argparse.Namespace()
        self.current_password = None

    def print_info(self, message):
        """Print info message in green"""
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")

    def print_warning(self, message):
        """Print warning message in yellow"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

    def print_error(self, message):
        """Print error message in red"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

    def print_question(self, message):
        """Print question message in cyan"""
        print(f"{Colors.CYAN}[QUESTION]{Colors.NC} {message}")

    def print_step(self, step_num, total_steps, message):
        """Print step progress"""
        print(f"{Colors.BLUE}[STEP {step_num}/{total_steps}]{Colors.NC} {message}")

    def load_config(self):
        """Load existing configuration if it exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                return True
            except json.JSONDecodeError:
                self.print_warning("Invalid configuration file found")
                return False
            except Exception as e:
                self.print_error(f"Error loading configuration: {e}")
                return False
        return False

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.print_info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.print_error(f"Error saving configuration: {e}")
            return False

    def get_user_input(self, prompt, default=None, sensitive=False):
        """Get user input with optional default value"""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "

        if sensitive:
            value = getpass.getpass(full_prompt)
        else:
            value = input(full_prompt).strip()

        return value if value else default

    def confirm_yes_no(self, prompt, default=True):
        """Get yes/no confirmation from user"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{prompt} [{default_str}]: ").strip().lower()

        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']

    def show_first_time_setup_message(self):
        """Display first-time setup prerequisites"""
        print("\n" + "=" * 70)
        self.print_info("FIRST TIME SETUP DETECTED")
        print("=" * 70)
        print("\n" + Colors.YELLOW + "IMPORTANT PREREQUISITES:" + Colors.NC)
        print("\nBefore proceeding, please ensure your Raspberry Pi has:")
        print("  ✓ A fresh SD card with Raspberry Pi OS installed")
        print("  ✓ SSH enabled (create an empty 'ssh' file in boot partition)")
        print("  ✓ Network connectivity (WiFi or Ethernet)")
        print("  ✓ A known hostname or IP address")
        print("\n" + Colors.CYAN + "If you haven't completed these steps:" + Colors.NC)
        print("  → Please refer to the documentation in the 'docs' folder")
        print("  → Especially check '1.raspberry-pi.md' for setup instructions")
        print("=" * 70)

    def collect_initial_config(self):
        """Collect initial configuration from user"""
        print("\n" + "=" * 60)
        self.print_info("SpotmicroAI Initial Setup Configuration")
        print("=" * 60)

        # Get hostname
        print()
        self.print_question("What is the hostname or IP address of your Raspberry Pi?")
        self.print_info("Examples: spotmicroai.local, raspberrypi.local, 192.168.1.100")
        hostname = self.get_user_input("Hostname/IP", 'spotmicroai.local')

        if not hostname:
            self.print_error("Hostname is required")
            return False

        # Get username
        print()
        self.print_question("What is the username for SSH access?")
        self.print_info("Default Raspberry Pi OS username is 'pi'")
        username = self.get_user_input("Username", 'pi')

        if not username:
            self.print_error("Username is required")
            return False

        # Get password
        print()
        self.print_question("What is the SSH password?")
        password = self.get_user_input("Password", sensitive=True)

        if not password:
            self.print_error("Password is required for initial setup")
            return False

        # Store configuration
        self.config = {
            'hostname': hostname,
            'username': username,
            'password_provided': True,
            'setup_completed': False
        }
        self.current_password = password

        return self.save_config()

    def test_ssh_connection(self):
        """Test SSH connection to verify credentials"""
        hostname = self.config.get('hostname')
        username = self.config.get('username')

        self.print_info(f"Testing SSH connection to {username}@{hostname}...")

        # For Windows, we'll use ssh command
        ssh_cmd = f'echo "SSH test successful" | ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {username}@{hostname} "cat"'

        try:
            if self.current_password and self.check_sshpass_available():
                ssh_cmd = f'sshpass -p "{self.current_password}" ' + ssh_cmd

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, timeout=15, text=True)

            if result.returncode == 0 or "SSH test successful" in result.stdout:
                self.print_info("✓ SSH connection successful!")
                return True
            else:
                self.print_error("✗ SSH connection failed")
                self.print_error(f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.print_error("SSH connection timed out")
            return False
        except Exception as e:
            self.print_error(f"SSH connection test failed: {e}")
            return False

    def check_sshpass_available(self):
        """Check if sshpass is available (for non-Windows systems)"""
        try:
            subprocess.run(['sshpass', '-V'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def setup_ssh_keys(self):
        """Setup SSH key authentication"""
        print("\n" + "=" * 60)
        self.print_info("SSH Key Authentication Setup")
        print("=" * 60)

        ssh_dir = Path.home() / ".ssh"
        ssh_key_path = ssh_dir / "id_rsa"
        ssh_pub_key_path = ssh_dir / "id_rsa.pub"

        # Check for existing SSH keys
        if ssh_key_path.exists() and ssh_pub_key_path.exists():
            print("\n" + Colors.GREEN + "✓ Existing SSH key pair found:" + Colors.NC)
            print(f"  Private key: {ssh_key_path}")
            print(f"  Public key:  {ssh_pub_key_path}")
            
            use_existing = self.confirm_yes_no("\nDo you want to use the existing SSH key pair?", True)
            
            if not use_existing:
                if not self.generate_new_ssh_keys():
                    return False
        else:
            print("\n" + Colors.YELLOW + "✗ No SSH key pair found" + Colors.NC)
            if self.confirm_yes_no("Do you want to generate a new SSH key pair?", True):
                if not self.generate_new_ssh_keys():
                    return False
            else:
                self.print_info("Skipping SSH key generation")
                return True

        # Copy SSH key to Raspberry Pi
        return self.copy_ssh_key_to_pi()

    def generate_new_ssh_keys(self):
        """Generate new SSH key pair"""
        self.print_info("Generating new SSH key pair...")
        
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(exist_ok=True)
        
        # Generate SSH key without passphrase
        keygen_cmd = f'ssh-keygen -t rsa -b 4096 -f "{ssh_dir / "id_rsa"}" -N "" -q'
        
        try:
            result = subprocess.run(keygen_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.print_info("✓ SSH key pair generated successfully")
                return True
            else:
                self.print_error(f"✗ Failed to generate SSH keys: {result.stderr}")
                return False
        except Exception as e:
            self.print_error(f"Error generating SSH keys: {e}")
            return False

    def copy_ssh_key_to_pi(self):
        """Copy SSH public key to Raspberry Pi"""
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        
        self.print_info(f"Copying SSH public key to {username}@{hostname}...")
        
        ssh_pub_key_path = Path.home() / ".ssh" / "id_rsa.pub"
        
        if not ssh_pub_key_path.exists():
            self.print_error("Public key file not found")
            return False

        # Read the public key
        try:
            with open(ssh_pub_key_path, 'r') as f:
                pub_key = f.read().strip()
        except Exception as e:
            self.print_error(f"Failed to read public key: {e}")
            return False

        # Command to add key to authorized_keys on the Pi
        add_key_cmd = f'mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo "{pub_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
        
        if not self.execute_ssh_command(add_key_cmd):
            self.print_error("Failed to copy SSH key to Raspberry Pi")
            return False

        self.print_info("✓ SSH key copied successfully")
        self.print_info("You can now connect without a password!")
        
        # Store SSH key path and clear password for key-based authentication
        ssh_key_path = str(Path.home() / ".ssh" / "id_rsa")
        self.config['ssh_key_path'] = ssh_key_path
        self.current_password = None  # Clear password to use key-based auth
        self.save_config()
        
        return True

    def execute_ssh_command(self, command, interactive=False, show_output=True):
        """Execute a command via SSH on the Raspberry Pi"""
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        ssh_key_path = self.config.get('ssh_key_path')

        # Build SSH command with key if available
        if ssh_key_path:
            ssh_base = f'ssh -i "{ssh_key_path}" -o ConnectTimeout=30 -o StrictHostKeyChecking=no {username}@{hostname}'
        else:
            ssh_base = f'ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no {username}@{hostname}'
        
        if self.current_password:
            # Use echo with pipe for password on Windows
            full_cmd = f'echo {self.current_password} | {ssh_base} "{command}"'
        else:
            full_cmd = f'{ssh_base} "{command}"'

        if show_output:
            self.print_info(f"Executing: {command}")

        try:
            if interactive:
                result = subprocess.run(full_cmd, shell=True, text=True)
                return result.returncode == 0
            else:
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)
                
                if show_output and result.stdout:
                    print(result.stdout)
                
                if result.stderr and "Warning" not in result.stderr:
                    if show_output:
                        print(result.stderr)
                
                return result.returncode == 0

        except subprocess.TimeoutExpired:
            self.print_error("Command timed out")
            return False
        except Exception as e:
            self.print_error(f"Command failed: {e}")
            return False

    def perform_system_update(self):
        """Update Raspberry Pi system packages"""
        print("\n" + "=" * 60)
        self.print_step(1, 8, "Updating Raspberry Pi System")
        print("=" * 60)

        commands = [
            ("sudo apt update", "Updating package list"),
            ("sudo apt upgrade -y", "Upgrading packages (this may take a while)"),
        ]

        for cmd, desc in commands:
            print(f"\n{desc}...")
            if not self.execute_ssh_command(cmd, interactive=False):
                self.print_warning(f"Command may have encountered issues: {cmd}")
                if not self.confirm_yes_no("Continue anyway?", True):
                    return False

        self.print_info("✓ System update completed")
        return True

    def enable_i2c(self):
        """Enable I2C interface on Raspberry Pi"""
        print("\n" + "=" * 60)
        self.print_step(2, 8, "Enabling I2C Interface")
        print("=" * 60)

        self.print_info("Configuring I2C...")
        
        # Enable I2C using raspi-config non-interactive mode
        commands = [
            "sudo raspi-config nonint do_i2c 0",  # 0 = enable
            "sudo grep -q 'dtparam=i2c_arm=on' /boot/firmware/config.txt || echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/firmware/config.txt",
        ]

        for cmd in commands:
            if not self.execute_ssh_command(cmd, show_output=False):
                self.print_warning("I2C configuration command may have issues")

        self.print_info("✓ I2C interface enabled")
        return True

    def create_project_directory(self):
        """Create spotmicroai directory on Raspberry Pi"""
        print("\n" + "=" * 60)
        self.print_step(3, 8, "Creating Project Directory")
        print("=" * 60)

        cmd = "mkdir -p ~/spotmicroai && cd ~/spotmicroai && pwd"
        
        if self.execute_ssh_command(cmd):
            self.print_info("✓ Project directory created: ~/spotmicroai")
            return True
        else:
            self.print_error("Failed to create project directory")
            return False

    def install_python_and_dependencies(self):
        """Install Python, pip, and system dependencies"""
        print("\n" + "=" * 60)
        self.print_step(4, 8, "Installing Python and Dependencies")
        print("=" * 60)

        dependencies = [
            "python3",
            "python3-pip",
            "python3-venv",
            "python3-dev",
            "i2c-tools",
            "python3-smbus",
        ]

        cmd = f"sudo apt install -y {' '.join(dependencies)}"
        
        self.print_info("Installing system packages...")
        if not self.execute_ssh_command(cmd, interactive=False):
            self.print_error("Failed to install system dependencies")
            return False

        self.print_info("✓ Python and dependencies installed")
        return True

    def create_virtual_environment(self):
        """Create Python virtual environment"""
        print("\n" + "=" * 60)
        self.print_step(5, 8, "Creating Python Virtual Environment")
        print("=" * 60)

        commands = [
            "cd ~/spotmicroai && python3 -m venv venv",
            "cd ~/spotmicroai && source venv/bin/activate && pip install --upgrade pip",
        ]

        for cmd in commands:
            if not self.execute_ssh_command(cmd):
                self.print_error("Failed to create virtual environment")
                return False

        self.print_info("✓ Virtual environment created and pip upgraded")
        return True

    def copy_project_files(self):
        """Copy project files from local robot folder to Raspberry Pi"""
        print("\n" + "=" * 60)
        self.print_step(6, 8, "Copying Project Files")
        print("=" * 60)

        # Determine source directory (robot folder)
        robot_dir = self.script_dir.parent / "robot"
        
        if not robot_dir.exists():
            self.print_error(f"Robot directory not found: {robot_dir}")
            return False

        hostname = self.config.get('hostname')
        username = self.config.get('username')
        ssh_key_path = self.config.get('ssh_key_path')
        
        # Use SCP to copy files
        self.print_info(f"Copying files from {robot_dir} to Raspberry Pi...")
        
        # Build scp command - copy directory contents directly (use SSH key if available)
        if ssh_key_path:
            scp_cmd = f'scp -i "{ssh_key_path}" -r -o StrictHostKeyChecking=no {robot_dir}/* {username}@{hostname}:~/spotmicroai/'
        else:
            scp_cmd = f'scp -r -o StrictHostKeyChecking=no {robot_dir}/* {username}@{hostname}:~/spotmicroai/'
        
        try:
            result = subprocess.run(scp_cmd, shell=True, text=True)
            
            if result.returncode == 0:
                self.print_info("✓ Project files copied successfully")
                return True
            else:
                self.print_error("Failed to copy project files")
                return False
                
        except Exception as e:
            self.print_error(f"Error copying files: {e}")
            return False

    def install_python_packages(self):
        """Install Python packages from requirements.txt"""
        print("\n" + "=" * 60)
        self.print_step(7, 8, "Installing Python Packages")
        print("=" * 60)

        self.print_info("Installing packages from requirements.txt...")
        
        cmd = "cd ~/spotmicroai && source venv/bin/activate && pip install -r requirements.txt"
        
        if not self.execute_ssh_command(cmd, interactive=False):
            self.print_error("Failed to install Python packages")
            return False

        self.print_info("✓ Python packages installed")
        return True

    def set_permissions_and_copy_config(self):
        """Set executable permissions and copy config file"""
        print("\n" + "=" * 60)
        self.print_step(8, 8, "Setting Permissions and Copying Config")
        print("=" * 60)

        # Set executable permissions on shell scripts
        self.print_info("Setting executable permissions on scripts...")
        chmod_cmd = "cd ~/spotmicroai && find . -name '*.sh' -exec chmod +x {} \\;"
        
        if not self.execute_ssh_command(chmod_cmd, show_output=False):
            self.print_warning("Some permissions may not have been set")

        # Copy spotmicroai.json to home directory root
        json_file = self.script_dir.parent / "robot" / "spotmicroai.json"
        
        if json_file.exists():
            self.print_info("Copying spotmicroai.json to home directory...")
            
            hostname = self.config.get('hostname')
            username = self.config.get('username')
            ssh_key_path = self.config.get('ssh_key_path')
            
            if ssh_key_path:
                scp_cmd = f'scp -i "{ssh_key_path}" -o StrictHostKeyChecking=no "{json_file}" {username}@{hostname}:~/'
            else:
                scp_cmd = f'scp -o StrictHostKeyChecking=no "{json_file}" {username}@{hostname}:~/'
            
            try:
                result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_info("✓ Config file copied to ~/spotmicroai.json")
                else:
                    self.print_warning("Could not copy config file")
            except Exception as e:
                self.print_warning(f"Error copying config file: {e}")
        else:
            self.print_warning("spotmicroai.json not found in robot directory")

        self.print_info("✓ Permissions set and configuration copied")
        return True

    def sync_code_changes(self):
        """Sync code changes to Raspberry Pi using rsync (for development)"""
        print("\n" + "=" * 60)
        self.print_info("Syncing Code Changes to Raspberry Pi")
        print("=" * 60)

        # Determine source directory (robot folder)
        robot_dir = self.script_dir.parent / "robot"
        
        if not robot_dir.exists():
            self.print_error(f"Robot directory not found: {robot_dir}")
            return False

        hostname = self.config.get('hostname')
        username = self.config.get('username')
        ssh_key_path = self.config.get('ssh_key_path')
        
        self.print_info(f"Syncing files from {robot_dir} to Raspberry Pi...")
        self.print_info("Using rsync to copy only changed files...")
        
        # Build rsync command
        # -a: archive mode (preserves permissions, timestamps, etc.)
        # -v: verbose
        # -z: compress during transfer
        # --delete: delete files on remote that don't exist locally
        # --exclude: exclude certain files/directories
        
        if ssh_key_path:
            rsync_cmd = (
                f'rsync -avz --delete '
                f'--exclude="__pycache__" --exclude="*.pyc" --exclude=".git" '
                f'--exclude="venv" --exclude="*.log" '
                f'-e "ssh -i \'{ssh_key_path}\' -o StrictHostKeyChecking=no" '
                f'{robot_dir}/ {username}@{hostname}:~/spotmicroai/'
            )
        else:
            rsync_cmd = (
                f'rsync -avz --delete '
                f'--exclude="__pycache__" --exclude="*.pyc" --exclude=".git" '
                f'--exclude="venv" --exclude="*.log" '
                f'-e "ssh -o StrictHostKeyChecking=no" '
                f'{robot_dir}/ {username}@{hostname}:~/spotmicroai/'
            )
        
        try:
            self.print_info("Running rsync...")
            result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            
            if result.returncode == 0:
                self.print_info("✓ Files synced successfully")
                
                # Set executable permissions on shell scripts
                self.print_info("Setting executable permissions on scripts...")
                chmod_cmd = "cd ~/spotmicroai && find . -name '*.sh' -exec chmod +x {} \\;"
                self.execute_ssh_command(chmod_cmd, show_output=False)
                
                return True
            else:
                self.print_error("Failed to sync files")
                if result.stderr:
                    print(result.stderr)
                return False
                
        except FileNotFoundError:
            self.print_error("rsync command not found. Please install rsync:")
            self.print_info("  Ubuntu/Debian: sudo apt-get install rsync")
            self.print_info("  macOS: brew install rsync")
            self.print_info("  Windows: Install rsync via WSL or Git Bash")
            return False
        except Exception as e:
            self.print_error(f"Error syncing files: {e}")
            return False

    def run_complete_setup(self):
        """Run the complete setup process"""
        print("\n" + "=" * 70)
        self.print_info("Starting Complete SpotmicroAI Setup")
        print("=" * 70)

        steps = [
            (self.perform_system_update, "System Update"),
            (self.enable_i2c, "Enable I2C"),
            (self.create_project_directory, "Create Project Directory"),
            (self.install_python_and_dependencies, "Install Python & Dependencies"),
            (self.create_virtual_environment, "Create Virtual Environment"),
            (self.copy_project_files, "Copy Project Files"),
            (self.install_python_packages, "Install Python Packages"),
            (self.set_permissions_and_copy_config, "Set Permissions & Copy Config"),
        ]

        for i, (step_func, step_name) in enumerate(steps, 1):
            try:
                if not step_func():
                    self.print_error(f"Setup failed at step: {step_name}")
                    return False
            except Exception as e:
                self.print_error(f"Error during {step_name}: {e}")
                return False

        # Mark setup as completed
        self.config['setup_completed'] = True
        self.save_config()

        print("\n" + "=" * 70)
        self.print_info("✓✓✓ SETUP COMPLETED SUCCESSFULLY! ✓✓✓")
        print("=" * 70)
        print("\nYour SpotmicroAI robot is now configured and ready!")
        print("\nNext steps:")
        print("  1. You can SSH into your Raspberry Pi:")
        print(f"     ssh {self.config.get('username')}@{self.config.get('hostname')}")
        print("  2. Navigate to the project: cd ~/spotmicroai")
        print("  3. Run the robot: ./run.sh")
        print("=" * 70)

        return True

    def run(self):
        """Main setup process"""
        try:
            # Handle --clean option
            if getattr(self.args, 'clean', False):
                if self.config_file.exists():
                    self.config_file.unlink()
                    self.print_info("Configuration cleared")
                else:
                    self.print_info("No existing configuration to clear")

            # Check for existing configuration
            config_exists = self.load_config()

            if not config_exists:
                # First time setup
                self.show_first_time_setup_message()
                
                if not self.confirm_yes_no("\nDo you want to continue with the setup?", True):
                    self.print_info("Setup cancelled")
                    return False

                # Collect initial configuration
                if not self.collect_initial_config():
                    return False

                # Test SSH connection
                if not self.test_ssh_connection():
                    self.print_error("Cannot proceed without SSH connection")
                    return False

                # Setup SSH keys
                print()
                if self.confirm_yes_no("Do you want to setup SSH key authentication?", True):
                    self.setup_ssh_keys()

            else:
                # Configuration exists
                self.print_info("Existing configuration found")
                print(f"  Hostname: {self.config.get('hostname')}")
                print(f"  Username: {self.config.get('username')}")
                
                if self.config.get('setup_completed'):
                    self.print_info("Setup was previously completed")
                    
                    # Check if --deploy flag is used or user wants to sync
                    if getattr(self.args, 'deploy', False):
                        self.print_info("Deploy mode: Syncing code changes...")
                        return self.sync_code_changes()
                    
                    # Ask if user wants to deploy/sync changes
                    print("\nOptions:")
                    print("  1. Sync code changes to Raspberry Pi (recommended for development)")
                    print("  2. Run full setup again")
                    print("  3. Exit")
                    print("  (You can also use --clean to start fresh or --deploy to sync directly)")
                    
                    choice = self.get_user_input("\nSelect option [1/2/3]", default="1")
                    
                    if choice == "1":
                        return self.sync_code_changes()
                    elif choice == "2":
                        self.print_info("Running full setup...")
                        # Continue to full setup below
                    else:
                        self.print_info("Exiting...")
                        return True
                else:
                    # Ask for password for incomplete setup
                    self.print_question("Please enter SSH password to continue")
                    password = self.get_user_input("Password", sensitive=True)
                    if password:
                        self.current_password = password

            # Run complete setup
            return self.run_complete_setup()

        except KeyboardInterrupt:
            print("\n")
            self.print_warning("Setup interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SpotmicroAI Initial Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool will guide you through the initial setup of your SpotmicroAI robot.

Examples:
  %(prog)s              # Run initial setup
  %(prog)s --deploy     # Sync code changes to Pi (for development)
  %(prog)s --clean      # Clear existing config and start fresh
  %(prog)s --version    # Show version information

Prerequisites:
  - Raspberry Pi with fresh Raspberry Pi OS
  - SSH enabled on the Pi
  - Network connectivity
  - Known hostname or IP address
        """,
    )

    parser.add_argument('--clean', action='store_true', help='Clear existing configuration and start fresh')
    parser.add_argument('--deploy', action='store_true', help='Deploy/sync code changes to Raspberry Pi (for development)')
    parser.add_argument('--version', action='version', version='SpotmicroAI Setup Tool v2.0')
    args = parser.parse_args()
    
    setup_tool = SetupTool(args)

    if setup_tool.run():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
