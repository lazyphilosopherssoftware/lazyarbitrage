#!/bin/bash

# LazyArbitrage Test Runner
# Activates virtual environment and runs the test suite

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}LazyArbitrage Test Runner${NC}"
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

echo -e "${GREEN}SUCCESS: Running test suite...${NC}"
echo "==============================="
echo ""

# Run the tests
python -m unittest discover -s test -p "test_*.py" -v

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}SUCCESS: All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}FAILURE: Some tests failed${NC}"
    exit 1
fi