#Day1
# from logger.logger import get_logger
# from sql.db import SQLiteClient
# from llm.client import hello

# def main():
#     log = get_logger("main")
#     log.info("Init DB...")
#     db = SQLiteClient()  # newsqa.db 생성 & 테이블 초기화

#     log.info("Calling LLM hello (Upstage)...")
#     msg = hello()
#     log.info(f"LLM said: {msg}")

# if __name__ == "__main__":
#     main()

# main.py
import sys
from logger.logger import get_logger
from sql.db import SQLiteClient
from llm.client import hello   # Day1 스모크 유지
from crawler.news_crawler import crawl_ai_news
from preprocessor.text_cleaner import clean_text, chunk_by_paragraphs

def run_hello():
    log = get_logger("main")
    log.info("Init DB...")
    db = SQLiteClient()
    log.info("Calling LLM hello (Upstage)...")
    msg = hello()
    log.info(f"LLM said: {msg}")

def run_ingest():
    log = get_logger("ingest")
    db = SQLiteClient()

    log.info("Crawling AI news (3~5 items)...")
    items = crawl_ai_news(limit=5)
    log.info(f"Fetched {len(items)} items")

    total_chunks = 0
    for it in items:
        # 1) article 저장
        aid = db.insert_article(
            title=it["title"],
            url=it["url"],
            published_at=it.get("published_at", ""),
            content=it["content"]
        )
        if not aid:
            log.info(f"skip (dup?): {it['title']}")
            continue

        # 2) clean + chunk
        cleaned = clean_text(it["content"])
        chunks = chunk_by_paragraphs(cleaned, min_chars=200, max_chars=1000)
        for idx, ch in enumerate(chunks):
            db.insert_chunk(aid, idx, ch)
        total_chunks += len(chunks)

        log.info(f"saved article id={aid}, chunks={len(chunks)} :: {it['title']}")

    log.info(f"Done. articles={db.count_articles()}, chunks={db.count_chunks()}")

if __name__ == "__main__":
    # 사용법:
    #   python main.py          -> Day1 hello
    #   python main.py ingest   -> Day2 파이프라인 실행
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        run_ingest()
    else:
        run_hello()

