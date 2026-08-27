import sqlite3
import os

# Menyimpan file SQLite di direktori lokal bot
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "visited_prospects.db")

def init_visited_db():
    """Inisialisasi tabel visited_prospects jika belum ada"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visited_prospects (
                user_id INTEGER,
                prospect_id TEXT,
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, prospect_id)
            )
        """)

def mark_as_visited(user_id: int, prospect_id: str):
    """Menandai prospek tertentu telah dikunjungi oleh sales bersangkutan"""
    init_visited_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO visited_prospects (user_id, prospect_id) VALUES (?, ?)",
            (user_id, str(prospect_id))
        )

def get_visited_prospect_ids(user_id: int) -> set:
    """Mengambil set ID prospek yang pernah ditandai oleh user_id tersebut"""
    init_visited_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT prospect_id FROM visited_prospects WHERE user_id = ?", (user_id,))
        return {str(row[0]) for row in cursor.fetchall()}

def reset_user_visited(user_id: int):
    """Mereset data kunjungan khusus untuk user ini"""
    init_visited_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM visited_prospects WHERE user_id = ?", (user_id,))
        conn.commit()