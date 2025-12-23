# Instagram Telegram Bot

A Telegram bot that downloads Instagram videos/images, retrieves following/followers lists, and gets user profile information using RapidAPI's Instagram API.

## Features

- Download Instagram videos and images from posts/reels
- Get following list for any user
- Get followers list for any user
- Get user profile information
- Interactive menu with inline keyboard
- Command-based interface

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
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

## Usage

Send `/start` to the bot to see the interactive menu, or use commands directly.

