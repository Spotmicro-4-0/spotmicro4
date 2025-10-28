#!/bin/bash
set -euo pipefail

# inverse_kinematics.sh
# Launch the interactive inverse kinematics controller for a specific leg corner.
# Usage: inverse_kinematics.sh <front_left|front_right|rear_left|rear_right>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <front_left|front_right|rear_left|rear_right>"
    exit 1
fi

CORNER="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
case "$CORNER" in
    front_left|front_right|rear_left|rear_right)
        ;;
    *)
        echo "Error: invalid corner '$1'"
        echo "Valid options: front_left, front_right, rear_left, rear_right"
        exit 1
        ;;
esac

# Directory that contains this script (inverse_kinematics/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Go up two levels to reach src/
SRC_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Virtual environment location
VENV_PATH="$SRC_DIR/.venv"

if [ ! -d "$VENV_PATH/bin" ]; then
    echo "Error: .venv not found at $VENV_PATH"
    exit 1
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Ensure Python can import the package modules
export PYTHONPATH="$SRC_DIR:${PYTHONPATH:-}"

# Execute the Python UI
python3 "$SCRIPT_DIR/inverse_kinematics.py" "$CORNER"
