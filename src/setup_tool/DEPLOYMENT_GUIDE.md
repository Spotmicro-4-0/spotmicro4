# SpotmicroAI Development Deployment Guide

## Overview

The setup tool now supports efficient code deployment for development workflows. After initial setup, you can quickly sync code changes to your Raspberry Pi using `rsync`.

## Usage Modes

### 1. Initial Setup (First Time)
```bash
./setup.sh
```
This will:
- Configure SSH connection
- Set up SSH keys for passwordless authentication
- Update system packages
- Install Python and dependencies
- Copy all project files
- Configure the environment

### 2. Development Mode (Sync Changes)
```bash
./setup.sh --deploy
```
Or simply run `./setup.sh` and select option 1 when prompted.

This will:
- Sync only changed files using `rsync`
- Preserve timestamps and permissions
- Delete remote files that don't exist locally
- Exclude unnecessary files (`.git`, `__pycache__`, `*.pyc`, `venv`, `*.log`)
- Set executable permissions on shell scripts

### 3. Clean Setup (Start Fresh)
```bash
./setup.sh --clean
```
This will clear all saved configuration and start from scratch.

## Development Workflow

1. **Initial Setup** (one time):
   ```bash
   cd ~/Spotmicro4/src
   ./setup.sh
   ```

2. **Make Code Changes** locally in your editor

3. **Deploy Changes** to Raspberry Pi:
   ```bash
   ./setup.sh --deploy
   ```
   or just:
   ```bash
   ./setup.sh
   # Then select option 1
   ```

4. **Test on Raspberry Pi**:
   ```bash
   ssh pi@spotmicroai.local
   cd ~/spotmicroai
   ./run.sh
   ```

## Benefits of rsync

- **Speed**: Only transfers changed files
- **Efficiency**: Compresses data during transfer
- **Safety**: Preserves file attributes and permissions
- **Clean**: Automatically removes deleted files on remote
- **Smart**: Excludes development artifacts automatically

## What Gets Synced

✅ **Included:**
- Python source files (`*.py`)
- Shell scripts (`*.sh`)
- Configuration files (`*.json`)
- README and documentation
- All project directories

❌ **Excluded:**
- `.git` directory
- `__pycache__` directories
- `*.pyc` compiled Python files
- `venv` virtual environment
- `*.log` log files

## Requirements

- `rsync` must be installed on your development machine
  - **Ubuntu/Debian**: `sudo apt-get install rsync`
  - **macOS**: `brew install rsync` (or use built-in)
  - **Windows**: Use WSL or Git Bash with rsync

## Troubleshooting

### "rsync command not found"
Install rsync on your development machine:
```bash
sudo apt-get install rsync  # Ubuntu/Debian
brew install rsync          # macOS
```

### Still asks for password
Ensure SSH keys are set up correctly:
```bash
./setup.sh --clean  # Start fresh
./setup.sh          # Set up SSH keys
```

### Files not syncing
Check that you're in the correct directory:
```bash
cd ~/Spotmicro4/src
./setup.sh --deploy
```

## Advanced Usage

### Manual rsync
You can also use rsync directly:
```bash
rsync -avz --delete \
  --exclude="__pycache__" --exclude="*.pyc" \
  -e "ssh -i ~/.ssh/id_rsa" \
  robot/ pi@spotmicroai.local:~/spotmicroai/
```

### Dry Run (see what would be synced)
```bash
rsync -avzn --delete \
  --exclude="__pycache__" --exclude="*.pyc" \
  -e "ssh -i ~/.ssh/id_rsa" \
  robot/ pi@spotmicroai.local:~/spotmicroai/
```
(Note the `-n` flag for dry-run)
