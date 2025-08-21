# preprocessor/text_cleaner.py
from __future__ import annotations
import re
from typing import List

_ws_re = re.compile(r"[ \t]+")
_multi_nl_re = re.compile(r"\n{3,}")

def clean_text(text: str) -> str:
    # 공백/개행 정규화
    t = text.replace("\r", "")
    t = _multi_nl_re.sub("\n\n", t)     # 3줄 이상 연속 개행 → 2줄
    t = _ws_re.sub(" ", t)              # 탭/다중공백 → 한 칸
    return t.strip()

def chunk_by_paragraphs(text: str, min_chars: int = 200, max_chars: int = 1000) -> List[str]:
    """빈 줄 기준으로 단락을 나눠 너무 짧으면 인접 단락과 병합."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf = ""

    def flush():
        nonlocal buf
        if buf:
            chunks.append(buf.strip())
            buf = ""

    for p in paras:
        if not buf:
            buf = p
        elif len(buf) + 1 + len(p) <= max_chars:
            buf = f"{buf}\n\n{p}"
        else:
            # 현재 버퍼가 충분히 길면 내보내고 새로 시작
            if len(buf) >= min_chars:
                flush()
                buf = p
            else:
                # 짧으면 무조건 병합
                buf = f"{buf}\n\n{p}"
                if len(buf) >= min_chars:
                    flush()
                    buf = ""

    if buf:
        flush()
    return chunks
