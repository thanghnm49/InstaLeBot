# Docker Deployment Guide

This guide covers deploying InstaLeBot using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose V2 (included with Docker Desktop or Docker Engine)
- At least 512MB RAM available
- Internet connection

## Installation

### Install Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**Or use package manager:**
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thanghnm49/InstaLeBot.git
   cd InstaLeBot
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Add your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   RAPIDAPI_KEY=your_key_here
   RAPIDAPI_HOST=instagram-api-fast-reliable-data-scraper.p.rapidapi.com
   ```

3. **Build and start:**
   ```bash
   chmod +x docker-run.sh
   ./docker-run.sh build
   ./docker-run.sh start
   ```

4. **Check logs:**
   ```bash
   ./docker-run.sh logs
   ```

## Docker Commands

### Using the helper script:

```bash
./docker-run.sh build      # Build the Docker image
./docker-run.sh start     # Start the container
./docker-run.sh stop      # Stop the container
./docker-run.sh restart   # Restart the container
./docker-run.sh logs      # View logs (follow mode)
./docker-run.sh status    # Check container status
./docker-run.sh shell     # Open shell in container
./docker-run.sh clean     # Remove container and image
```

### Using Docker Compose directly:

```bash
# Build image
docker compose build

# Start in background
docker compose up -d

# Start in foreground (see logs)
docker compose up

# Stop container
docker compose down

# Restart container
docker compose restart

# View logs
docker compose logs -f

# View logs (last 100 lines)
docker compose logs --tail=100

# Check status
docker compose ps

# Execute command in container
docker compose exec instalebot python3 bot.py

# Open shell
docker compose exec instalebot /bin/bash
```

### Using Docker directly:

```bash
# Build image
docker build -t instalebot .

# Run container
docker run -d \
  --name instalebot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/logs:/app/logs \
  instalebot

# View logs
docker logs -f instalebot

# Stop container
docker stop instalebot

# Remove container
docker rm instalebot
```

## Configuration

### Environment Variables

You can configure the bot using environment variables in `.env` file or pass them directly:

**Required:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `RAPIDAPI_KEY` - Your RapidAPI key

**Optional:**
- `RAPIDAPI_HOST` - RapidAPI host (default: instagram-api-fast-reliable-data-scraper.p.rapidapi.com)

### Volumes

The Docker setup mounts the following directories:

- `./downloads` → `/app/downloads` - Downloaded media files
- `./logs` → `/app/logs` - Application logs
- `./.env` → `/app/.env:ro` - Environment file (read-only)

### Ports

Currently, the bot uses polling, so no ports need to be exposed. If you switch to webhooks, you'll need to expose a port in `docker-compose.yml`.

## Updating the Bot

1. **Pull latest changes:**
   ```bash
   git pull
   ```

2. **Rebuild and restart:**
   ```bash
   ./docker-run.sh build
   ./docker-run.sh restart
   ```

Or with docker compose:
```bash
docker compose build
docker compose up -d
```

## Troubleshooting

### Container won't start

1. **Check logs:**
   ```bash
   docker compose logs
   ```

2. **Check environment variables:**
   ```bash
   docker compose exec instalebot env | grep -E "TELEGRAM|RAPIDAPI"
   ```

3. **Verify .env file:**
   ```bash
   cat .env
   ```

### Container keeps restarting

1. **Check logs for errors:**
   ```bash
   docker compose logs --tail=50
   ```

2. **Check container status:**
   ```bash
   docker compose ps
   ```

3. **Inspect container:**
   ```bash
   docker inspect instalebot
   ```

### Permission issues

If you have permission issues with mounted volumes:

```bash
# Fix downloads directory
sudo chown -R $USER:$USER downloads

# Fix logs directory
sudo chown -R $USER:$USER logs
```

### Out of memory

If the container runs out of memory:

1. **Check memory usage:**
   ```bash
   docker stats instalebot
   ```

2. **Increase Docker memory limit** in Docker Desktop settings or add memory limit in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M
   ```

### Network issues

If the bot can't connect to APIs:

1. **Test network connectivity:**
   ```bash
   docker compose exec instalebot ping -c 3 api.telegram.org
   ```

2. **Check DNS:**
   ```bash
   docker compose exec instalebot nslookup api.telegram.org
   ```

## Production Deployment

For production, consider:

1. **Use Docker secrets** instead of .env file:
   ```yaml
   secrets:
     telegram_token:
       file: ./secrets/telegram_token.txt
     rapidapi_key:
       file: ./secrets/rapidapi_key.txt
   ```

2. **Set resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

3. **Use health checks:**
   The Dockerfile already includes a health check.

4. **Set up log rotation:**
   Docker Compose is configured with log rotation (10MB max, 3 files).

5. **Use a reverse proxy** if switching to webhooks:
   ```yaml
   ports:
     - "8000:8000"
   ```

## Backup

To backup your data:

```bash
# Backup downloads
tar -czf downloads-backup-$(date +%Y%m%d).tar.gz downloads/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

## Monitoring

### View resource usage:
```bash
docker stats instalebot
```

### View container events:
```bash
docker events --filter container=instalebot
```

### Check container health:
```bash
docker inspect --format='{{.State.Health.Status}}' instalebot
```

