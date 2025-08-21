import sqlite3
from pathlib import Path

class SQLiteClient:
    def __init__(self, path="newsqa.db"):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        # articles: URL 유니크 인덱스 추가 (중복 저장 방지)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS articles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, url TEXT UNIQUE, published_at TEXT, content TEXT
        )
        """)
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url ON articles(url)")
        # chunks: 기사 단락 저장
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER, chunk_idx INTEGER, text TEXT,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        )
        """)
        self.conn.commit()

    # ---------- 간단 DAO ----------
    def insert_article(self, title:str, url:str, published_at:str, content:str) -> int | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT OR IGNORE INTO articles(title, url, published_at, content) VALUES (?,?,?,?)",
                (title, url, published_at, content)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print("insert_article error:", e)
        # 방금 넣었거나 기존의 id 가져오기
        cur.execute("SELECT id FROM articles WHERE url=?", (url,))
        row = cur.fetchone()
        return row[0] if row else None

    def insert_chunk(self, article_id:int, chunk_idx:int, text:str):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO chunks(article_id, chunk_idx, text) VALUES (?,?,?)",
            (article_id, chunk_idx, text)
        )
        self.conn.commit()

    def count_articles(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    def count_chunks(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

