#!/bin/bash
set -euo pipefail

pidfile="$HOME/spotmicroai/.lock"

# Prevent double runs
if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "spotmicroai is already running (PID $(cat "$pidfile"))"
    exit 1
fi

echo $$ > "$pidfile"
trap 'rm -f "$pidfile"' EXIT

# Activate the venv in home dir
source "$HOME/.venv/bin/activate"

# Safely set PYTHONPATH - ensure spotmicroai parent directory is in path
export PYTHONPATH="${HOME}:${PYTHONPATH:-}"

# Run main
python3 "$HOME/spotmicroai/runtime/main.py" "$@"
