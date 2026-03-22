#!/bin/sh

# 8bitify Uninstall Script

# Colors for output
if command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    NC=$(tput sgr0)
else
    RED=''
    GREEN=''
    NC=''
fi

echo "${RED}Uninstalling 8bitify...${NC}"

# Uninstall via pip
python3 -m pip uninstall -y 8bitify

# Remove any leftover __pycache__ or build artifacts if they exist in the source dir
# (Assuming they ran it from the source dir or installed in a way that left traces)
# If we were truly "no trace", we'd also remove the repo folder if we cloned it.

echo "${GREEN}8bitify has been uninstalled.${NC}"
echo "To remove the source files (if downloaded manually), run: rm -rf 8bitify"
