"""SQLite episodic memory, isolated per thread_id."""
import sqlite3
import time

DB_PATH = "memory.db"


def _conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL, ts REAL NOT NULL)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_thread ON messages(thread_id)")
    return c


def add(thread_id: str, role: str, content: str):
    with _conn() as c:
        c.execute("INSERT INTO messages(thread_id, role, content, ts) VALUES (?,?,?,?)",
                  (thread_id, role, content, time.time()))


def history(thread_id: str, limit: int = 10):
    with _conn() as c:
        rows = c.execute("SELECT role, content FROM messages WHERE thread_id=? "
                         "ORDER BY id DESC LIMIT ?", (thread_id, limit)).fetchall()
    return list(reversed(rows))


def count(thread_id=None) -> int:
    with _conn() as c:
        if thread_id:
            return c.execute("SELECT COUNT(*) FROM messages WHERE thread_id=?", (thread_id,)).fetchone()[0]
        return c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
