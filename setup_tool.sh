#!/bin/bash

# SpotmicroAI Setup Tool
# This tool validates the host environment and initiates the setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "SpotmicroAI Setup Tool"
    echo
    echo "OPTIONS:"
    echo "  --deploy      Sync code changes to Raspberry Pi (for development)"
    echo "  --clean       Clear existing configuration and start fresh"
    echo "  --version     Show version information"
    echo "  -h, --help    Show this help message"
    echo
    echo "Examples:"
    echo "  $0                # Interactive setup"
    echo "  $0 --deploy       # Sync code changes to Pi"
    echo "  $0 --clean        # Clear existing config and start fresh"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    local version=$($python_cmd --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 6 ]; then
        return 0
    else
        return 1
    fi
}

# Check for help option early
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    print_usage
    exit 0
fi

print_info "SpotmicroAI Setup Tool"
print_info "=============================="

# Check if Python is installed
print_info "Checking Python installation..."

PYTHON_CMD=""
if command_exists python3; then
    if check_python_version python3; then
        PYTHON_CMD="python3"
        print_info "Found Python 3 ($(python3 --version))"
    else
        print_error "Python 3.6 or higher is required. Found: $(python3 --version)"
        exit 1
    fi
elif command_exists python; then
    if check_python_version python; then
        PYTHON_CMD="python"
        print_info "Found Python ($(python --version))"
    else
        print_error "Python 3.6 or higher is required. Found: $(python --version)"
        exit 1
    fi
else
    print_error "Python is not installed or not in PATH"
    print_error "Please install Python 3.6 or higher and try again"
    exit 1
fi

# Check if pip is available
print_info "Checking pip installation..."
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    print_error "pip is not available. Please install pip and try again"
    exit 1
else
    print_info "pip is available"
fi

# Check required Python modules
print_info "Checking required Python modules..."
required_modules=("json" "os" "sys" "getpass")
missing_modules=()

for module in "${required_modules[@]}"; do
    if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
        missing_modules+=("$module")
    fi
done

if [ ${#missing_modules[@]} -ne 0 ]; then
    print_error "Missing required Python modules: ${missing_modules[*]}"
    print_info "Attempting to install missing modules..."
    for module in "${missing_modules[@]}"; do
        if ! $PYTHON_CMD -m pip install "$module"; then
            print_error "Failed to install $module"
            exit 1
        fi
    done
fi

# Check if setup directory exists
SETUP_DIR="$(dirname "$0")/setup_tool"
if [ ! -d "$SETUP_DIR" ]; then
    print_error "Setup directory not found: $SETUP_DIR"
    exit 1
fi

# Check if setup.py exists
SETUP_TOOL="$SETUP_DIR/setup_tool.py"
if [ ! -f "$SETUP_TOOL" ]; then
    print_error "Setup tool not found: $SETUP_TOOL"
    exit 1
fi

print_info "All validation checks passed!"
print_info "Launching setup tool..."

# Change to the source directory
cd "$(dirname "$0")"

# Execute the Python setup tool
exec $PYTHON_CMD setup_tool/setup_tool.py "$@"
