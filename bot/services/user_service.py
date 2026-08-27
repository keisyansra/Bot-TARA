import sqlite3
import os

#database untuk user yg udah di acc admin
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "tara_users.db")

def init_user_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_user_role(user_id: int):
    init_user_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def register_user(user_id: int, username: str, full_name: str, role: str = 'pending'):
    init_user_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, role) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, role)
        )

def update_user_role(user_id: int, role: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        conn.commit()

def get_pending_users():
    """Mengambil semua user yang statusnya masih 'pending'"""
    init_user_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT user_id, username, full_name FROM users WHERE role = 'pending'")
        return cursor.fetchall()

def delete_user(user_id: int) -> bool:
    """Menghapus user dari database berdasarkan user_id"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()

        return cursor.rowcount > 0