import sqlite3
from pathlib import Path

class SQLiteClient:
    def __init__(self, path="newsqa.db"):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS articles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, url TEXT, published_at TEXT, content TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS qna(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT, answer TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        self.conn.commit()
