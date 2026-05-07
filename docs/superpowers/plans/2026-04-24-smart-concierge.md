# Smart Multi-Personality Concierge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a multi-personality system and a smart concierge for tracking interests (sports, artists, etc.) across Telegram and Discord.

**Architecture:** Extend database with config and interest tables. Update AI logic to use persona-based system prompts. Add background tasks for daily briefings.

**Tech Stack:** Python, `discord.py`, `python-telegram-bot`, PostgreSQL, Google Gemini API.

---

### Task 1: Database Schema for Persona and Interests

**Files:**
- Modify: `database.py`

- [ ] **Step 1: Add user_config and user_interests tables**
Update `init_db` to include `user_config` and `user_interests`.

- [ ] **Step 2: Implement getter/setter functions**
Add `set_user_persona`, `get_user_persona`, `add_user_interest`, `remove_user_interest`, and `get_user_interests`.

- [ ] **Step 3: Commit**
```bash
git add database.py
git commit -m "feat: add database support for personas and interests"
```

---

### Task 4: AI Logic and Persona Integration

**Files:**
- Modify: `ai.py`

- [ ] **Step 1: Define PERSONAS dictionary**
Add a dictionary containing system prompts for: Tsundere, Secretary, Wibu, Cold, Senpai.

- [ ] **Step 2: Update get_ai_response**
Modify the function to accept a `persona` key and include it in the AI prompt.

- [ ] **Step 3: Commit**
```bash
git add ai.py
git commit -m "feat: implement multi-personality AI logic"
```

---

### Task 3: Discord Command Implementation

**Files:**
- Modify: `discord_bot.py`

- [ ] **Step 1: Add !persona command**
Implement command to switch persona and save to DB.

- [ ] **Step 2: Add !follow and !artist commands**
Implement commands to track topics and singers.

- [ ] **Step 3: Integrate persona into all responses**
Ensure chat and other commands use the user's selected persona.

- [ ] **Step 4: Commit**
```bash
git add discord_bot.py
git commit -m "feat: add persona and interest commands to discord bot"
```

---

### Task 4: Telegram Command Implementation

**Files:**
- Modify: `bot.py`
- Modify: `main.py`

- [ ] **Step 1: Add /persona, /follow, /artist to bot.py**
Implement the handlers.

- [ ] **Step 2: Register handlers in main.py**
Add the new commands to the Telegram application.

- [ ] **Step 3: Commit**
```bash
git add bot.py main.py
git commit -m "feat: add persona and interest commands to telegram bot"
```

---

### Task 5: Smart Concierge Background Task

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Implement daily_concierge_briefing task**
Create a background loop that finds news for user interests using AI and sends persona-styled reports.

- [ ] **Step 2: Register the task in main loop**
Ensure the task starts with the bots.

- [ ] **Step 3: Commit**
```bash
git add main.py
git commit -m "feat: implement automated smart concierge briefings"
```
