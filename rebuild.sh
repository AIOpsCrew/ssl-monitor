#!/bin/bash
#
# SSL Certificate Monitor - Rebuild Script
# This script rebuilds and restarts the Docker container
#

set -e  # Exit on any error

echo "========================================="
echo "SSL Certificate Monitor - Rebuild Script"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Restarting with sudo..."
    sudo "$0" "$@"
    exit $?
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Step 1: Stop the container
echo "[1/5] Stopping containers..."
docker compose down
echo "✓ Containers stopped"
echo ""

# Step 2: Optional - Delete data to reload from seed file
read -p "Delete data/websites.json to reload from seed file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f data/websites.json ]; then
        rm -f data/websites.json
        echo "✓ Deleted data/websites.json"
    else
        echo "✓ data/websites.json already deleted"
    fi
else
    echo "✓ Keeping existing data/websites.json"
fi
echo ""

# Step 3: Build the image
echo "[2/5] Building Docker image..."
docker compose build
echo "✓ Image built successfully"
echo ""

# Step 4: Start the containers
echo "[3/5] Starting containers..."
docker compose up -d
echo "✓ Containers started"
echo ""

# Step 5: Wait a moment for startup
echo "[4/5] Waiting for application to start..."
sleep 3
echo "✓ Ready"
echo ""

# Step 6: Show logs
echo "[5/5] Showing recent logs..."
echo "========================================="
docker compose logs --tail=20 ssl-monitor
echo "========================================="
echo ""

# Show status
echo "Container status:"
docker compose ps
echo ""

echo "✓ Rebuild complete!"
echo ""
echo "Application is running at: http://localhost:5000"
echo ""
echo "To view logs: docker compose logs -f ssl-monitor"
echo "To stop: docker compose down"
echo ""
