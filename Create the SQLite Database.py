import sqlite3

def create_db():
    conn = sqlite3.connect('leitner_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 chat_id INTEGER UNIQUE,
                 reminder_enabled BOOLEAN DEFAULT 1)''')

    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 question TEXT,
                 answer TEXT,
                 box INTEGER DEFAULT 1,
                 review_date DATE,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

create_db()
