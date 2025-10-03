#!/bin/bash

# LazyArbitrage Bot Runner
# Activates virtual environment and runs the arbitrage bot

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}LazyArbitrage Bot Runner${NC}"
echo "==============================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found at ./venv${NC}"
    echo -e "${YELLOW}Please create it with: python -m venv venv${NC}"
    exit 1
fi

# Check if venv has been activated before (has packages)
if [ ! -f "venv/pyvenv.cfg" ]; then
    echo -e "${RED}ERROR: Virtual environment appears to be corrupted${NC}"
    exit 1
fi

echo -e "${GREEN}SUCCESS: Found virtual environment${NC}"

# Activate virtual environment
echo -e "${YELLOW}INFO: Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
echo -e "${YELLOW}INFO: Checking dependencies...${NC}"
if ! python -c "import ccxt, jsonc_parser" 2>/dev/null; then
    echo -e "${RED}ERROR: Missing required packages${NC}"
    echo -e "${YELLOW}INFO: Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if config file exists
if [ ! -f "config.jsonc" ]; then
    echo -e "${YELLOW}WARNING: No config.jsonc found${NC}"
    if [ -f "config.example.jsonc" ]; then
        echo -e "${YELLOW}INFO: Copy config.example.jsonc to config.jsonc and configure your exchanges${NC}"
    else
        echo -e "${RED}ERROR: No config.example.jsonc found either${NC}"
    fi
    echo -e "${YELLOW}INFO: Continuing anyway (may fail if config is required)...${NC}"
fi

echo -e "${GREEN}SUCCESS: Starting arbitrage bot...${NC}"
echo "==============================="
echo ""

# Run the bot
python main.py

# Note: The bot runs indefinitely, so this line won't be reached unless it exits
echo ""
echo -e "${YELLOW}INFO: Bot stopped${NC}"