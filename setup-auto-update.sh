#!/bin/bash

# Setup auto-update cron job for InstaLeBot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚙️  Setting up auto-update for InstaLeBot${NC}"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UPDATE_SCRIPT="$SCRIPT_DIR/update.sh"

# Make update script executable
chmod +x "$UPDATE_SCRIPT"

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo -e "${RED}❌ crontab is not installed.${NC}"
    echo "   Please install cron: sudo apt install cron"
    exit 1
fi

# Ask for update frequency
echo "Select update frequency:"
echo "  1) Every 5 minutes"
echo "  2) Every 15 minutes"
echo "  3) Every 30 minutes"
echo "  4) Every hour"
echo "  5) Every 6 hours"
echo "  6) Every 12 hours"
echo "  7) Once daily (at midnight)"
echo "  8) Custom (enter cron expression)"
echo ""
read -p "Enter choice [1-8]: " choice

case $choice in
    1)
        CRON_SCHEDULE="*/5 * * * *"
        DESC="every 5 minutes"
        ;;
    2)
        CRON_SCHEDULE="*/15 * * * *"
        DESC="every 15 minutes"
        ;;
    3)
        CRON_SCHEDULE="*/30 * * * *"
        DESC="every 30 minutes"
        ;;
    4)
        CRON_SCHEDULE="0 * * * *"
        DESC="every hour"
        ;;
    5)
        CRON_SCHEDULE="0 */6 * * *"
        DESC="every 6 hours"
        ;;
    6)
        CRON_SCHEDULE="0 */12 * * *"
        DESC="every 12 hours"
        ;;
    7)
        CRON_SCHEDULE="0 0 * * *"
        DESC="once daily at midnight"
        ;;
    8)
        echo ""
        echo "Enter cron expression (minute hour day month weekday):"
        echo "Example: '*/10 * * * *' for every 10 minutes"
        read -p "Cron expression: " CRON_SCHEDULE
        DESC="custom schedule"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

# Create cron job
CRON_JOB="$CRON_SCHEDULE cd $SCRIPT_DIR && $UPDATE_SCRIPT >> $SCRIPT_DIR/logs/update.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Auto-update cron job already exists.${NC}"
    read -p "Replace existing cron job? (y/n): " replace
    if [ "$replace" = "y" ] || [ "$replace" = "Y" ]; then
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT" | crontab -
        echo -e "${GREEN}✅ Removed existing cron job${NC}"
    else
        echo -e "${YELLOW}⚠️  Keeping existing cron job. Exiting.${NC}"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo -e "${GREEN}✅ Auto-update configured successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Details:${NC}"
echo "   Schedule: $DESC ($CRON_SCHEDULE)"
echo "   Script: $UPDATE_SCRIPT"
echo "   Logs: $SCRIPT_DIR/logs/update.log"
echo ""
echo -e "${BLUE}📝 View cron jobs:${NC}"
echo "   crontab -l"
echo ""
echo -e "${BLUE}🗑️  Remove auto-update:${NC}"
echo "   crontab -e  (then delete the line)"
echo "   or run: crontab -l | grep -v '$UPDATE_SCRIPT' | crontab -"
echo ""
echo -e "${BLUE}📋 View update logs:${NC}"
echo "   tail -f $SCRIPT_DIR/logs/update.log"
echo ""

