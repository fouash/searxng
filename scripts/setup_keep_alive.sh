#!/bin/bash
# Setup script for keep-alive cron job
# Usage: bash scripts/setup_keep_alive.sh https://your-render-instance.onrender.com

set -e

if [ $# -eq 0 ]; then
    echo "Usage: bash scripts/setup_keep_alive.sh https://your-render-instance.onrender.com"
    echo ""
    echo "Examples:"
    echo "  bash scripts/setup_keep_alive.sh https://my-searxng.onrender.com"
    echo "  bash scripts/setup_keep_alive.sh my-searxng.onrender.com"
    exit 1
fi

RENDER_URL="$1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( dirname "$SCRIPT_DIR" )"

# Ensure URL has proper format
if [[ ! "$RENDER_URL" =~ ^https?:// ]]; then
    RENDER_URL="https://$RENDER_URL"
fi

echo "================================"
echo "SearXNG Keep-Alive Setup"
echo "================================"
echo ""
echo "Instance URL: $RENDER_URL"
echo "Script: $PROJECT_DIR/scripts/keep_alive.py"
echo ""

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
touch "$PROJECT_DIR/logs/keep_alive.log"

echo "1. Testing connection..."
python3 "$PROJECT_DIR/scripts/keep_alive.py" "$RENDER_URL"

if [ $? -eq 0 ]; then
    echo "✓ Connection successful!"
else
    echo "✗ Connection failed. Check the URL and try again."
    exit 1
fi

echo ""
echo "2. Adding to crontab..."

# Check if already in crontab
CRON_ENTRY="*/10 * * * * cd $PROJECT_DIR && python3 scripts/keep_alive.py $RENDER_URL >> logs/keep_alive.log 2>&1"

if crontab -l 2>/dev/null | grep -q "keep_alive.py"; then
    echo "⚠️  Cron entry already exists. Updating..."
    (crontab -l 2>/dev/null | grep -v "keep_alive.py"; echo "$CRON_ENTRY") | crontab -
else
    echo "Adding new cron entry..."
    (crontab -l 2>/dev/null || echo ""; echo "$CRON_ENTRY") | crontab -
fi

echo "✓ Cron job added!"
echo ""
echo "3. Verifying..."
echo ""
echo "Current cron jobs:"
crontab -l | grep "keep_alive" || echo "Not found (this is normal)"

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "✓ Cron job will ping your instance every 10 minutes"
echo "✓ Check logs: tail -f $PROJECT_DIR/logs/keep_alive.log"
echo "✓ Dashboard: $RENDER_URL/keep-alive"
echo ""
echo "To remove the cron job:"
echo "  crontab -e  # and delete the keep_alive line"
echo ""
