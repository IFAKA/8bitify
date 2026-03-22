#!/bin/bash

# 8bitify Uninstall Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}Uninstalling 8bitify...${NC}"

# Uninstall via pip
python3 -m pip uninstall -y 8bitify

# Remove any leftover __pycache__ or build artifacts if they exist in the source dir
# (Assuming they ran it from the source dir or installed in a way that left traces)
# If we were truly "no trace", we'd also remove the repo folder if we cloned it.

echo -e "${GREEN}8bitify has been uninstalled.${NC}"
echo "To remove the source files, simply run: rm -rf mp3-to-8bit"
