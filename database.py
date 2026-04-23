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

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully with Supabase PostgreSQL.")
