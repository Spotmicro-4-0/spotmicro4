# SpotmicroAI Setup Tool

Automated setup tool for configuring SpotmicroAI on Raspberry Pi.

## Quick Start

```bash
python setup_tool.py
```

This will:
1. Detect first-time setup and show prerequisites
2. Collect Raspberry Pi connection details (hostname, username, password)
3. Test SSH connection
4. Optionally setup SSH keys for passwordless authentication
5. Perform complete automated setup (8 steps)

## What It Does

### Automated Setup Process

1. **System Update** - Updates and upgrades all packages
2. **Enable I2C** - Configures I2C interface for hardware communication
3. **Create Project Directory** - Sets up `~/spotmicroai`
4. **Install Dependencies** - Installs Python, pip, and system packages
5. **Create Virtual Environment** - Sets up isolated Python environment
6. **Copy Project Files** - Transfers all robot code to Raspberry Pi
7. **Install Python Packages** - Installs requirements from `requirements.txt`
8. **Configure System** - Sets permissions and copies config files

## Prerequisites

Before running:

✓ Raspberry Pi with fresh Raspberry Pi OS  
✓ SSH enabled on the Raspberry Pi  
✓ Network connectivity (WiFi or Ethernet)  
✓ Known hostname or IP address  

See `docs/1.raspberry-pi.md` for detailed setup instructions.

## Commands

### Run Setup
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

## Configuration

The tool creates `setup_config.json`:

```json
{
  "hostname": "spotmicroai.local",
  "username": "pi",
  "password_provided": true,
  "setup_completed": true
}
```

**Security Note:** Passwords are never stored in the config file.

## SSH Key Setup

The tool offers to setup SSH key authentication:

- **Existing Keys**: Will detect and offer to use existing SSH keys
- **New Keys**: Can generate new RSA 4096-bit keys
- **Auto-Copy**: Automatically copies public key to Raspberry Pi

After setup, you can connect without a password:
```bash
ssh pi@spotmicroai.local
```

## After Setup

Once complete:

1. SSH into your Raspberry Pi:
   ```bash
   ssh pi@spotmicroai.local
   ```

2. Navigate to project:
   ```bash
   cd ~/spotmicroai
   ```

3. Run the robot:
   ```bash
   ./run.sh
   ```

## Files Deployed

From `robot/` folder to `~/spotmicroai/`:
- Python source code
- Configuration files
- Shell scripts
- Requirements

Plus `spotmicroai.json` copied to `~/spotmicroai.json`

## Troubleshooting

### Connection Issues
- Verify Raspberry Pi is on
- Check network: `ping spotmicroai.local`
- Verify SSH is enabled
- Confirm hostname/IP is correct

### Permission Denied
- Check username is correct
- Verify password
- Ensure SSH is enabled

### Installation Failures
- Check internet connectivity
- Verify disk space
- Try manual `sudo apt update`

## Technical Details

- **Language**: Python 3
- **Transport**: SSH and SCP
- **Authentication**: Password and/or SSH keys
- **Platform**: Windows/Linux/macOS compatible

## See Also

- `CHANGES.md` - Detailed changelog and migration guide
- `docs/1.raspberry-pi.md` - Raspberry Pi setup instructions
- `docs/2.ssh-keys.md` - SSH configuration details

## Support

For issues or questions:
1. Check documentation in `docs/` folder
2. Review `CHANGES.md` for common scenarios
3. Check Raspberry Pi connectivity and SSH status
