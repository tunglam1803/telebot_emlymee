import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'anime_bot.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        username TEXT,
        summary_enabled INTEGER DEFAULT 1
    )
    ''')
    
    # Table for subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        anime_id INTEGER,
        anime_title TEXT,
        airing_day TEXT,
        airing_time TEXT,
        FOREIGN KEY(chat_id) REFERENCES users(chat_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_user(chat_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (chat_id, username) VALUES (?, ?)', (chat_id, username))
    conn.commit()
    conn.close()

def subscribe_anime(chat_id, anime_id, title, airing_day, airing_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO subscriptions (chat_id, anime_id, anime_title, airing_day, airing_time)
    VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, anime_id, title, airing_day, airing_time))
    conn.commit()
    conn.close()

def unsubscribe_anime(chat_id, anime_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subscriptions WHERE chat_id = ? AND anime_id = ?', (chat_id, anime_id))
    conn.commit()
    conn.close()

def get_user_subscriptions(chat_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép lấy dữ liệu theo tên cột
    cursor = conn.cursor()
    cursor.execute('SELECT anime_id, anime_title, airing_day, airing_time FROM subscriptions WHERE chat_id = ?', (chat_id,))
    subs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return subs

def get_all_subscriptions_for_day(day_name):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, anime_id, anime_title, airing_time FROM subscriptions WHERE airing_day = ?', (day_name,))
    subs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return subs

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
