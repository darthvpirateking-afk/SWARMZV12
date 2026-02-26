#!/usr/bin/env bash
# SWARMZ - One-Command Startup Script (Unix/Linux/macOS)
# Usage: ./RUN.sh [test|demo|api|help]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  SWARMZ - Operator-Sovereign System${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Parse arguments
MODE="interactive"
if [ "$1" == "test" ] || [ "$1" == "--test" ]; then
    MODE="test"
elif [ "$1" == "demo" ] || [ "$1" == "--demo" ]; then
    MODE="demo"
elif [ "$1" == "api" ] || [ "$1" == "--api" ]; then
    MODE="api"
elif [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo -e "${YELLOW}Usage: ./RUN.sh [options]${NC}"
    echo ""
    echo -e "${GREEN}Options:${NC}"
    echo "  (no args)   Start interactive CLI mode"
    echo "  test        Run test suite"
    echo "  demo        Run demo examples"
    echo "  api         Start API server (requires FastAPI)"
    echo "  help        Show this help message"
    echo ""
    exit 0
fi

# Check Python installation
echo -e "${YELLOW}[1/5] Checking Python installation...${NC}"
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1)
        if [[ $version =~ Python\ 3\.([6-9]|[1-9][0-9]) ]]; then
            PYTHON_CMD=$cmd
            echo -e "  ${GREEN}✓ Found: $version${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "  ${RED}✗ Error: Python 3.6+ not found${NC}"
    echo -e "  ${RED}Please install Python from https://www.python.org/${NC}"
    exit 1
fi

# Check/create virtual environment
echo -e "${YELLOW}[2/5] Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "  ${CYAN}Creating new virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "  ${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}[3/5] Activating virtual environment...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "  ${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "  ${YELLOW}⚠ Activation script not found, continuing...${NC}"
fi

# Install dependencies
echo -e "${YELLOW}[4/5] Installing dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    PIP_CMD="venv/bin/pip"
    if [ ! -f "$PIP_CMD" ]; then
        PIP_CMD="pip"
    fi
    
    $PIP_CMD install -q -r requirements.txt 2>&1 > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "  ${YELLOW}⚠ Some dependencies may have failed (optional packages)${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ requirements.txt not found, skipping...${NC}"
fi

# Determine Python executable
PYTHON_EXE="venv/bin/python"
if [ ! -f "$PYTHON_EXE" ]; then
    PYTHON_EXE=$PYTHON_CMD
fi

# Run appropriate command
echo -e "${YELLOW}[5/5] Starting SWARMZ...${NC}"
echo ""

case $MODE in
    test)
        echo -e "${CYAN}Running test suite...${NC}"
        echo -e "${CYAN}============================================${NC}"
        $PYTHON_EXE test_swarmz.py
        ;;
    demo)
        echo -e "${CYAN}Running demo examples...${NC}"
        echo -e "${CYAN}============================================${NC}"
        $PYTHON_EXE examples.py
        ;;
    api)
        echo -e "${CYAN}Starting API server...${NC}"
        echo -e "${CYAN}============================================${NC}"
        $PYTHON_EXE run_swarmz.py
        ;;
    *)
        echo -e "${CYAN}Starting interactive CLI...${NC}"
        echo -e "${CYAN}============================================${NC}"
        echo -e "${GREEN}Available commands:${NC}"
        echo "  list          - List all capabilities"
        echo "  task <name>   - Execute a task"
        echo "  audit         - View audit log"
        echo "  exit          - Exit interactive mode"
        echo ""
        echo -e "${YELLOW}Quick start:${NC}"
        echo "  swarmz> list"
        echo "  swarmz> task echo {\"message\": \"Hello!\"}"
        echo ""
        echo -e "${CYAN}============================================${NC}"
        echo ""
        $PYTHON_EXE swarmz_cli.py --interactive
        ;;
esac

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  SWARMZ session ended${NC}"
echo -e "${CYAN}============================================${NC}"
