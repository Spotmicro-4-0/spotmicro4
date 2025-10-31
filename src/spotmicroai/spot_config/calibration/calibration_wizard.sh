#!/bin/bash
set -euo pipefail

# calibration_wizard.sh
# Interactive servo calibration wizard
# Usage: calibration_wizard.sh <SERVO_ID>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <SERVO_ID>"
    exit 1
fi

SERVO_ID="$1"

# Get the absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve project structure:
# calibration/ -> spot_config/ -> spotmicroai/ -> src/
SPOT_CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
SPOTMICROAI_DIR="$(dirname "$SPOT_CONFIG_DIR")"
SRC_DIR="$(dirname "$SPOTMICROAI_DIR")"
VENV_PATH="$SRC_DIR/.venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: .venv not found at $VENV_PATH"
    exit 1
fi

# Activate venv and run the calibration wizard
source "$VENV_PATH/bin/activate"

# Set PYTHONPATH to include the src directory
export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

# Run the Python script as a module to support relative imports
cd "$SRC_DIR"
python3 -m spotmicroai.spot_config.calibration.calibration_wizard "$SERVO_ID"
