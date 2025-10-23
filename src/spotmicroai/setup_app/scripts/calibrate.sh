#!/bin/bash
set -euo pipefail

# Get the absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go up 3 levels: setup_app/scripts/calibration.py -> setup_app/ -> spotmicroai/ -> src/
SRC_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# The venv is in the home directory
VENV_PATH="$HOME/venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: venv not found at $VENV_PATH"
    exit 1
fi

# Activate the venv
source "$VENV_PATH/bin/activate"

# Export PYTHONPATH and run the script
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$SRC_DIR"
python3 "$SCRIPT_DIR/calibration.py"
