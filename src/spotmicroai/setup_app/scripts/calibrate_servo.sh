#!/bin/bash
set -euo pipefail

# calibrate_servo.sh
# Interactive servo calibration script
# Usage: calibrate_servo.sh <SERVO_ID> <MODE>
# Modes: min, max, rest, range

if [ $# -ne 2 ]; then
    echo "Usage: $0 <SERVO_ID> <MODE>"
    echo "Modes: min, max, rest, range"
    exit 1
fi

SERVO_ID="$1"
MODE="$2"

# Get the absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go up 3 levels: setup_app/scripts/ -> setup_app/ -> spotmicroai/ -> src/
SRC_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# The venv is in the src directory
VENV_PATH="$SRC_DIR/.venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: .venv not found at $VENV_PATH"
    exit 1
fi

# Activate the venv
source "$VENV_PATH/bin/activate"

# Export PYTHONPATH and run the Python calibration script
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$SRC_DIR"
python3 "$SCRIPT_DIR/calibrate_servo.py" "$SERVO_ID" "$MODE"
