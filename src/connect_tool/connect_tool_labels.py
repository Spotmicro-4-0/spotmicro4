"""
ConnectTool Labels
------------------
Centralized storage for all user-facing strings and labels used by connect_tool.py
"""

# Logging and error messages
MSG_LOG_WRITE_FAILED = "Warning: Could not write to log: {e}"
MSG_LOG_ROTATE_FAILED = "Warning: Could not rotate log: {e}"
MSG_LOG_PATH = "See src/connect_tool/setup.log for more details"

# Input prompts with defaults
PROMPT_HOSTNAME = "Hostname"
PROMPT_USERNAME = "Username"
PROMPT_PASSWORD = "Password"
PROMPT_REMOVE_DIR = "Remove existing directory?"
PROMPT_FIRST_TIME_SETUP = "Is this your first time setting up?"
PROMPT_SSH_KEY_AUTH = "Use SSH key authentication?"

# UI Headers and messages
UI_INITIAL_SETUP_HEADER = "== Initial Setup =="
UI_ACCEPT_DEFAULTS = "You can accept defaults by pressing Enter"

# Information messages
INFO_PREFIX = "[INFO]"
MSG_CONFIG_SAVED = "Configuration saved: {config_file}"
MSG_CONFIG_CLEARED = "Configuration cleared"
MSG_CONFIG_FOUND = "Existing configuration found"
MSG_SSH_CONNECTION_VERIFIED = "SSH connection verified successfully!"
MSG_SSH_KEY_GENERATED = "SSH key pair generated successfully"
MSG_SSH_KEY_INSTALLED = "SSH public key installed on Raspberry Pi"
MSG_TRANSFERRING_FILES = "Transferring files to Raspberry Pi..."
MSG_FILES_COPIED = "Files copied successfully"
MSG_FILES_SYNCED = "Files synchronized successfully"
MSG_EXEC_PERMISSIONS_SET = "Setting executable permissions on shell scripts"
MSG_LAUNCHING_SETUP_APP = "Launching setup application..."
MSG_SYNCING_CHANGES = "Syncing code changes..."
MSG_SETUP_COMPLETED = "Setup completed successfully!"

# Warning messages
WARN_PREFIX = "[WARN]"
WARN_NO_PREVIOUS_CONFIG = "No previous configuration found"
WARN_EXISTING_DIR_FOUND = "Directory ~/spotmicroai already exists"
WARN_INTERRUPTED = "Setup interrupted by user"

# Error messages
ERROR_PREFIX = "[ERROR]"
ERR_INVALID_CONFIG = "Invalid configuration file: {e}"
ERR_SAVE_CONFIG_FAILED = "Failed to save configuration: {e}"
ERR_SSH_COMMAND_FAILED = "SSH command failed: {e}"
ERR_SSH_TEST_FAILED = "SSH connection test failed"
ERR_SSH_KEY_GEN_FAILED = "Failed to generate SSH key pair"
ERR_PUBLIC_KEY_NOT_FOUND = "SSH public key not found (~/.ssh/id_rsa.pub)"
ERR_MISSING_REQUIRED = "Missing required configuration values"
ERR_MISSING_SOURCE_DIR = "Source directory not found: {src_dir}"
ERR_SOURCE_DIR_NOT_FOUND = "Source directory not found: {src_dir}"
ERR_FILE_COPY_FAILED = "Failed to copy files to Raspberry Pi"
ERR_SYNC_FAILED = "Failed to sync code changes"
ERR_CANNOT_PROCEED_EXISTING_DIR = "Cannot proceed with existing directory"
ERR_SETUP_FAILED_AT_STEP = "Setup failed at step: {name}"
ERR_UNEXPECTED_ERROR = "Unexpected error: {e}"

# Step labels
STEP_PREFIX = "[Step {n}/{TOTAL_STEPS}]"
STEP_SYSTEM_UPDATE = "Update system packages"
STEP_ENABLE_I2C = "Enable I2C interface"
STEP_CREATE_PROJECT_DIR = "Create project directory"
STEP_INSTALL_PYTHON_DEPS = "Install Python and dependencies"
STEP_CREATE_VENV = "Create Python virtual environment"
STEP_COPY_FILES = "Copy project files"
STEP_INSTALL_PACKAGES = "Install Python packages"
STEP_FINALIZE = "Finalize deployment"
STEP_LAUNCH_APP = "Launch setup application"

# Sub-step labels
SUBSTEP_TESTING_SSH = "Testing SSH connection..."
SUBSTEP_UPDATING_PACKAGES = "Updating packages..."
SUBSTEP_UPGRADING_PACKAGES = "Upgrading packages..."
SUBSTEP_INSTALLING_SSH_KEY = "Installing SSH key..."
