#!/bin/bash
set -euo pipefail

# servo_manual_control.sh
# Manual servo control for testing and motion verification
# Usage: servo_manual_control.sh <SERVO_ID>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <SERVO_ID>"
    exit 1
fi

SERVO_ID="$1"

# Get the absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go up 2 levels: calibration/ -> spotmicroai/ -> src/
SRC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# The venv is in the src directory
VENV_PATH="$SRC_DIR/.venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: .venv not found at $VENV_PATH"
    exit 1
fi

# Activate venv and run the manual control
source "$VENV_PATH/bin/activate"

# Set PYTHONPATH to include the src directory
export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

# Run the Python script
python3 "$SCRIPT_DIR/servo_manual_control.py" "$SERVO_ID"
