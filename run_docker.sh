#!/bin/bash

# SecurePixel Docker Launcher for Linux/Mac
# ==========================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================="
echo "   🔐 SecurePixel - Docker Launcher"
echo "========================================="
echo -e "${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running!${NC}"
    echo "Please start Docker Desktop or Docker daemon"
    exit 1
fi

# Create shared directory
mkdir -p shared
echo -e "${GREEN}✅ Created shared directory${NC}"

# Check X11 for GUI
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - check DISPLAY
    if [ -z "$DISPLAY" ]; then
        echo -e "${YELLOW}⚠️ DISPLAY not set. GUI may not work.${NC}"
        export DISPLAY=:0
    fi
    # Allow X11 connections
    xhost +local:docker &> /dev/null
    echo -e "${GREEN}✅ X11 forwarding enabled${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - check XQuartz
    if ! command -v xquartz &> /dev/null; then
        echo -e "${YELLOW}⚠️ XQuartz not found. Install with: brew install --cask xquartz${NC}"
    else
        echo -e "${GREEN}✅ XQuartz detected${NC}"
    fi
fi

# Menu
echo -e "\n${YELLOW}Select option:${NC}"
echo " 1) 🚀 Run SecurePixel application"
echo " 2) 🧪 Run tests"
echo " 3) 🐚 Open shell in container"
echo " 4) 📊 View logs"
echo " 5) 🛑 Stop all containers"
echo " 6) 🗑️  Clean up (remove containers and volumes)"
echo " 7) 🚪 Exit"
echo

read -p "Enter choice (1-7): " choice

case $choice in
    1)
        echo -e "\n${BLUE}🚀 Starting SecurePixel...${NC}"
        docker-compose up app
        ;;
    2)
        echo -e "\n${BLUE}🧪 Running tests...${NC}"
        docker-compose --profile tests up test-runner
        echo -e "\n${YELLOW}Test reports saved in ./test-reports/${NC}"
        ;;
    3)
        echo -e "\n${BLUE}🐚 Opening shell in app container...${NC}"
        docker-compose run --rm app /bin/bash
        ;;
    4)
        echo -e "\n${BLUE}📊 Showing logs...${NC}"
        docker-compose logs -f
        ;;
    5)
        echo -e "\n${BLUE}🛑 Stopping containers...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Containers stopped${NC}"
        ;;
    6)
        echo -e "\n${YELLOW}⚠️ This will remove all containers and volumes!${NC}"
        read -p "Are you sure? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            docker-compose down -v
            echo -e "${GREEN}✅ Cleanup complete${NC}"
        fi
        ;;
    7)
        echo -e "${BLUE}Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
