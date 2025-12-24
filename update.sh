#!/bin/bash

# Auto-update script for InstaLeBot
# This script pulls latest code and restarts the container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Checking for updates...${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Cannot check for updates.${NC}"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Not a git repository. Skipping update check.${NC}"
    exit 0
fi

# Fetch latest changes
echo -e "${BLUE}📥 Fetching latest changes from remote...${NC}"
git fetch origin
echo -e "${BLUE}   Fetch completed. Current HEAD:${NC}"
git log -1 --oneline

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
REMOTE_BRANCH="origin/$CURRENT_BRANCH"

# Check if there are updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "$REMOTE_BRANCH" 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}⚠️  Remote branch not found. Skipping update.${NC}"
    exit 0
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅ Already up to date!${NC}"
    exit 0
fi

echo -e "${YELLOW}📦 New updates available!${NC}"
echo -e "${BLUE}   Local:  $LOCAL${NC}"
echo -e "${BLUE}   Remote: $REMOTE${NC}"

# Check if container is running
CONTAINER_RUNNING=$(docker ps --format '{{.Names}}' | grep -q "^instalebot$" && echo "yes" || echo "no")
echo -e "${BLUE}📊 Container status: $CONTAINER_RUNNING${NC}"

if [ "$CONTAINER_RUNNING" = "yes" ]; then
    echo -e "${BLUE}🛑 Stopping container...${NC}"
    docker compose down
    echo -e "${BLUE}   Waiting for container to fully stop...${NC}"
    sleep 2
    echo -e "${GREEN}   ✅ Container stopped${NC}"
fi

# Remove old image to force rebuild
echo -e "${BLUE}🗑️  Removing old image to ensure fresh build...${NC}"
docker rmi instalebot-instalebot 2>/dev/null || echo "   (No old image found)"

# Pull latest code
echo -e "${BLUE}⬇️  Pulling latest code...${NC}"
git pull origin "$CURRENT_BRANCH"

# Check what files changed
echo -e "${BLUE}📝 Files changed in this update:${NC}"
CHANGED_FILES=$(git diff --name-only HEAD@{1} HEAD)
echo "$CHANGED_FILES" | sed 's/^/   /'

# Rebuild image if critical files changed OR if any Python code changed
if echo "$CHANGED_FILES" | grep -qE "Dockerfile|requirements.txt|docker-compose.yml|\.py$|handlers/|services/|utils/"; then
    echo -e "${BLUE}🔨 Rebuilding Docker image (code or dependencies changed)...${NC}"
    echo -e "${YELLOW}   Using --no-cache to ensure fresh build...${NC}"
    docker compose build --no-cache
else
    echo -e "${GREEN}✅ No code changes detected. Skipping rebuild.${NC}"
fi

# Start container
echo -e "${BLUE}🚀 Starting container...${NC}"
docker compose up -d
sleep 3

# Verify container is running
echo -e "${BLUE}📊 Verifying container status...${NC}"
if docker ps --format '{{.Names}}' | grep -q "^instalebot$"; then
    echo -e "${GREEN}   ✅ Container is running${NC}"
    echo -e "${BLUE}   Image ID:${NC}"
    docker inspect instalebot --format='   {{.Image}}'
    echo -e "${BLUE}   Container ID:${NC}"
    docker inspect instalebot --format='   {{.ID}}'
else
    echo -e "${RED}   ❌ Container failed to start!${NC}"
    echo -e "${BLUE}   Checking logs:${NC}"
    docker compose logs --tail=20
    exit 1
fi

echo -e "${GREEN}✅ Update complete!${NC}"
echo -e "${BLUE}📋 View logs with: docker compose logs -f${NC}"

