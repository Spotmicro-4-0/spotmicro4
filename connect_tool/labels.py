# ------------------------------------------------------------------
# Labels and Messages
# ------------------------------------------------------------------

# Version and branding
VERSION = "SpotmicroAI Setup Tool v4.0"

# Console prefixes
INFO_PREFIX = "[INFO]"
WARN_PREFIX = "[WARN]"
ERROR_PREFIX = "[ERROR]"
STEP_PREFIX = "[STEP {n}/{TOTAL_STEPS}]"

# User prompts
PROMPT_HOSTNAME = "Hostname/IP"
PROMPT_USERNAME = "Username"
PROMPT_PASSWORD = "Password"
PROMPT_REMOVE_DIR = "Remove it?"
PROMPT_FIRST_TIME_SETUP = "Run first-time setup?"
PROMPT_SSH_KEY_AUTH = "Setup SSH key authentication?"

# Error messages
ERR_MISSING_REQUIRED = "Hostname, username, and password are required"
ERR_SSH_TEST_FAILED = "SSH test failed"
ERR_SSH_KEY_GEN_FAILED = "Failed to generate SSH keys"
ERR_PUBLIC_KEY_NOT_FOUND = "Public key not found"
ERR_MISSING_SOURCE_DIR = "Missing source directory: {src_dir}"
ERR_FILE_COPY_FAILED = "File copy failed"
ERR_SYNC_FAILED = "Sync failed"
ERR_SETUP_FAILED_AT_STEP = "Setup failed at step: {name}"
ERR_CANNOT_PROCEED_EXISTING_DIR = "Cannot proceed with existing directory"
ERR_SOURCE_DIR_NOT_FOUND = "Source directory not found: {src_dir}"
ERR_SSH_COMMAND_FAILED = "SSH command failed: {e}"
ERR_INVALID_CONFIG = "Invalid configuration: {e}"
ERR_SAVE_CONFIG_FAILED = "Failed to save configuration: {e}"
ERR_UNEXPECTED_ERROR = "Unexpected error: {e}"

# Success messages
MSG_SSH_TEST_SUCCESSFUL = "SSH test successful"
MSG_SSH_CONNECTION_VERIFIED = "SSH connection verified"
MSG_SSH_KEY_GENERATED = "Generated SSH keypair"
MSG_SSH_KEY_INSTALLED = "SSH key installed on Raspberry Pi"
MSG_FILES_COPIED = "Files copied successfully"
MSG_FILES_SYNCED = "Files synced successfully"
MSG_SETUP_COMPLETED = "Setup Completed Successfully"
MSG_CONFIG_SAVED = "Saved configuration → {config_file}"
MSG_CONFIG_CLEARED = "Configuration cleared"
MSG_CONFIG_FOUND = "Existing configuration found"
MSG_SYNCING_CHANGES = "Syncing code changes..."
MSG_EXEC_PERMISSIONS_SET = "Setting execute permissions"
MSG_CONFIG_FILE_COPIED = "Config file copied"
MSG_LAUNCHING_SETUP_APP = "Launching Setup App on Raspberry Pi..."
MSG_TRANSFERRING_FILES = "Transferring project files..."

# Warning messages
WARN_CONFIG_FILE_NOT_FOUND = "{config_filename} not found locally"
WARN_EXISTING_DIR_FOUND = "Found existing ~/{project_dir} directory"
WARN_INTERRUPTED = "Interrupted by user"

# Step descriptions
STEP_SYSTEM_UPDATE = "System Update"
STEP_ENABLE_I2C = "Enable I2C"
STEP_CREATE_PROJECT_DIR = "Create Project Directory"
STEP_INSTALL_PYTHON_DEPS = "Install Python & Dependencies"
STEP_CREATE_VENV = "Create Virtual Environment"
STEP_COPY_FILES = "Copy Project Files"
STEP_INSTALL_PACKAGES = "Install Python Packages"
STEP_FINALIZE = "Finalize Setup"
STEP_LAUNCH_APP = "Launch Setup Application"

# Sub-step descriptions
SUBSTEP_UPDATING_PACKAGES = "Updating package list"
SUBSTEP_UPGRADING_PACKAGES = "Upgrading packages"
SUBSTEP_INSTALLING_SSH_KEY = "Installing SSH key on Raspberry Pi"
SUBSTEP_TESTING_SSH = "Testing SSH connectivity..."

# UI elements
UI_INITIAL_SETUP_HEADER = "SpotmicroAI Initial Setup"

# Command line help
CLI_DESCRIPTION = "SpotmicroAI Setup Tool"
CLI_CLEAN_HELP = "Clear existing configuration and start fresh"
CLI_DEPLOY_HELP = "Sync code changes only"
