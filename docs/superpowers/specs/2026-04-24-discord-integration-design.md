# Design Spec: Discord Integration for Anime Bot

## Overview
This project extends the existing Telegram Anime Bot to support Discord. The Discord version will maintain feature parity with the Telegram version while keeping data storage and notification systems completely separate.

## Requirements
- Support for Discord using `discord.py`.
- Command prefix `!`.
- Feature parity: search, today's schedule, gacha, quiz, character search, top anime, and photo-to-anime search.
- Separate database tables for Discord users and subscriptions.
- Independent notification systems for Telegram and Discord.

## Architecture

### 1. Database Schema Extensions (`database.py`)
New tables will be added to support Discord:
- `discord_users`:
  - `user_id` (BIGINT, PK)
  - `username` (TEXT)
- `discord_subscriptions`:
  - `id` (SERIAL, PK)
  - `user_id` (BIGINT, FK to `discord_users`)
  - `anime_id` (INTEGER)
  - `anime_title` (TEXT)
  - `airing_day` (TEXT)
  - `airing_time` (TEXT)

New functions:
- `add_discord_user(user_id, username)`
- `subscribe_discord_anime(user_id, anime_id, title, airing_day, airing_time)`
- `unsubscribe_discord_anime(user_id, anime_id)`
- `get_discord_user_subscriptions(user_id)`
- `get_all_discord_subscriptions_for_day(day_name)`

### 2. Discord Bot Logic (`discord_bot.py`)
A new module to handle Discord-specific logic using `discord.py`.
- Commands: `!start`, `!search`, `!today`, `!mylist`, `!gacha`, `!quiz`, `!char`, `!top`.
- UI: Use `discord.Embed` for rich formatting and `discord.ui.View` for interactive buttons (e.g., Subscribe, Unsubscribe, Trailer).
- Photo handling: Listen for message attachments and use Trace.moe API for recognition.

### 3. Integrated Entry Point (`main.py`)
Update `main.py` to run both bots.
- Use `asyncio` to run the Telegram `application` and Discord `client` concurrently.
- Separate reminder loops:
  - `telegram_reminder_loop`: Quets `subscriptions` table -> Sends to Telegram.
  - `discord_reminder_loop`: Quets `discord_subscriptions` table -> Sends to Discord.

## Implementation Details

### Dependencies
Add `discord.py` to `requirements.txt`.

### Environment Variables
Add `DISCORD_BOT_TOKEN` to `.env`.

### UI/UX
- Use Discord Embeds with colors matching the anime theme.
- Implement pagination or multiple messages if search results are numerous.

## Error Handling
- Standard try-except blocks for API calls and message sending.
- Graceful failure if one bot's token is missing while the other is present.

## Testing Plan
- Manual testing of all `!` commands on Discord.
- Verify that subscriptions on Discord do not appear on Telegram and vice versa.
- Test scheduled notifications for both platforms.
