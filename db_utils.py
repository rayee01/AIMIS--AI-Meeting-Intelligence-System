import sqlite3
import os
import datetime

DB_NAME = "aimis_data.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create meetings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT,
            transcript TEXT,
            mom TEXT
        )
    ''')
    # Create chats table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (meeting_id) REFERENCES meetings (id)
        )
    ''')
    conn.commit()
    conn.close()

def save_meeting(title, transcript, mom, chat_messages):
    """Save a meeting session to the database."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute('INSERT INTO meetings (title, created_at, transcript, mom) VALUES (?, ?, ?, ?)',
              (title, now, transcript, mom))
    meeting_id = c.lastrowid
    
    # Save chat history
    for msg in chat_messages:
        role = msg.get("role", "user")
        content = msg.get("parts", [""])[0] if "parts" in msg else ""
        c.execute('INSERT INTO chats (meeting_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                  (meeting_id, role, content, now))
    
    conn.commit()
    conn.close()
    return meeting_id

def get_all_meetings():
    """Retrieve all saved meetings for the archive tab."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, title, created_at FROM meetings ORDER BY id DESC')
    meetings = c.fetchall()
    conn.close()
    
    results = []
    for m in meetings:
        try:
            # Parse ISO format for cleaner display
            dt = datetime.datetime.fromisoformat(m[2])
            formatted_date = dt.strftime("%b %d, %Y - %I:%M %p")
        except:
            formatted_date = m[2]
            
        results.append({
            "id": m[0],
            "title": m[1],
            "date": formatted_date
        })
    return results

def get_meeting(meeting_id):
    """Retrieve full details of a specific meeting."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT transcript, mom FROM meetings WHERE id = ?', (meeting_id,))
    meeting = c.fetchone()
    
    c.execute('SELECT role, content FROM chats WHERE meeting_id = ? ORDER BY id ASC', (meeting_id,))
    chats = c.fetchall()
    conn.close()
    
    if meeting:
        return {
            "transcript": meeting[0],
            "mom": meeting[1],
            "chats": [{"role": r[0], "content": r[1]} for r in chats]
        }
    return None
