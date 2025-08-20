from logger.logger import get_logger
from sql.db import SQLiteClient
from llm.client import hello

def main():
    log = get_logger("main")
    log.info("Init DB...")
    db = SQLiteClient()  # newsqa.db 생성 & 테이블 초기화

    log.info("Calling LLM hello (Upstage)...")
    msg = hello()
    log.info(f"LLM said: {msg}")

if __name__ == "__main__":
    main()
