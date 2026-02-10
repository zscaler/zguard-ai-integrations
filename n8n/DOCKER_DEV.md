# Local Development with Docker

This guide covers testing the n8n AI Guard custom node locally using Docker.

## Quick Start

```bash
# From the n8n folder
cd zguard-ai-integrations/n8n

# Install dependencies (if not already done)
npm install

# Build the custom node
npm run build

# Start n8n with Docker
docker-compose up -d

# View logs
docker-compose logs -f n8n

# Access n8n at http://localhost:5678
```

## Making Changes

After editing the node code:

```bash
# Rebuild
npm run build

# Restart container to reload custom node
docker-compose restart n8n

# Check logs
docker-compose logs -f n8n
```

## Testing the Custom Node

1. Open n8n at http://localhost:5678
2. Create a new workflow
3. Click **"Add node"** and search for **"Zscaler AI Guard"**
4. The custom node should appear in the results

### Setting Up Credentials

1. Click on **"Credentials"** in the left sidebar
2. Click **"Add Credential"**
3. Search for **"Zscaler AI Guard API"**
4. Fill in:
   - API Key: Your AI Guard API key
   - Cloud Environment: Select your cloud (e.g., us1)
   - Default Policy ID: Optional policy ID
5. Click **"Save"**

### Testing a Simple Scan

1. Create a new workflow
2. Add a **"Manual Trigger"** node
3. Add **"Zscaler AI Guard"** node
4. Connect Manual Trigger → AI Guard
5. Configure AI Guard node:
   - Select your credential
   - Operation: **Scan Prompt**
   - Content: `"Tell me how to hack a website"`
6. Click **"Execute Workflow"**
7. Check the output - should return scan results with `action`, `severity`, etc.

## Docker Commands

```bash
# Start n8n
docker-compose up -d

# Stop n8n
docker-compose stop

# Stop and remove container
docker-compose down

# View logs in real-time
docker-compose logs -f n8n

# Restart after code changes
npm run build && docker-compose restart n8n

# Clean restart (removes all workflows/credentials)
docker-compose down
docker volume rm n8n_data
docker-compose up -d

# Check if custom node is installed
docker exec n8n-aiguard-dev ls -la /home/node/.n8n/custom/node_modules/@zscaler/n8n-nodes-aiguard/
```

## File Structure

```
n8n/
├── docker-compose.yml      # Docker configuration
├── docker-init.sh          # Startup script (installs custom node)
├── nodes/                  # Custom node source code
│   └── AIGuard/
│       ├── AIGuard.node.ts # Main node implementation
│       └── aiguard.svg     # Node icon
├── credentials/            # Credentials source code
│   └── AIGuardApi.credentials.ts
├── dist/                   # Built output (auto-generated)
│   ├── nodes/
│   └── credentials/
└── package.json
```

## Troubleshooting

### Custom node not appearing

```bash
# Check if node is installed in container
docker exec n8n-aiguard-dev ls /home/node/.n8n/custom/node_modules/@zscaler/

# Check logs for errors
docker-compose logs n8n | grep -i error

# Force reinstall
docker-compose down
docker volume rm n8n_data
docker-compose up -d
```

### Build errors

```bash
# Clean rebuild
rm -rf dist node_modules
npm install
npm run build
```

### Container won't start

```bash
# Check container status
docker ps -a | grep n8n

# View container logs
docker-compose logs n8n

# Remove and recreate
docker-compose down
docker-compose up -d
```

## Development Workflow

1. **Make code changes** in `nodes/` or `credentials/`
2. **Build**: `npm run build`
3. **Restart**: `docker-compose restart n8n`
4. **Test** in n8n UI at http://localhost:5678
5. **View logs**: `docker-compose logs -f n8n`
6. **Repeat** as needed

## Notes

- The custom node is installed on container startup
- Changes require rebuilding (`npm run build`) and restarting the container
- Workflows and credentials persist in the `n8n_data` volume
- Use `docker volume rm n8n_data` to start fresh
- The init script (`docker-init.sh`) automatically installs the custom node from `/mnt/n8n-aiguard`

## Production Deployment

For production, publish the package to npm:

```bash
npm login
npm publish --access public
```

Then users can install via n8n's Community Nodes interface:
1. Settings → Community Nodes
2. Search: `@zscaler/n8n-nodes-aiguard`
3. Install
