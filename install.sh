#!/bin/sh

# 8bitify Install Script

# Colors for output (using tput for portability if available, otherwise fallback)
if command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    BLUE=$(tput setaf 4)
    NC=$(tput sgr0)
else
    RED=''
    GREEN=''
    BLUE=''
    NC=''
fi

echo "${BLUE}Installing 8bitify...${NC}"

# 1. Dependency Checks
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "${RED}Error: ffmpeg is not installed.${NC}"
    echo "Please install it first:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "${RED}Error: git is not installed (required for installation).${NC}"
    exit 1
fi

# 2. Setup Installation Directory
# If setup.py is present, we are running locally (git clone mode).
# If not, we are running via curl, so we need to clone to a temp dir.
CLEANUP_REQUIRED=false
INSTALL_DIR="."

if [ ! -f "setup.py" ]; then
    echo "${BLUE}Fetching source code...${NC}"
    # mktemp -d is mostly portable, works on macOS/Linux
    INSTALL_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t '8bitify')
    git clone --depth 1 https://github.com/IFAKA/8bitify.git "$INSTALL_DIR"
    CLEANUP_REQUIRED=true
fi

# 3. Install
cd "$INSTALL_DIR" || exit 1

echo "${BLUE}Installing Python dependencies...${NC}"
# Try installing with --break-system-packages (for managed python environments)
# Fallback to standard install if that flag isn't supported/needed.
if python3 -m pip install . --break-system-packages >/dev/null 2>&1; then
    SUCCESS=true
elif python3 -m pip install .; then
    SUCCESS=true
else
    SUCCESS=false
fi

# 4. Cleanup & Verify
if [ "$CLEANUP_REQUIRED" = true ]; then
    cd ..
    rm -rf "$INSTALL_DIR"
fi

if [ "$SUCCESS" = true ]; then
    echo "${GREEN}8bitify successfully installed! 👾${NC}"
    echo "Run it by typing: 8bitify"
else
    echo "${RED}Installation failed. Please check your python/pip configuration.${NC}"
    exit 1
fi
