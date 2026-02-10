#!/bin/sh
set -e

echo "Installing AI Guard custom node..."
mkdir -p /home/node/.n8n/custom
cd /home/node/.n8n/custom

# Install the custom node from mounted directory if not already installed
if [ ! -d "node_modules/@zscaler/n8n-nodes-aiguard" ]; then
  echo "Installing @zscaler/n8n-nodes-aiguard from /mnt/n8n-aiguard..."
  npm install /mnt/n8n-aiguard --no-save --legacy-peer-deps
  echo "Custom node installed successfully!"
else
  echo "Custom node already installed, skipping..."
fi

echo "Starting n8n..."
exec tini -- /docker-entrypoint.sh "$@"
