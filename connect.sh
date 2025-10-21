#!/bin/bash
# =============================================================
# SpotmicroAI Setup Tool (Bootstrap Script)
# =============================================================
# Ensures Python, pip, and venv are ready, then launches connect_tool.py.
# Includes spinner animation + preview delay.
# =============================================================

set -e

# --- Color definitions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# --- Spinner animation ---
show_spinner() {
    local pid=$1
    local delay=0.15
    local spin=( "⠋" "⠙" "⠸" "⢰" "⣠" "⣄" "⡆" "⠇" )
    while ps -p $pid >/dev/null 2>&1; do
        for s in "${spin[@]}"; do
            printf "\r   %s " "$s"
            sleep $delay
        done
    done
    printf "\r      \r"
}

# --- Parse args ---
VERBOSE=false
for arg in "$@"; do
    if [[ "$arg" == "--verbose" ]]; then
        VERBOSE=true
        shift
    fi
done

# --- Check if .venv already exists ---
if [ -d ".venv" ]; then
    print_info "Existing virtual environment detected. Skipping setup checks..."
    SKIP_SETUP=true
else
    SKIP_SETUP=false
    # --- Verify Python ---
    print_info "Checking Python installation..."
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python 3.6+ is required. Please install Python."
        exit 1
    fi

    MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')
    VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

    if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 6 ]; }; then
        print_error "Python version must be >= 3.6 (found $VERSION)"
        exit 1
    fi
    print_info "Python found: $($PYTHON_CMD --version)"

    # --- Verify pip ---
    print_info "Checking pip..."
    if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        print_warn "pip not found, installing..."
        (
            curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD >/dev/null 2>&1
        ) &
        show_spinner $!
    else
        print_info "pip is available"
    fi

    # --- Virtual environment setup ---
    print_info "Creating virtual environment (.venv)..."
    (
        sleep 3  # <-- Demo delay: remove this later
    ) &
    show_spinner $!
    print_info "Virtual environment created at $(pwd)/.venv"
fi

# --- Activate venv ---
source .venv/bin/activate

# --- Dependency installation ---
if [ "$SKIP_SETUP" = false ]; then
    REQ_FILE="requirements-dev.txt"
    if [ -f "$REQ_FILE" ]; then
        print_info "Installing dev dependencies from $REQ_FILE..."
        if [ "$VERBOSE" = true ]; then
            pip install --upgrade pip
            pip install -r "$REQ_FILE"
        else
            (
                pip install --upgrade pip >/dev/null 2>&1
                pip install -r "$REQ_FILE" >/dev/null 2>&1
            ) &
            show_spinner $!
        fi
    else
        print_warn "No $REQ_FILE found; skipping dependency installation."
    fi
fi

# --- Locate connect_tool.py ---
SETUP_TOOL="connect_tool/connect_tool.py"
if [ ! -f "$SETUP_TOOL" ]; then
    print_error "Connect tool not found: $SETUP_TOOL"
    exit 1
fi

print_info "Environment ready. Launching connect tool..."
exec $PYTHON_CMD "$SETUP_TOOL" "$@"
