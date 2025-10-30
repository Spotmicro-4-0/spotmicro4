#!/bin/bash

# Change to the directory where the script lives
cd "$(dirname "$0")" || exit

# Detect environment by checking venv location
if [ -d "../.venv" ]; then
    # Local mode: venv is at project root (parent directory)
    export PYTHONPATH="$(pwd):$(pwd)/..:${PYTHONPATH:-}"
    ../.venv/bin/python3 config_app/config_app.py
elif [ -d "./.venv" ]; then
    # Remote mode: venv is in current directory (~/spotmicroai)
    export PYTHONPATH="$(pwd):$(pwd)/..:${PYTHONPATH:-}"
    ./venv/bin/python3 config_app/config_app.py
else
    echo "Error: Cannot find venv in expected locations"
    exit 1
fi
