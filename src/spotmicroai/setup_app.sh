#!/bin/bash

# Change to the directory where the script lives
cd "$(dirname "$0")" || exit

# Detect environment by checking venv location
if [ -d "../.venv" ]; then
    # Local mode: venv is at project root (parent directory)
    export PYTHONPATH="$(pwd)"
    ../.venv/bin/python3 -m setup_app
elif [ -d "./.venv" ]; then
    # Remote mode: venv is in current directory (~/spotmicroai)
    export PYTHONPATH="$(pwd)"
    ./venv/bin/python3 -m setup_app
else
    echo "Error: Cannot find venv in expected locations"
    exit 1
fi
