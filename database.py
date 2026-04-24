import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("CẢNH BÁO: Chưa có DATABASE_URL trong file .env!")
        return None
    return psycopg2.connect(db_url)

def init_db():
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    
    # Table for users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id BIGINT PRIMARY KEY,
        username TEXT,
        summary_enabled INTEGER DEFAULT 1
    )
    ''')
    
    # Table for subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        anime_id INTEGER,
        anime_title TEXT,
        airing_day TEXT,
        airing_time TEXT,
        FOREIGN KEY(chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
    )
    ''')

    # Table for discord users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discord_users (
        user_id BIGINT PRIMARY KEY,
        username TEXT
    )
    ''')

    # Table for discord subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discord_subscriptions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        anime_id INTEGER,
        anime_title TEXT,
        airing_day TEXT,
        airing_time TEXT,
        FOREIGN KEY(user_id) REFERENCES discord_users(user_id) ON DELETE CASCADE
    )
    ''')

    # Table for user configurations (Persona)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_config (
        chat_id BIGINT PRIMARY KEY,
        platform TEXT,
        persona TEXT DEFAULT 'tsundere'
    )
    ''')

    # Table for user interests
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_interests (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        platform TEXT,
        topic_type TEXT, -- 'general' or 'artist'
        topic_name TEXT
    )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def add_user(chat_id, username):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (chat_id, username) 
        VALUES (%s, %s) 
        ON CONFLICT (chat_id) DO NOTHING
    ''', (chat_id, username))
    conn.commit()
    cursor.close()
    conn.close()

def subscribe_anime(chat_id, anime_id, title, airing_day, airing_time):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    # Kiểm tra đã đăng ký chưa để tránh trùng lặp
    cursor.execute('SELECT id FROM subscriptions WHERE chat_id = %s AND anime_id = %s', (chat_id, anime_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False  # Đã đăng ký rồi
        
    cursor.execute('''
    INSERT INTO subscriptions (chat_id, anime_id, anime_title, airing_day, airing_time)
    VALUES (%s, %s, %s, %s, %s)
    ''', (chat_id, anime_id, title, airing_day, airing_time))
    conn.commit()
    cursor.close()
    conn.close()
    return True  # Đăng ký thành công

def unsubscribe_anime(chat_id, anime_id):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subscriptions WHERE chat_id = %s AND anime_id = %s', (chat_id, anime_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_subscriptions(chat_id):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT anime_id, anime_title, airing_day, airing_time FROM subscriptions WHERE chat_id = %s', (chat_id,))
    subs = cursor.fetchall()
    cursor.close()
    conn.close()
    return subs

def get_all_subscriptions_for_day(day_name):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT chat_id, anime_id, anime_title, airing_time FROM subscriptions WHERE airing_day = %s', (day_name,))
    subs = cursor.fetchall()
    cursor.close()
    conn.close()
    return subs

# --- DISCORD FUNCTIONS ---

def add_discord_user(user_id, username):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO discord_users (user_id, username) 
        VALUES (%s, %s) 
        ON CONFLICT (user_id) DO NOTHING
    ''', (user_id, username))
    conn.commit()
    cursor.close()
    conn.close()

def subscribe_discord_anime(user_id, anime_id, title, airing_day, airing_time):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM discord_subscriptions WHERE user_id = %s AND anime_id = %s', (user_id, anime_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False
        
    cursor.execute('''
    INSERT INTO discord_subscriptions (user_id, anime_id, anime_title, airing_day, airing_time)
    VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, anime_id, title, airing_day, airing_time))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def unsubscribe_discord_anime(user_id, anime_id):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('DELETE FROM discord_subscriptions WHERE user_id = %s AND anime_id = %s', (user_id, anime_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_discord_user_subscriptions(user_id):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT anime_id, anime_title, airing_day, airing_time FROM discord_subscriptions WHERE user_id = %s', (user_id,))
    subs = cursor.fetchall()
    cursor.close()
    conn.close()
    return subs

def get_all_discord_subscriptions_for_day(day_name):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT user_id, anime_id, anime_title, airing_time FROM discord_subscriptions WHERE airing_day = %s', (day_name,))
    subs = cursor.fetchall()
    cursor.close()
    conn.close()
    return subs

# --- PERSONA & INTERESTS FUNCTIONS ---

def set_user_persona(chat_id, platform, persona):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_config (chat_id, platform, persona) 
        VALUES (%s, %s, %s) 
        ON CONFLICT (chat_id) DO UPDATE SET persona = EXCLUDED.persona
    ''', (chat_id, platform, persona))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_persona(chat_id, platform):
    conn = get_connection()
    if not conn: return 'tsundere'
    cursor = conn.cursor()
    cursor.execute('SELECT persona FROM user_config WHERE chat_id = %s AND platform = %s', (chat_id, platform))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res[0] if res else 'tsundere'

def add_user_interest(chat_id, platform, topic_type, topic_name):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_interests (chat_id, platform, topic_type, topic_name) 
        VALUES (%s, %s, %s, %s)
    ''', (chat_id, platform, topic_type, topic_name))
    conn.commit()
    cursor.close()
    conn.close()

def remove_user_interest(chat_id, platform, topic_name):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_interests WHERE chat_id = %s AND platform = %s AND topic_name ILIKE %s', (chat_id, platform, topic_name))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_interests(chat_id, platform):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT topic_type, topic_name FROM user_interests WHERE chat_id = %s AND platform = %s', (chat_id, platform))
    interests = cursor.fetchall()
    cursor.close()
    conn.close()
    return interests

def get_all_users_with_interests():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT DISTINCT chat_id, platform FROM user_interests')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with Supabase PostgreSQL.")
