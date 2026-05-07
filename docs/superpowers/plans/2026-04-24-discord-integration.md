# Discord Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Discord support into the Anime Bot with separate database tables and independent notification systems.

**Architecture:** Use `discord.py` for the Discord bot, running alongside the Telegram bot in `main.py` using `asyncio`. Maintain separate database tables (`discord_users`, `discord_subscriptions`) to ensure isolation.

**Tech Stack:** Python, `discord.py`, `python-telegram-bot`, PostgreSQL (psycopg2), `asyncio`.

---

### Task 1: Setup Dependencies and Configuration

**Files:**
- Modify: `requirements.txt`
- Modify: `.env`

- [ ] **Step 1: Add discord.py to requirements.txt**
Add `discord.py` to the end of the file.

- [ ] **Step 2: Add DISCORD_BOT_TOKEN to .env**
Add a placeholder `DISCORD_BOT_TOKEN=your_discord_token_here` to `.env`.

- [ ] **Step 3: Commit**
```bash
git add requirements.txt .env
git commit -m "chore: add discord dependencies and config"
```

---

### Task 2: Database Schema and Functions

**Files:**
- Modify: `database.py`

- [ ] **Step 1: Update init_db to create Discord tables**
Add `discord_users` and `discord_subscriptions` table creation logic.

- [ ] **Step 2: Implement Discord user and subscription functions**
Implement `add_discord_user`, `subscribe_discord_anime`, `unsubscribe_discord_anime`, `get_discord_user_subscriptions`, and `get_all_discord_subscriptions_for_day`.

- [ ] **Step 3: Verify database initialization**
Run `python database.py` and check if tables are created (manually or via tool).

- [ ] **Step 4: Commit**
```bash
git add database.py
git commit -m "feat: add discord database tables and functions"
```

---

### Task 3: Discord Bot Core Implementation

**Files:**
- Create: `discord_bot.py`

- [ ] **Step 1: Initialize Discord client and basic commands**
Setup `discord.ext.commands.Bot` with `!` prefix and implement `!start`, `!today`, and `!search`.

- [ ] **Step 2: Implement Embeds and Views for Search**
Create a rich `discord.Embed` for search results and a `discord.ui.View` with "Subscribe" and "Trailer" buttons.

- [ ] **Step 3: Implement Subscription Logic**
Handle button clicks to subscribe/unsubscribe users in the Discord tables.

- [ ] **Step 4: Commit**
```bash
git add discord_bot.py
git commit -m "feat: implement core discord bot with search and sub"
```

---

### Task 4: Discord Bot Advanced Features

**Files:**
- Modify: `discord_bot.py`

- [ ] **Step 1: Implement !gacha, !quiz, !char, and !top**
Port the logic from `bot.py` to `discord_bot.py`, using Discord Embeds and Polls (for quiz).

- [ ] **Step 2: Implement Photo-to-Anime Search (Trace.moe)**
Listen for image attachments and call the Trace.moe API, similar to `handle_photo` in `bot.py`.

- [ ] **Step 3: Implement AI Chat**
Handle non-command text messages by calling `get_ai_response`.

- [ ] **Step 4: Commit**
```bash
git add discord_bot.py
git commit -m "feat: add gacha, quiz, and photo search to discord bot"
```

---

### Task 5: Integrated Entry Point and Reminders

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Update main.py to run both bots**
Use `asyncio.gather` or similar to start both the Telegram `application` and the Discord `bot`.

- [ ] **Step 2: Add Discord Reminder System**
Implement `discord_daily_reminder` and `discord_check_airing_now` tasks that query Discord tables and send to Discord channels.

- [ ] **Step 3: Verify both bots run concurrently**
Run `python main.py` and check logs for both platform initializations.

- [ ] **Step 4: Commit**
```bash
git add main.py
git commit -m "feat: run both bots and integrate discord reminders"
```
