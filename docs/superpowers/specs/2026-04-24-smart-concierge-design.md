# Design Spec: Smart Multi-Personality Concierge

## Overview
This project adds advanced features to the Anime Bot, transforming it into a smart personal assistant with multiple personalities and the ability to track user interests (sports, music, crypto, etc.).

## Requirements
- **Multi-Personality System**: 
  - Change bot's response style via `!persona <name>`.
  - Personas: Tsundere, Secretary, Wibu, Cold, Senpai.
- **Concierge System**:
  - `!follow <topic>`: Track general topics (e.g., Bitcoin, Arsenal).
  - `!artist <name>`: Track specific singers/artists.
  - `!unfollow <topic/artist>`: Remove from tracking.
  - Automated daily briefings based on tracked interests.
- **Feature Integration**:
  - Personas affect all AI responses (chat, gacha descriptions, quiz explanations, daily briefings).

## Architecture

### 1. Database Schema (`database.py`)
New tables:
- `user_config`:
  - `chat_id` (BIGINT, PK) - handles both platforms by prefixing or using platform column (since we have separate tables, we'll add these to both `users` and `discord_users` or create separate config tables).
  - `persona` (TEXT, default 'Secretary')
- `user_interests`:
  - `id` (SERIAL, PK)
  - `chat_id` (BIGINT)
  - `platform` (TEXT - 'telegram' or 'discord')
  - `topic_type` (TEXT - 'general' or 'artist')
  - `topic_name` (TEXT)

New functions:
- `set_user_persona(chat_id, platform, persona)`
- `get_user_persona(chat_id, platform)`
- `add_user_interest(chat_id, platform, type, name)`
- `remove_user_interest(chat_id, platform, name)`
- `get_user_interests(chat_id, platform)`

### 2. AI Logic (`ai.py`)
Update `get_ai_response` to accept a `persona` parameter.
- Define system prompts for each persona:
  - **Tsundere**: Grumpy, uses "Hmpf!", "It's not like I like you!", but actually helpful.
  - **Secretary**: Professional, polite, organized.
  - **Wibu**: Uses Japanese loanwords (kawaii, desu), obsessed with anime.
  - **Cold**: Short, blunt, efficient.
  - **Senpai**: Caring, guiding, protective.

### 3. Concierge Background Task (`main.py`)
- Implement a task that runs daily.
- For each user with interests:
  - Use AI (with `search_web` if available in the future or via current model's knowledge) to find updates.
  - Format the briefing using the user's selected persona.

### 4. Commands Integration
- Telegram (`bot.py`): Add `/persona`, `/follow`, `/artist`.
- Discord (`discord_bot.py`): Add `!persona`, `!follow`, `!artist`.

## Implementation Details

### Personas Definition
```python
PERSONAS = {
    'tsundere': "Bạn là một cô gái Tsundere. Bạn hay gắt gỏng, dùng những câu như 'Hứ!', 'Không phải tôi muốn giúp bạn đâu!', nhưng thực chất vẫn làm tốt công việc. Trả lời bằng tiếng Việt.",
    'secretary': "Bạn là một thư ký chuyên nghiệp, lịch sự, luôn hỗ trợ người dùng một cách tận tâm và ngăn nắp. Trả lời bằng tiếng Việt.",
    # ... other personas
}
```

### Concierge Flow
1. Fetch all unique interests from DB.
2. Generate summary for each interest using AI.
3. Distribute summaries to corresponding users in their chosen persona style.
