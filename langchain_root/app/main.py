# app/main.py

from src.utils.config import AppConfig
from src.sql.db import SqlStore
from src.crawler.rss_crawler import fetch_rss_docs

# 새로 추가된 import
from src.llm.solar import SolarClient
from src.vector_store.indexer import Indexer

class MainApp:
    def __init__(self):
        self.cfg = AppConfig()
        print("[INIT] 환경 로드 완료")
        print(f" - APP_ENV       : {self.cfg.env}")
        print(f" - CHROMA_DIR    : {self.cfg.chroma_dir}")
        print(f" - SQLITE_PATH   : {self.cfg.sqlite_path}")
        print(f" - RSS SOURCES   : {len(self.cfg.rss_list)}개 등록")

    # 1) 수집: RSS → 본문 추출 → SQLite 저장
    def run_ingest(self):
        """
        1) RSS에서 글 목록을 읽고
        2) 각 글의 본문을 추출한 뒤
        3) SQLite에 '중복 없이' 저장합니다.
        """
        store = SqlStore(self.cfg.sqlite_path)              # DB 연결(없으면 생성)
        docs = fetch_rss_docs(self.cfg.rss_list, per_feed_limit=20)  # RSS 2개 x 최대 20개
        inserted = 0
        for d in docs:
            doc_id = store.upsert_document(d)               # 중복이면 기존 id 반환
            if doc_id:
                inserted += 1
        print(f"[INGEST] new docs inserted: {inserted} / fetched: {len(docs)}")

    # 2) 인덱싱: 청킹/임베딩 → Chroma 업서트
    def run_index(self):
        """
        SQLite에서 문서를 불러와:
          - 청킹(조각내기)
          - 임베딩(숫자 벡터로 변환, embedding-passage)
          - Chroma(VectorDB)에 업서트(저장/갱신)
        를 수행합니다.
        """
        store = SqlStore(self.cfg.sqlite_path)
        solar = SolarClient(api_key=self.cfg.solar_api_key)

        indexer = Indexer(
            store=store,
            chroma_dir=self.cfg.chroma_dir,
            solar_client=solar,
            # 필요하면 configs로 빼서 조정 가능
            max_chars=1200,
            overlap=120,
            min_chunk_chars=200,
            batch_size=16,
        )

        result = indexer.index_recent(limit_docs=100)  # 최근 N개만 색인
        print("[INDEX RESULT]", result)

    # 3) 검색+생성: Top-k 검색 → LLM 답변 생성(+출처)
    def run_qa(self, question: str):
        print(f"[QA    ] Q: {question}")
        print("        아직 구현 전입니다. 다음 단계에서 'retriever'와 'llm(생성)'을 붙일게요.")

def main():
    app = MainApp()
    # 워킹 스켈레톤: 전체 흐름 자리만 호출
    app.run_ingest()  # 최신 뉴스 기사 수집
    app.run_index()   # 수집한 기사를 청킹/임베딩해 벡터DB에 색인
    app.run_qa("최근 생성형 AI 규제 동향을 요약해줘.")  # 검색+생성

if __name__ == "__main__":
    main()