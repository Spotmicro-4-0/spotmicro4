#!/bin/bash

# SpotmicroAI Development Environment Setup
# This script sets up the local development environment for developers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements-dev.txt"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=8

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "SpotmicroAI Development Environment Setup"
    echo "Sets up Python virtual environment and installs development dependencies"
    echo
    echo "OPTIONS:"
    echo "  --clean       Remove existing virtual environment and recreate"
    echo "  --upgrade     Upgrade all packages to latest versions"
    echo "  --version     Show version information"
    echo "  -h, --help    Show this help message"
    echo
    echo "Examples:"
    echo "  $0                # Setup development environment"
    echo "  $0 --clean        # Remove and recreate virtual environment"
    echo "  $0 --upgrade      # Upgrade all packages"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    local version=$($python_cmd --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "0.0.0")
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -eq $MIN_PYTHON_MAJOR ] && [ "$minor" -ge $MIN_PYTHON_MINOR ]; then
        echo "$version"
        return 0
    elif [ "$major" -gt $MIN_PYTHON_MAJOR ]; then
        echo "$version"
        return 0
    else
        echo "$version"
        return 1
    fi
}

# Parse command line arguments
CLEAN_MODE=false
UPGRADE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        --upgrade)
            UPGRADE_MODE=true
            shift
            ;;
        --version)
            echo "SpotmicroAI Development Environment Setup v1.0"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Print banner
echo "============================================================"
print_info "SpotmicroAI Development Environment Setup"
echo "============================================================"
echo

# Step 1: Validate Python installation
print_step "Validating Python installation..."

PYTHON_CMD=""
PYTHON_VERSION=""

if command_exists python3; then
    PYTHON_VERSION=$(check_python_version python3)
    if [ $? -eq 0 ]; then
        PYTHON_CMD="python3"
        print_success "Found Python 3: version $PYTHON_VERSION"
    else
        print_error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
elif command_exists python; then
    PYTHON_VERSION=$(check_python_version python)
    if [ $? -eq 0 ]; then
        PYTHON_CMD="python"
        print_success "Found Python: version $PYTHON_VERSION"
    else
        print_error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python is not installed or not in PATH"
    print_error "Please install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} or higher"
    echo
    echo "Installation instructions:"
    echo "  - Windows: Download from https://www.python.org/downloads/"
    echo "  - macOS: brew install python3"
    echo "  - Linux: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Step 2: Validate pip installation
print_step "Validating pip installation..."

if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    print_error "pip is not available"
    print_error "Please install pip:"
    echo "  $PYTHON_CMD -m ensurepip --upgrade"
    exit 1
else
    PIP_VERSION=$($PYTHON_CMD -m pip --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    print_success "pip is available: version $PIP_VERSION"
fi

# Step 3: Validate venv module
print_step "Validating venv module..."

if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1; then
    print_error "venv module is not available"
    print_error "Please install python3-venv:"
    echo "  - Linux: sudo apt install python3-venv"
    echo "  - Windows/macOS: Should be included with Python"
    exit 1
else
    print_success "venv module is available"
fi

# Step 4: Check for requirements file
print_step "Checking for requirements file..."

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    print_error "Requirements file not found: $REQUIREMENTS_FILE"
    print_warning "Creating a basic requirements-dev.txt file..."
    cat > "$REQUIREMENTS_FILE" << EOF
# Development dependencies
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
flake8>=4.0.0
pylint>=2.12.0
mypy>=0.931
isort>=5.10.0

# Project dependencies
# Add your project dependencies here
EOF
    print_info "Created $REQUIREMENTS_FILE with common development tools"
    print_warning "Please review and add your project-specific dependencies"
fi

# Step 5: Handle virtual environment
print_step "Setting up virtual environment..."

if [ "$CLEAN_MODE" = true ] && [ -d "$VENV_DIR" ]; then
    print_warning "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
    print_success "Existing virtual environment removed"
fi

if [ -d "$VENV_DIR" ]; then
    print_info "Virtual environment already exists: $VENV_DIR"
else
    print_info "Creating virtual environment: $VENV_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment created successfully"
fi

# Step 6: Activate virtual environment
print_step "Activating virtual environment..."

# Detect OS and activate accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash or similar)
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
elif [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
    # macOS or Linux
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    print_error "Activation script not found: $ACTIVATE_SCRIPT"
    exit 1
fi

source "$ACTIVATE_SCRIPT"

if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_success "Virtual environment activated"

# Verify we're in the virtual environment
VENV_PYTHON=$(which python)
print_info "Using Python: $VENV_PYTHON"

# Step 7: Upgrade pip in virtual environment
print_step "Upgrading pip in virtual environment..."

python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1

if [ $? -ne 0 ]; then
    print_warning "Failed to upgrade pip, setuptools, or wheel"
else
    print_success "pip, setuptools, and wheel upgraded"
fi

# Step 8: Install/upgrade requirements
if [ "$UPGRADE_MODE" = true ]; then
    print_step "Upgrading all packages from $REQUIREMENTS_FILE..."
    python -m pip install --upgrade -r "$REQUIREMENTS_FILE"
else
    print_step "Installing packages from $REQUIREMENTS_FILE..."
    python -m pip install -r "$REQUIREMENTS_FILE"
fi

if [ $? -ne 0 ]; then
    print_error "Failed to install requirements"
    print_error "Please check $REQUIREMENTS_FILE for errors"
    exit 1
fi

print_success "All packages installed successfully"

# Step 9: Display installed packages
echo
print_step "Installed packages:"
python -m pip list

# Step 10: Final summary
echo
echo "============================================================"
print_success "Development environment setup complete!"
echo "============================================================"
echo
print_info "Virtual environment: $VENV_DIR"
print_info "Python version: $PYTHON_VERSION"
print_info "Requirements file: $REQUIREMENTS_FILE"
echo
print_info "To activate the virtual environment manually:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  source $VENV_DIR/Scripts/activate"
else
    echo "  source $VENV_DIR/bin/activate"
fi
echo
print_info "To deactivate the virtual environment:"
echo "  deactivate"
echo
print_info "The virtual environment is currently activated in this shell."
print_info "You can now run your development commands."
echo

# Keep shell in activated state
exec $SHELL
