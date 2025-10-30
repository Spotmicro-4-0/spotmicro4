#!/bin/bash
set -euo pipefail

# diagnostics.sh
# Servo diagnostics wizard for SpotMicroAI
# Tests all servos for symmetry and proper range of motion

# Get the absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go up 2 levels: diagnostics/ -> spotmicroai/ -> src/
SRC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# The venv is in the src directory
VENV_PATH="$SRC_DIR/.venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: .venv not found at $VENV_PATH"
    exit 1
fi

# Activate venv and run the diagnostics wizard
source "$VENV_PATH/bin/activate"

# Set PYTHONPATH to include the src directory
export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

# Run the Python script as a module to support relative imports
cd "$SRC_DIR"
python3 -m spotmicroai.diagnostics.diagnostics
