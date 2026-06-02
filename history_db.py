import sqlite3
import os

DB_PATH = "chatbot_history.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            );
        """)
        conn.commit()

def create_conversation(title: str) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,)
        )
        conn.commit()
        return cursor.lastrowid

def save_message(conversation_id: int, role: str, content: str):
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        conn.commit()

def get_conversations():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

def get_messages(conversation_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def delete_conversation(conversation_id: int):
    with get_db_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
