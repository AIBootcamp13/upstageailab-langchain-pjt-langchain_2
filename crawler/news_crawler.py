# crawler/news_crawler.py
from __future__ import annotations
import time
from typing import List, Dict, Any
from urllib.parse import quote_plus

import feedparser
import trafilatura

def _google_news_rss(query: str) -> str:
    # 한국어 뉴스, 한국 지역
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=ko&gl=KR&ceid=KR:ko"

def crawl_ai_news(limit: int = 5) -> List[Dict[str, Any]]:
    """AI/인공지능 관련 최신 뉴스 3~5건 크롤링 → 기사 본문 추출(실패 시 summary 사용)."""
    # Naver 호스팅 기사를 우선 노려보되(없어도 상관 없음)
    query = '("생성형 AI" OR 인공지능 OR AI) site:news.naver.com'
    feed_url = _google_news_rss(query)
    feed = feedparser.parse(feed_url)

    results: List[Dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        published = getattr(entry, "published", "")
        summary = getattr(entry, "summary", "")

        # 본문 추출 시도 (실패하면 summary 사용)
        text = None
        try:
            # polite crawling: 너무 빠른 연속요청 방지
            time.sleep(0.8)
            text = trafilatura.fetch_url(link)
            text = trafilatura.extract(text) if text else None
        except Exception:
            text = None

        content = (text or summary or "").strip()
        if not content:
            continue

        results.append({
            "title": title,
            "url": link,
            "published_at": published,
            "content": content
        })
    return results
