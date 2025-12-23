# Instagram Telegram Bot

A Telegram bot that downloads Instagram videos/images, retrieves following/followers lists, and gets user profile information using RapidAPI's Instagram API.

## Features

- Download Instagram videos and images from posts/reels
- Get following list for any user
- Get followers list for any user
- Get user profile information
- Get similar account recommendations
- Get user video feed, post feed, and reels
- Interactive menu with inline keyboard
- Command-based interface

## Quick Start

### Docker Deployment (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thanghnm49/InstaLeBot.git
   cd InstaLeBot
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Add your credentials:
   - `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather)
   - `RAPIDAPI_KEY`: Get from [RapidAPI](https://rapidapi.com)

3. **Build and start with Docker:**
   ```bash
   chmod +x docker-run.sh
   ./docker-run.sh build
   ./docker-run.sh start
   ```

4. **View logs:**
   ```bash
   ./docker-run.sh logs
   ```

**Docker Commands:**
- `./docker-run.sh build` - Build Docker image
- `./docker-run.sh start` - Start container
- `./docker-run.sh stop` - Stop container
- `./docker-run.sh restart` - Restart container
- `./docker-run.sh logs` - View logs
- `./docker-run.sh status` - Check status
- `./docker-run.sh shell` - Open shell in container
- `./docker-run.sh clean` - Remove container and image

**Or use Docker Compose directly:**
```bash
docker-compose up -d          # Start in background
docker-compose logs -f       # View logs
docker-compose down           # Stop
docker-compose restart        # Restart
```

### Local Development (Without Docker)

1. Clone the repository
   ```bash
   git clone https://github.com/thanghnm49/InstaLeBot.git
   cd InstaLeBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add:
   - `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather)
   - `RAPIDAPI_KEY`: Get from [RapidAPI](https://rapidapi.com)

4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

- `/start` or `/menu` - Show interactive menu
- `/download <instagram_url>` - Download video/image from Instagram post/reel
- `/following <user_id>` - Get following list for a user
- `/followers <user_id>` - Get followers list for a user
- `/userinfo <user_id>` - Get user profile information
- `/similar <user_id>` - Find similar account recommendations
- `/videofeed <user_id>` - Get user video feed
- `/postfeed <user_id>` - Get user post feed
- `/reels <user_id>` - Get user reels

## Service Management

### Docker

```bash
./docker-run.sh start      # Start
./docker-run.sh stop       # Stop
./docker-run.sh restart    # Restart
./docker-run.sh logs       # View logs
./docker-run.sh status     # Check status
```

### Docker Compose

```bash
docker-compose up -d        # Start in background
docker-compose down         # Stop
docker-compose restart      # Restart
docker-compose logs -f      # View logs
docker-compose ps           # Check status
```

## Logs

- **Docker logs**: `./docker-run.sh logs` or `docker-compose logs -f`
- **Application logs**: `logs/bot.log` and `logs/bot-error.log`

## Documentation

- [Docker Deployment Guide](DOCKER.md) - Complete Docker setup and troubleshooting

## Usage

Send `/start` to the bot to see the interactive menu, or use commands directly.
