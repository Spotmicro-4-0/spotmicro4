#!/usr/bin/env python3
"""
SpotMicroAI Deployment Script

This script handles the deployment configuration and SSH connection to the Raspberry Pi.
It prompts the user for necessary information and persists the configuration locally.
"""

import json
import os
import sys
import getpass
import subprocess
import argparse
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class DeploymentManager:
    """Manages the deployment process for SpotMicroAI"""
    
    def __init__(self, args=None):
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / "deployment_config.json"
        self.config = {}
        self.args = args or argparse.Namespace()
        
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
        
    def load_config(self):
        """Load existing configuration if it exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.print_info("Loaded existing configuration")
                return True
            except json.JSONDecodeError:
                self.print_warning("Invalid configuration file found, will create new one")
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
        # Check if --yes-all flag is set
        if getattr(self.args, 'yes_all', False):
            self.print_info(f"Auto-confirming: {prompt} (--yes-all flag)")
            return True
            
        default_str = "Y/n" if default else "y/N"
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
        
    def check_ssh_available(self):
        """Check if SSH client is available"""
        try:
            subprocess.run(['ssh', '-V'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
            
    def test_ssh_connection(self, hostname, username, password=None):
        """Test SSH connection to the Raspberry Pi"""
        self.print_info(f"Testing SSH connection to {username}@{hostname}...")
        
        # Create SSH command
        ssh_cmd = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 
                   f'{username}@{hostname}', 'echo "SSH connection successful"']
        
        try:
            # Try SSH connection without password first (key-based auth)
            result = subprocess.run(ssh_cmd, capture_output=True, timeout=15)
            
            if result.returncode == 0:
                self.print_info("SSH connection successful (key-based authentication)")
                return True
            else:
                self.print_warning("Key-based SSH authentication failed")
                if password:
                    self.print_info("Password-based authentication will be attempted during deployment")
                    return True
                else:
                    self.print_error("SSH connection failed and no password provided")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.print_error("SSH connection timed out")
            return False
        except Exception as e:
            self.print_error(f"SSH connection test failed: {e}")
            return False
            
    def collect_deployment_info(self):
        """Collect deployment information from user"""
        print("\n" + "="*60)
        self.print_info("SpotMicroAI Deployment Configuration")
        print("="*60)
        
        # Handle --clean option
        if getattr(self.args, 'clean', False):
            if self.config_file.exists():
                self.config_file.unlink()
                self.print_info("Existing configuration cleared")
            else:
                self.print_info("No existing configuration to clear")
        
        # Check if we have existing config
        config_exists = self.load_config()
        
        if config_exists:
            print("\nExisting configuration found:")
            print(f"  RPI WiFi Configured: {self.config.get('rpi_wifi_configured', 'Not set')}")
            print(f"  Hostname: {self.config.get('hostname', 'Not set')}")
            print(f"  Username: {self.config.get('username', 'Not set')}")
            print()
            
            # Handle -y option for auto-accept
            use_existing = getattr(self.args, 'yes', False)
            if not use_existing:
                use_existing = self.confirm_yes_no("Do you want to use the existing configuration?", True)
            else:
                self.print_info("Auto-accepting existing configuration (-y flag)")
                
            if use_existing:
                # Ask for password again since we don't store it
                if self.config.get('password_provided', False):
                    print()
                    self.print_question("Please enter the SSH password:")
                    password = self.get_user_input("Password", sensitive=True)
                    if password:
                        self.current_password = password
                return True
                
        print("\n" + "-"*40)
        self.print_info("Please provide the following information:")
        print("-"*40)
        
        # Ask about RPI WiFi configuration
        self.print_question("Is your Raspberry Pi configured and running on WiFi?")
        self.print_info("Valid answers: yes, y, no, n")
        rpi_wifi_configured = self.confirm_yes_no("RPI WiFi configured", 
                                                 self.config.get('rpi_wifi_configured', True))
        
        if not rpi_wifi_configured:
            self.print_error("Please configure your Raspberry Pi with WiFi first")
            self.print_info("Refer to the documentation for WiFi setup instructions")
            return False
            
        # Get hostname
        print()
        self.print_question("What is the hostname or IP address of your Raspberry Pi?")
        self.print_info("Examples: spotmicroai, spotmicroai.local, 192.168.1.100, 10.0.0.50")
        hostname = self.get_user_input("Hostname/IP", 
                                     self.config.get('hostname', 'spotmicroai'))
        
        if not hostname:
            self.print_error("Hostname is required")
            return False
            
        # Get username
        print()
        self.print_question("What is the username for SSH access to the Raspberry Pi?")
        self.print_info("Common usernames: pi, ubuntu, spotmicro")
        username = self.get_user_input("Username", 
                                     self.config.get('username', 'pi'))
        
        if not username:
            self.print_error("Username is required")
            return False
            
        # Get password (optional if using key-based auth)
        print()
        self.print_question("What is the password for SSH access?")
        self.print_info("(Leave blank if using SSH key-based authentication)")
        password = self.get_user_input("Password", sensitive=True)
        
        # Store configuration
        self.config.update({
            'rpi_wifi_configured': rpi_wifi_configured,
            'hostname': hostname,
            'username': username,
            'password_provided': bool(password)
        })
        
        # Don't store the actual password in the config file for security
        if password:
            self.current_password = password
        
        return self.save_config()
        
    def establish_ssh_connection(self):
        """Establish SSH connection to the Raspberry Pi"""
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        password = getattr(self, 'current_password', None)
        
        self.print_info(f"Establishing SSH connection to {username}@{hostname}...")
        
        # For now, we'll prepare the SSH command that can be used
        # In a full implementation, you might want to use paramiko for programmatic SSH
        ssh_cmd = f"ssh {username}@{hostname}"
        
        self.print_info(f"SSH command: {ssh_cmd}")
        
        if password:
            self.print_info("Password-based authentication will be used")
            # Note: For automated password-based SSH, you'd typically use sshpass
            # or a Python library like paramiko
        else:
            self.print_info("Key-based authentication will be used")
            
        return True
        
    def get_deployment_action(self):
        """Ask user what deployment action they want to perform"""
        print("\n" + "="*60)
        self.print_info("Deployment Action Selection")
        print("="*60)
        
        actions = {
            '1': {
                'name': 'Initial Setup',
                'description': 'First-time setup: install dependencies, configure system'
            },
            '2': {
                'name': 'Sync Files Only',
                'description': 'Transfer only changed files to RPI (auto-deletes removed files)'
            },
            '3': {
                'name': 'Full Deployment',
                'description': 'Complete deployment: sync files + restart services'
            },
            '4': {
                'name': 'System Update',
                'description': 'Update RPI system (apt update & upgrade)'
            },
            '5': {
                'name': 'Setup SSH Keys',
                'description': 'Configure passwordless SSH authentication'
            },
            '6': {
                'name': 'Clean Remote Files',
                'description': 'Remove files/directories on RPI'
            },
            '7': {
                'name': 'Setup System Service',
                'description': 'Install SpotMicroAI as systemctl service'
            },
            '8': {
                'name': 'View System Status',
                'description': 'Check RPI status, disk space, services'
            },
            '9': {
                'name': 'Custom Actions',
                'description': 'Advanced: choose multiple specific actions'
            }
        }
        
        print("\nAvailable deployment actions:")
        for key, action in actions.items():
            print(f"  {key}. {action['name']}")
            print(f"     {action['description']}")
        
        print("\nOther options:")
        print("  q. Quit without deploying")
        
        while True:
            choice = input(f"\nSelect an action [1-9, q]: ").strip().lower()
            
            if choice == 'q':
                self.print_info("Deployment cancelled by user")
                return None
            elif choice in actions:
                selected_action = actions[choice]
                self.print_info(f"Selected: {selected_action['name']}")
                return choice
            else:
                self.print_error("Invalid choice. Please select 1-9 or q to quit.")
    
    def check_sshpass_available(self):
        """Check if sshpass is available for password-based SSH"""
        try:
            subprocess.run(['sshpass', '-V'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def setup_ssh_key(self):
        """Set up SSH key-based authentication"""
        self.print_info("Setting up SSH key-based authentication...")
        
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        
        # Check if SSH key already exists
        ssh_key_path = Path.home() / ".ssh" / "id_rsa"
        if not ssh_key_path.exists():
            self.print_info("No SSH key found. Generating new SSH key...")
            if self.confirm_yes_no("Generate SSH key pair?", True):
                key_gen_cmd = ['ssh-keygen', '-t', 'rsa', '-b', '2048', '-f', str(ssh_key_path), '-N', '']
                try:
                    subprocess.run(key_gen_cmd, check=True)
                    self.print_info("SSH key generated successfully")
                except subprocess.CalledProcessError:
                    self.print_error("Failed to generate SSH key")
                    return False
            else:
                self.print_info("SSH key generation skipped")
                return False
        
        # Copy SSH key to remote host
        self.print_info("Copying SSH key to Raspberry Pi...")
        password = getattr(self, 'current_password', None)
        
        if password and self.check_sshpass_available():
            # Use sshpass to automate password entry
            ssh_copy_cmd = [
                'sshpass', '-p', password,
                'ssh-copy-id', '-o', 'StrictHostKeyChecking=no',
                f'{username}@{hostname}'
            ]
        else:
            # Manual password entry
            ssh_copy_cmd = ['ssh-copy-id', f'{username}@{hostname}']
            self.print_info("You will be prompted for the password to copy the SSH key")
        
        try:
            result = subprocess.run(ssh_copy_cmd, timeout=60)
            if result.returncode == 0:
                self.print_info("SSH key copied successfully")
                self.print_info("Future connections will use key-based authentication")
                return True
            else:
                self.print_error("Failed to copy SSH key")
                return False
        except subprocess.TimeoutExpired:
            self.print_error("SSH key copy timed out")
            return False
        except Exception as e:
            self.print_error(f"SSH key copy failed: {e}")
            return False
    
    def check_rsync_available(self):
        """Check if rsync is available for file transfer"""
        try:
            subprocess.run(['rsync', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_project_files(self):
        """Get list of project files to transfer"""
        project_root = self.script_dir.parent  # Go up from deployment/ to src/
        
        # Files and directories to include in the spotmicroai folder
        include_patterns = [
            'spotmicroai/',
            'calibration/',
            'integration_tests/',
            '*.py',
            '*.json',
            '*.sh',
            'README.md'
        ]
        
        # Files and directories to exclude
        exclude_patterns = [
            '__pycache__/',
            '*.pyc',
            '*.pyo',
            '.git/',
            '.vscode/',
            'deployment/',       # Don't sync deployment scripts to RPI
            'utilities/',        # Don't sync utilities folder to RPI
            '*.log',
            'deployment_config.json'
        ]
        
        return include_patterns, exclude_patterns
    
    def execute_ssh_command(self, command, interactive=False):
        """Execute a command via SSH on the Raspberry Pi"""
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        password = getattr(self, 'current_password', None)
        
        # Build SSH command
        if password and self.check_sshpass_available() and not interactive:
            # Use sshpass for non-interactive commands with password
            ssh_cmd = [
                'sshpass', '-p', password,
                'ssh',
                '-o', 'ConnectTimeout=30',
                '-o', 'StrictHostKeyChecking=no',
                f'{username}@{hostname}',
                command
            ]
        else:
            # Standard SSH (may prompt for password or use keys)
            ssh_cmd = [
                'ssh',
                '-o', 'ConnectTimeout=30',
                f'{username}@{hostname}',
                command
            ]
        
        self.print_info(f"Executing on RPI: {command}")
        
        try:
            if interactive:
                # For interactive commands, don't capture output
                result = subprocess.run(ssh_cmd, timeout=300)
                return result.returncode == 0
            else:
                # For non-interactive commands, capture output
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
                
                if result.stdout:
                    print("Output:", result.stdout.strip())
                if result.stderr:
                    print("Error:", result.stderr.strip())
                    
                return result.returncode == 0
                
        except subprocess.TimeoutExpired:
            self.print_error("SSH command timed out")
            return False
        except Exception as e:
            self.print_error(f"SSH command failed: {e}")
            return False
    
    def execute_rsync(self, rsync_cmd):
        """Execute rsync command with progress display"""
        password = getattr(self, 'current_password', None)
        
        # Modify rsync command to use sshpass if available and password provided
        if password and self.check_sshpass_available():
            # Insert sshpass into the rsync command
            ssh_command = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no"
            rsync_cmd.insert(1, '-e')  # Add -e flag for custom SSH command
            rsync_cmd.insert(2, ssh_command)  # Add the sshpass SSH command
        
        try:
            self.print_info("Starting file transfer...")
            
            # Execute rsync
            result = subprocess.run(rsync_cmd, text=True, timeout=600)
            
            if result.returncode == 0:
                self.print_info("File transfer completed successfully")
                return True
            else:
                self.print_error(f"File transfer failed with exit code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self.print_error("File transfer timed out")
            return False
        except Exception as e:
            self.print_error(f"File transfer failed: {e}")
            return False
    
    def perform_initial_setup(self):
        """Perform initial setup on the Raspberry Pi"""
        self.print_info("Starting initial setup on Raspberry Pi...")
        
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        
        setup_commands = [
            # Update system first
            "sudo apt update",
            "sudo apt upgrade -y",
            # Install Python dependencies and venv
            "sudo apt install -y python3-pip python3-venv git",
            # Create project directory
            "mkdir -p ~/spotmicroai",
        ]
        
        self.print_info("Initial setup commands to run on RPI:")
        for i, cmd in enumerate(setup_commands, 1):
            print(f"  {i}. {cmd}")
        
        if not self.confirm_yes_no("Execute initial setup commands?", True):
            self.print_info("Initial setup skipped")
            return True
            
        # Execute setup commands
        success = True
        for i, cmd in enumerate(setup_commands, 1):
            self.print_info(f"Step {i}/{len(setup_commands)}: Running setup command...")
            if not self.execute_ssh_command(cmd, interactive=True):
                self.print_error(f"Setup command {i} failed")
                success = False
                if not self.confirm_yes_no("Continue with remaining setup steps?", False):
                    break
        
        if not success:
            self.print_warning("Basic setup completed with some errors")
            return False
        
        # Set up Python virtual environment
        if not self.setup_python_venv():
            self.print_error("Virtual environment setup failed")
            return False
        
        # Install Python packages
        if not self.install_python_packages():
            self.print_error("Package installation failed")
            return False
        
        # Set executable permissions
        if not self.set_executable_permissions():
            self.print_warning("Failed to set some executable permissions")
        
        # Optionally set up systemctl service
        print()
        if self.confirm_yes_no("Set up SpotMicroAI as a system service?", False):
            if not self.setup_systemctl_service():
                self.print_warning("Service setup failed")
                    
        self.print_info("Initial setup completed successfully")
        return True
    
    def perform_system_update(self):
        """Perform system update on the Raspberry Pi"""
        self.print_info("Performing system update on Raspberry Pi...")
        
        update_commands = [
            "sudo apt update",
            "sudo apt upgrade -y"
        ]
        
        self.print_info("System update commands:")
        for i, cmd in enumerate(update_commands, 1):
            print(f"  {i}. {cmd}")
        
        if not self.confirm_yes_no("Execute system update?", True):
            self.print_info("System update skipped")
            return True
            
        # Execute update commands
        for i, cmd in enumerate(update_commands, 1):
            self.print_info(f"Step {i}/{len(update_commands)}: {cmd}")
            if not self.execute_ssh_command(cmd, interactive=True):
                self.print_error(f"System update step {i} failed")
                return False
                    
        self.print_info("System update completed successfully")
        return True
    
    def setup_python_venv(self):
        """Create and configure Python virtual environment"""
        self.print_info("Setting up Python virtual environment...")
        
        venv_commands = [
            # Create virtual environment
            "cd ~/spotmicroai && python3 -m venv venv",
            # Upgrade pip in venv
            "cd ~/spotmicroai && source venv/bin/activate && pip install --upgrade pip"
        ]
        
        self.print_info("Virtual environment setup commands:")
        for i, cmd in enumerate(venv_commands, 1):
            print(f"  {i}. {cmd}")
        
        if not self.confirm_yes_no("Create Python virtual environment?", True):
            self.print_info("Virtual environment setup skipped")
            return True
            
        # Execute venv commands
        for i, cmd in enumerate(venv_commands, 1):
            self.print_info(f"Step {i}/{len(venv_commands)}: Setting up venv...")
            if not self.execute_ssh_command(cmd):
                self.print_error(f"Virtual environment setup step {i} failed")
                return False
                    
        self.print_info("Virtual environment setup completed successfully")
        return True
    
    def install_python_packages(self):
        """Install required Python packages in the virtual environment"""
        self.print_info("Installing required Python packages...")
        
        # Required packages for SpotMicroAI
        packages = [
            "pip",
            "setuptools", 
            "jmespath",
            "throttle",
            "adafruit-circuitpython-motor",
            "adafruit-circuitpython-pca9685",
            "inputs",
            "smbus",
            "RPi.GPIO",
            "pick"
        ]
        
        packages_str = " ".join(packages)
        install_cmd = f"cd ~/spotmicroai && source venv/bin/activate && pip install {packages_str}"
        
        self.print_info("Required packages:")
        for i, pkg in enumerate(packages, 1):
            print(f"  {i:2d}. {pkg}")
        
        print(f"\nInstall command:")
        print(f"  {install_cmd}")
        
        if not self.confirm_yes_no("Install required Python packages?", True):
            self.print_info("Package installation skipped")
            return True
            
        self.print_info("Installing packages (this may take a while)...")
        if not self.execute_ssh_command(install_cmd, interactive=True):
            self.print_error("Package installation failed")
            return False
                    
        self.print_info("Python packages installed successfully")
        return True
    
    def set_executable_permissions(self, interactive=True):
        """Set executable permissions on shell scripts"""
        if interactive:
            self.print_info("Setting executable permissions on scripts...")
        
        chmod_commands = [
            "cd ~/spotmicroai && find . -name '*.sh' -exec chmod +x {} \\;",
            "cd ~/spotmicroai && chmod +x run.sh || true",
            "cd ~/spotmicroai && chmod +x deploy.sh || true"
        ]
        
        if interactive:
            self.print_info("Permission commands:")
            for i, cmd in enumerate(chmod_commands, 1):
                print(f"  {i}. {cmd}")
        
            if not self.confirm_yes_no("Set executable permissions?", True):
                self.print_info("Permission setting skipped")
                return True
        
        # Execute chmod commands
        success = True
        for i, cmd in enumerate(chmod_commands, 1):
            if interactive:
                self.print_info(f"Step {i}/{len(chmod_commands)}: Setting permissions...")
            if not self.execute_ssh_command(cmd):
                if interactive:
                    self.print_warning(f"Permission command {i} failed (may be normal)")
                success = False
                    
        if interactive:
            self.print_info("Executable permissions set successfully")
        
        return success
    
    def setup_systemctl_service(self):
        """Set up SpotMicroAI as a systemctl service"""
        self.print_info("Setting up SpotMicroAI systemctl service...")
        
        # Check if service file exists in utilities
        service_file_exists = False
        check_cmd = "test -f ~/spotmicroai/utilities/boot/spotmicroai.service"
        if self.execute_ssh_command(check_cmd):
            service_file_exists = True
        
        if not service_file_exists:
            self.print_warning("Service file not found at ~/spotmicroai/utilities/boot/spotmicroai.service")
            self.print_info("Service setup skipped")
            return True
        
        service_commands = [
            # Copy service file to systemd
            "sudo cp ~/spotmicroai/utilities/boot/spotmicroai.service /etc/systemd/system/",
            # Reload systemd daemon
            "sudo systemctl daemon-reload",
            # Enable service (optional - will ask user)
            # "sudo systemctl enable spotmicroai.service"
        ]
        
        self.print_info("Service setup commands:")
        for i, cmd in enumerate(service_commands, 1):
            print(f"  {i}. {cmd}")
        
        if not self.confirm_yes_no("Set up systemctl service?", True):
            self.print_info("Systemctl service setup skipped")
            return True
            
        # Execute service setup commands
        for i, cmd in enumerate(service_commands, 1):
            self.print_info(f"Step {i}/{len(service_commands)}: Setting up service...")
            if not self.execute_ssh_command(cmd, interactive=True):
                self.print_error(f"Service setup step {i} failed")
                return False
        
        # Ask if user wants to enable the service
        if self.confirm_yes_no("Enable SpotMicroAI service to start on boot?", False):
            if self.execute_ssh_command("sudo systemctl enable spotmicroai.service"):
                self.print_info("SpotMicroAI service enabled for boot")
            else:
                self.print_error("Failed to enable service")
        
        # Ask if user wants to start the service now
        if self.confirm_yes_no("Start SpotMicroAI service now?", False):
            if self.execute_ssh_command("sudo systemctl start spotmicroai.service"):
                self.print_info("SpotMicroAI service started")
                # Show status
                self.execute_ssh_command("sudo systemctl status spotmicroai.service --no-pager")
            else:
                self.print_error("Failed to start service")
                    
        self.print_info("Systemctl service setup completed")
        return True
    
    def clean_remote_files(self):
        """Clean/delete files on the remote Raspberry Pi"""
        self.print_info("Remote File Cleanup Options")
        
        cleanup_options = {
            '1': 'Remove entire ~/spotmicroai directory',
            '2': 'Remove Python virtual environment only',
            '3': 'Remove log files and cache',
            '4': 'Remove __pycache__ directories',
            '5': 'Custom cleanup (enter commands manually)'
        }
        
        print("\nAvailable cleanup options:")
        for key, option in cleanup_options.items():
            print(f"  {key}. {option}")
        
        while True:
            choice = input(f"\nSelect cleanup option [1-5]: ").strip()
            
            if choice in cleanup_options:
                break
            else:
                self.print_error("Invalid choice. Please select 1-5.")
        
        selected_option = cleanup_options[choice]
        self.print_info(f"Selected: {selected_option}")
        
        # Define cleanup commands based on choice
        if choice == '1':
            commands = [
                "rm -rf ~/spotmicroai",
                "rm -f ~/spotmicroai.json"
            ]
            self.print_warning("This will completely remove the SpotMicroAI installation!")
        elif choice == '2':
            commands = [
                "rm -rf ~/spotmicroai/venv"
            ]
        elif choice == '3':
            commands = [
                "find ~/spotmicroai -name '*.log' -delete",
                "find ~/spotmicroai -name '*.tmp' -delete",
                "rm -rf ~/spotmicroai/.cache"
            ]
        elif choice == '4':
            commands = [
                "find ~/spotmicroai -name '__pycache__' -type d -exec rm -rf {} + || true",
                "find ~/spotmicroai -name '*.pyc' -delete || true"
            ]
        elif choice == '5':
            # Custom cleanup
            commands = []
            print("\nEnter cleanup commands (one per line, empty line to finish):")
            while True:
                cmd = input("Command: ").strip()
                if not cmd:
                    break
                commands.append(cmd)
        
        if not commands:
            self.print_info("No cleanup commands to execute")
            return True
        
        print(f"\nCleanup commands to execute:")
        for i, cmd in enumerate(commands, 1):
            print(f"  {i}. {cmd}")
        
        if not self.confirm_yes_no("Execute these cleanup commands?", False):
            self.print_info("Cleanup cancelled")
            return True
        
        # Execute cleanup commands
        success = True
        for i, cmd in enumerate(commands, 1):
            self.print_info(f"Executing cleanup command {i}/{len(commands)}")
            if not self.execute_ssh_command(cmd):
                self.print_warning(f"Cleanup command {i} failed: {cmd}")
                success = False
        
        if success:
            self.print_info("Remote cleanup completed successfully")
        else:
            self.print_warning("Remote cleanup completed with some errors")
        
        return success
    
    def sync_files_to_rpi(self):
        """Sync files to Raspberry Pi using rsync"""
        self.print_info("Syncing files to Raspberry Pi...")
        
        if not self.check_rsync_available():
            self.print_error("rsync is not available")
            self.print_info("Please install rsync: sudo apt install rsync")
            return False
            
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        project_root = self.script_dir.parent
        
        # Ensure remote directory exists
        self.print_info("Ensuring remote directory exists...")
        if not self.execute_ssh_command("mkdir -p ~/spotmicroai"):
            self.print_warning("Could not create remote directory")
        
        include_patterns, exclude_patterns = self.get_project_files()
        
        # First, sync the main project files to ~/spotmicroai/
        rsync_cmd = [
            'rsync',
            '-avz',  # archive, verbose, compress
            '--progress',
            '--delete',  # Delete files on target that don't exist on source
        ]
        
        # Add exclude patterns
        for pattern in exclude_patterns:
            rsync_cmd.extend(['--exclude', pattern])
            
        # Add source and destination for main project files
        rsync_cmd.append(f"{project_root}/")
        rsync_cmd.append(f"{username}@{hostname}:~/spotmicroai/")
        
        self.print_info("Main project sync command:")
        print(f"  {' '.join(rsync_cmd)}")
        
        if not self.confirm_yes_no("Execute main project file sync?", True):
            self.print_info("Main project sync skipped")
        else:
            if not self.execute_rsync(rsync_cmd):
                return False
        
        # Second, copy spotmicroai.json to the home directory root
        json_file = project_root / "spotmicroai.json"
        if json_file.exists():
            self.print_info("Copying spotmicroai.json to home directory...")
            json_rsync_cmd = [
                'rsync',
                '-avz',
                str(json_file),
                f"{username}@{hostname}:~/"
            ]
            
            self.print_info("Config file sync command:")
            print(f"  {' '.join(json_rsync_cmd)}")
            
            if self.confirm_yes_no("Copy spotmicroai.json to home directory?", True):
                if not self.execute_rsync(json_rsync_cmd):
                    self.print_warning("Failed to copy spotmicroai.json")
            else:
                self.print_info("Config file copy skipped")
        else:
            self.print_warning("spotmicroai.json not found in source directory")
        
        # Third, set executable permissions on transferred files
        self.print_info("Setting executable permissions on transferred files...")
        if not self.set_executable_permissions(interactive=False):
            self.print_warning("Failed to set some executable permissions")
        
        return True
    
    def perform_full_deployment(self):
        """Perform full deployment: sync files and restart services"""
        self.print_info("Starting full deployment...")
        
        # Sync files
        if not self.sync_files_to_rpi():
            return False
        
        # Note: sync_files_to_rpi() already handles chmod automatically
            
        # Restart services
        self.print_info("Managing SpotMicroAI services...")
        
        service_commands = [
            "pkill -f spotmicroai || true",           # Stop any running instances
            "cd ~/spotmicroai && source venv/bin/activate && ./run.sh &",  # Start in venv
        ]
        
        for cmd in service_commands:
            self.print_info(f"Executing service command: {cmd}")
            if not self.execute_ssh_command(cmd):
                self.print_warning(f"Service command failed: {cmd}")
        
        self.print_info("Full deployment completed")
        return True
    
    def perform_custom_actions(self):
        """Allow user to select custom actions"""
        self.print_info("Custom Actions Menu")
        
        custom_actions = {
            '1': 'Restart services only',
            '2': 'Install/update Python packages', 
            '3': 'Set executable permissions',
            '4': 'Setup Python virtual environment',
            '5': 'Install system dependencies'
        }
        
        print("\nAvailable custom actions:")
        for key, action in custom_actions.items():
            print(f"  {key}. {action}")
            
        selected = []
        while True:
            choice = input(f"\nSelect actions (comma-separated) or 'done': ").strip()
            
            if choice.lower() == 'done':
                break
                
            choices = [c.strip() for c in choice.split(',')]
            for c in choices:
                if c in custom_actions and c not in selected:
                    selected.append(c)
                    self.print_info(f"Added: {custom_actions[c]}")
                elif c in selected:
                    self.print_warning(f"Already selected: {custom_actions[c]}")
                else:
                    self.print_error(f"Invalid choice: {c}")
        
        if selected:
            self.print_info(f"Will execute {len(selected)} custom actions")
            for action_id in selected:
                action_name = custom_actions[action_id]
                self.print_info(f"Executing: {action_name}")
                
                if action_id == '1':  # Restart services only
                    self.execute_ssh_command("pkill -f spotmicroai || true")
                    self.execute_ssh_command("cd ~/spotmicroai && source venv/bin/activate && ./run.sh &")
                elif action_id == '2':  # Install/update Python packages
                    self.install_python_packages()
                elif action_id == '3':  # Set executable permissions
                    self.set_executable_permissions()
                elif action_id == '4':  # Setup Python virtual environment
                    self.setup_python_venv()
                elif action_id == '5':  # Install system dependencies
                    self.execute_ssh_command("sudo apt install -y python3-pip python3-venv git rsync", interactive=True)
                
        return True
    
    def execute_deployment_action(self, action):
        """Execute the selected deployment action"""
        if action == '1':  # Initial Setup
            return self.perform_initial_setup()
        elif action == '2':  # Sync Files Only
            return self.sync_files_to_rpi()
        elif action == '3':  # Full Deployment
            return self.perform_full_deployment()
        elif action == '4':  # System Update
            return self.perform_system_update()
        elif action == '5':  # Setup SSH Keys
            return self.setup_ssh_key()
        elif action == '6':  # Clean Remote Files
            return self.clean_remote_files()
        elif action == '7':  # Setup System Service
            return self.setup_systemctl_service()
        elif action == '8':  # View System Status
            return self.execute_ssh_command("uptime && echo && df -h && echo && free -h && echo && systemctl status spotmicroai.service --no-pager || echo 'Service not installed'")
        elif action == '9':  # Custom Actions
            return self.perform_custom_actions()
        else:
            self.print_error(f"Unknown action: {action}")
            return False
            
    def validate_ssh_setup(self):
        """Validate SSH setup and connection"""
        if not self.check_ssh_available():
            self.print_error("SSH client is not available")
            self.print_info("Please install openssh-client and try again")
            return False
            
        hostname = self.config.get('hostname')
        username = self.config.get('username')
        password = getattr(self, 'current_password', None)
        
        return self.test_ssh_connection(hostname, username, password)
        
    def run(self):
        """Main deployment process"""
        try:
            # Collect deployment information
            if not self.collect_deployment_info():
                self.print_error("Failed to collect deployment information")
                return False
                
            # Validate SSH setup
            if not self.validate_ssh_setup():
                self.print_error("SSH validation failed")
                
                # Offer to set up SSH keys if password was provided
                password = getattr(self, 'current_password', None)
                if password:
                    print()
                    self.print_info("SSH key-based authentication can eliminate password prompts")
                    if self.confirm_yes_no("Set up SSH key-based authentication?", True):
                        if self.setup_ssh_key():
                            self.print_info("SSH key setup completed. Retrying SSH validation...")
                            if not self.validate_ssh_setup():
                                self.print_error("SSH validation still failed after key setup")
                                return False
                        else:
                            self.print_warning("SSH key setup failed, continuing with password authentication")
                            # Check if sshpass is available for password automation
                            if not self.check_sshpass_available():
                                self.print_warning("sshpass not found - you will be prompted for password multiple times")
                                self.print_info("Install sshpass for automated password handling: sudo apt install sshpass")
                    else:
                        # Check if sshpass is available for password automation
                        if not self.check_sshpass_available():
                            self.print_warning("sshpass not found - you will be prompted for password multiple times")
                            self.print_info("Install sshpass for automated password handling: sudo apt install sshpass")
                else:
                    return False
                    
            # Establish SSH connection
            if not self.establish_ssh_connection():
                self.print_error("Failed to establish SSH connection")
                return False
                
            # Get deployment action from user
            action = self.get_deployment_action()
            if action is None:
                return True  # User chose to quit
                
            # Execute the selected deployment action
            if not self.execute_deployment_action(action):
                self.print_error("Deployment action failed")
                return False
                
            self.print_info("Deployment completed successfully!")
            return True
            
        except KeyboardInterrupt:
            self.print_warning("\nDeployment cancelled by user")
            return False
        except Exception as e:
            self.print_error(f"Deployment failed: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SpotMicroAI Deployment Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive deployment
  %(prog)s -y                 # Use existing config without prompting
  %(prog)s --yes-all          # Auto-confirm all actions (no prompts)
  %(prog)s -y --yes-all       # Use existing config + auto-confirm all
  %(prog)s --clean            # Clear existing config and start fresh
  %(prog)s --clean --yes-all  # Clear config and auto-confirm all
        """
    )
    
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Automatically accept existing configuration without prompting'
    )
    
    parser.add_argument(
        '--yes-all',
        action='store_true',
        help='Automatically confirm all actions (skips all Y/n prompts)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clear existing configuration and start fresh'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='SpotMicroAI Deployment Script v1.0'
    )
    
    args = parser.parse_args()
    
    deployment_manager = DeploymentManager(args)
    
    if deployment_manager.run():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
