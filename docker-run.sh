#!/bin/bash

# Docker run script for InstaLeBot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 InstaLeBot Docker Deployment${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}   Please edit .env file and add your credentials:${NC}"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - RAPIDAPI_KEY"
        echo ""
        echo "   You can edit it with: nano .env"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        echo -e "${RED}❌ .env.example not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Create necessary directories
mkdir -p downloads logs

# Function to check if container is running
is_running() {
    docker ps --format '{{.Names}}' | grep -q "^instalebot$"
}

# Parse command line arguments
case "${1:-}" in
    build)
        echo -e "${GREEN}🔨 Building Docker image...${NC}"
        docker compose build
        echo -e "${GREEN}✅ Build complete!${NC}"
        ;;
    start)
        if is_running; then
            echo -e "${YELLOW}⚠️  Container is already running${NC}"
        else
            echo -e "${GREEN}🚀 Starting container...${NC}"
            docker compose up -d
            echo -e "${GREEN}✅ Container started!${NC}"
            echo ""
            echo "View logs with: ./docker-run.sh logs"
        fi
        ;;
    stop)
        if is_running; then
            echo -e "${YELLOW}🛑 Stopping container...${NC}"
            docker compose down
            echo -e "${GREEN}✅ Container stopped!${NC}"
        else
            echo -e "${YELLOW}⚠️  Container is not running${NC}"
        fi
        ;;
    restart)
        echo -e "${YELLOW}🔄 Restarting container...${NC}"
        docker compose restart
        echo -e "${GREEN}✅ Container restarted!${NC}"
        ;;
    logs)
        echo -e "${GREEN}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker compose logs -f
        ;;
    status)
        if is_running; then
            echo -e "${GREEN}✅ Container is running${NC}"
            docker compose ps
        else
            echo -e "${RED}❌ Container is not running${NC}"
        fi
        ;;
    shell)
        echo -e "${GREEN}🐚 Opening shell in container...${NC}"
        docker compose exec instalebot /bin/bash || docker compose exec instalebot /bin/sh
        ;;
    clean)
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker compose down -v
        docker rmi instalebot-instalebot 2>/dev/null || true
        echo -e "${GREEN}✅ Cleanup complete!${NC}"
        ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|shell|clean}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Start the container"
        echo "  stop     - Stop the container"
        echo "  restart  - Restart the container"
        echo "  logs     - Show container logs"
        echo "  status   - Show container status"
        echo "  shell    - Open shell in container"
        echo "  clean    - Stop and remove container, remove image"
        exit 1
        ;;
esac

