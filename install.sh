#!/bin/bash

# 8bitify Install Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing 8bitify...${NC}"

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: ffmpeg is not installed.${NC}"
    echo "Please install it first:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

# Install the package using pip
# We use --user to avoid needing sudo and -e for editable if they want to tweak, 
# but for a clean install we'll just do a standard install.
echo -e "${BLUE}Installing Python dependencies...${NC}"
python3 -m pip install . --break-system-packages 2>/dev/null || python3 -m pip install .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}8bitify successfully installed!${NC}"
    echo "You can now run it by typing: 8bitify"
else
    echo -e "${RED}Installation failed. You might need to install with pip manually.${NC}"
    exit 1
fi
