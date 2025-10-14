# Setup Tool Changes - v2.0

## Overview
The setup tool has been completely rewritten to provide a streamlined, automated first-time setup experience for SpotmicroAI on Raspberry Pi.

## Key Changes

### 1. First-Time Setup Detection
- Automatically detects if this is the first run (no `setup_config.json` present)
- Displays important prerequisites before starting:
  - Fresh SD card with Raspberry Pi OS
  - SSH enabled
  - Network connectivity
  - Known hostname/IP address
- Points users to documentation if prerequisites aren't met

### 2. Simplified Initial Configuration
- Prompts for hostname (default: `spotmicroai.local`)
- Prompts for username (default: `pi`)
- Requires password for initial setup
- Removes unnecessary "WiFi configured" question

### 3. SSH Key Setup
- Checks for existing SSH key pairs
- Offers choice to use existing keys or generate new ones
- Automatically copies SSH public key to Raspberry Pi
- Enables passwordless authentication for future connections

### 4. Automated Setup Process (8 Steps)

The tool now performs a complete, automated setup:

**Step 1: System Update**
- Runs `sudo apt update`
- Runs `sudo apt upgrade -y`

**Step 2: Enable I2C**
- Configures I2C interface using `raspi-config`
- Adds `dtparam=i2c_arm=on` to config.txt

**Step 3: Create Project Directory**
- Creates `~/spotmicroai` directory

**Step 4: Install Python & Dependencies**
- Installs Python3, pip, venv
- Installs system packages: `i2c-tools`, `python3-smbus`, etc.

**Step 5: Create Virtual Environment**
- Creates Python virtual environment in `~/spotmicroai/venv`
- Upgrades pip to latest version

**Step 6: Copy Project Files**
- Uses SCP to copy all files from local `robot/` folder
- Transfers to `~/spotmicroai/` on Raspberry Pi

**Step 7: Install Python Packages**
- Activates virtual environment
- Runs `pip install -r requirements.txt`

**Step 8: Set Permissions & Copy Config**
- Sets executable permissions on all `.sh` scripts
- Copies `spotmicroai.json` to home directory root (`~/`)

### 5. Status Tracking
- Saves `setup_completed` flag in config
- Prevents re-running complete setup on already configured systems
- Provides clear next steps after successful setup

## Usage

### First Time Setup
```bash
python setup_tool.py
```

### Clear Config and Start Fresh
```bash
python setup_tool.py --clean
```

### Show Version
```bash
python setup_tool.py --version
```

## Configuration File

The tool creates `setup_config.json` with:
```json
{
  "hostname": "spotmicroai.local",
  "username": "pi",
  "password_provided": true,
  "setup_completed": true
}
```

**Note:** The actual password is never stored in the config file for security reasons.

## Prerequisites

Before running the setup tool, ensure:

1. **Raspberry Pi OS is installed**
   - Use Raspberry Pi Imager
   - Select Raspberry Pi OS (64-bit recommended)

2. **SSH is enabled**
   - Create an empty file named `ssh` in the boot partition
   - Or use Raspberry Pi Imager's settings to enable SSH

3. **Network is configured**
   - Configure WiFi using Raspberry Pi Imager
   - Or connect via Ethernet

4. **You know the hostname or IP**
   - Default: `raspberrypi.local`
   - Custom: Set during OS installation
   - IP: Check your router's DHCP list

## What Gets Deployed

From the `robot/` folder:
- All Python source files (`spotmicroai/`, `calibration/`, `integration_tests/`)
- Configuration files (`spotmicroai.json`, `requirements.txt`)
- Shell scripts (`run.sh`, `*.sh`)
- Documentation (`README.md`)

The `spotmicroai.json` file is also copied to the home directory root (`~/spotmicroai.json`).

## After Setup

Once setup is complete, you can:

1. SSH into your Raspberry Pi:
   ```bash
   ssh pi@spotmicroai.local
   ```

2. Navigate to the project:
   ```bash
   cd ~/spotmicroai
   ```

3. Run the robot:
   ```bash
   ./run.sh
   ```

## Troubleshooting

### SSH Connection Fails
- Verify the Raspberry Pi is powered on
- Check network connectivity: `ping spotmicroai.local`
- Verify SSH is enabled
- Check hostname/IP address is correct

### Permission Denied
- Ensure you're using the correct username
- Verify password is correct
- Check SSH is properly enabled on the Pi

### Package Installation Fails
- Ensure internet connectivity on Raspberry Pi
- Try running system update manually first
- Check available disk space

### File Copy Fails
- Verify network connectivity
- Check available disk space on Raspberry Pi
- Ensure `robot/` folder exists locally

## Notes for Bluetooth Controller

The Bluetooth controller setup is noted in the code but deferred to later implementation. This will be added in a future update.

## Migration from Old Setup Tool

The old setup tool has been backed up as `setup_tool_old.py`. You can:
- Review the old implementation for reference
- Delete it once you're satisfied with the new version
- Use `--clean` flag to clear old configurations

## Security Considerations

- Passwords are never stored in config files
- SSH key authentication is strongly recommended
- Keys are generated without passphrases for automation (you can add passphrases manually)
- StrictHostKeyChecking is disabled for convenience (enable in production)
