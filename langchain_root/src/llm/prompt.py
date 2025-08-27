
# src/llm/prompt.py
"""
목적
-----
- LLM에 보낼 '프롬프트 묶음'을 일관된 형식으로 생성한다.
- 구성: System(역할/규칙) + User(질문 + Evidence 블록 + 출력 포맷 지시).
- 옵션: 한국어/영어, 불릿 개수/문장 수, Sources 강제, CoT(조용한 사고), ReAct 힌트 등.

하위호환
---------
- 과거 코드가 `PromptOptions(style=..., include_sources=...)`로 호출해도 깨지지 않도록
  `style`과 `include_sources`를 그대로 받는다.
- 내부적으로는 `include_sources` → `require_sources`로 매핑한다.
- 과거에 사용하던 `max_blocks`도 유지한다.

사용 흐름
---------
- retriever.search(question) → evidences(List[dict]) 확보
- PromptBuilder.build_messages(question, evidences, extra_instructions) → (system, user) 반환
- SolarClient.generate(system, user, model=...) 로 답변 생성
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import textwrap
import datetime

# src/llm/prompt.py  — PromptOptions 클래스만 교체

# from dataclasses import dataclass
# from typing import List, Optional

# @dataclass
# class PromptOptions:
#     """
#     프롬프트 옵션(하위호환 포함)

#     Parameters
#     ----------
#     language : str
#         답변 언어. 기본 "ko".
#     bullets_min : int
#         최소 불릿 개수(길이 확장을 위해 기본 5).
#     sentences_per_bullet_min : int
#         각 불릿의 최소 문장 수(기본 2).
#     require_sources : bool
#         Sources 섹션(참고 URL) 강제 여부. (신규 표준 필드)
#     forbid_hallucination : bool
#         Evidence 밖의 내용을 추측/창작하지 말도록 지시.
#     max_context_chars : int
#         Evidence 전체 텍스트 길이 상한.
#     max_block_chars : int
#         Evidence 블록(한 청크)당 본문 길이 상한.
#     max_blocks : int
#         Evidence 블록 최대 개수(Top-k와 유사; 하위호환 유지).
#     title : str
#         시스템 프롬프트 상단 타이틀.

#     하위호환 필드
#     ------------
#     style : Optional[str]
#         과거 호출부에서 넘기던 출력 스타일 힌트(예: "bullets"). 내부에선 사용하지 않지만 받기만 함.
#     include_sources : Optional[bool]
#         과거 호출부 호환 목적. 전달되면 require_sources로 매핑.

#     추가 옵션
#     --------
#     cot_silent : bool
#         '조용한 단계적 사고' 유도(사고 과정은 출력 금지).
#     react_hint : bool
#         Evidence 부족 시 추가 검색 필요를 언급하도록 힌트.
#     """
#     # 표준 옵션
#     language: str = "ko"
#     bullets_min: int = 5
#     sentences_per_bullet_min: int = 2
#     require_sources: bool = True
#     forbid_hallucination: bool = True
#     max_context_chars: int = 4200
#     max_block_chars: int = 1000
#     max_blocks: int = 7
#     title: str = "뉴스 RAG 어시스턴트"

#     # 하위호환
#     style: Optional[str] = None
#     include_sources: Optional[bool] = None

#     # 추가 동작 힌트
#     cot_silent: bool = True
#     react_hint: bool = False

#     def __post_init__(self):
#         # include_sources가 명시되면 require_sources로 매핑 (하위호환)
#         if self.include_sources is not None:
#             self.require_sources = bool(self.include_sources)

#     def render_system_rules(self) -> str:
#         """
#         시스템 프롬프트(역할/규칙/형식)를 생성한다.
#         - 길이 확장을 위해 불릿/문장 최소치, 구체 인용, 중복 금지, 구조(주장→근거→시사점)를 강하게 지시.
#         """
#         rules: List[str] = []
#         rules.append(f"당신은 {self.title}입니다.")

#         if self.forbid_hallucination:
#             rules.append("아래 Evidence에 포함된 정보만 사용해 답변하세요. 추측/창작 금지.")
#             rules.append("Evidence가 불충분하면 '모르겠습니다'라고 명확히 말하세요.")

#         # 길이/구조 강화
#         rules.append(
#             f"답변은 {self.language}로 작성하고, 불릿은 최소 {self.bullets_min}개 이상, "
#             f"각 불릿은 최소 {self.sentences_per_bullet_min}문장 이상으로 상세히 쓰세요."
#         )
#         rules.append("가능하면 날짜·수치·고유명사를 Evidence에서 인용해 구체적으로 작성하세요.")
#         rules.append("같은 내용을 반복하지 말고, 불릿마다 새로운 정보를 추가하세요.")
#         rules.append("각 불릿은 '핵심 주장 → 근거 인용/요약 → 시사점(So What)' 순서로 구성하세요.")

#         if self.require_sources:
#             rules.append("답변 마지막에 'Sources' 섹션을 만들고, 참고한 URL을 번호와 함께 모두 나열하세요.")

#         if self.cot_silent:
#             rules.append("답변을 작성하기 전, 조용히 단계적으로 생각하되 그 생각 과정을 출력하지 마세요.")

#         if self.react_hint:
#             rules.append("Evidence가 부족하다고 판단되면, 추가 검색이 필요하다는 점을 답변 내에서 간단히 알려주세요.")

#         return "\n".join(rules)
    
  
#     def _render_evidence_block(self, evidences):
#         """
#         Evidence 블록을 조합한다. evidences가 list가 아니어도 안전하게 처리하고,
#         각 원소를 dict로 강제 변환한다.
#         """
#         # 리스트 보장
#         if evidences is None:
#             evidences = []
#         elif isinstance(evidences, dict):
#             evidences = list(evidences.values())
#         elif not isinstance(evidences, list):
#             evidences = list(evidences)

#         # max_blocks 만큼만 사용
#         try:
#             max_blocks = max(1, int(self.opt.max_blocks))
#         except Exception:
#             max_blocks = 5
#         items = evidences[:max_blocks]

#         def _coerce(ev) -> dict:
#             # dict → 그대로
#             if isinstance(ev, dict):
#                 # 필수 키 기본값 채움
#                 return {
#                     "title": ev.get("title") or "(제목 없음)",
#                     "url": ev.get("url") or "",
#                     "source": ev.get("source") or "",
#                     "date_published": ev.get("date_published") or "",
#                     "score": ev.get("score", None),
#                     "text": ev.get("text") or "",
#                 }
#             # str → text로 감싸기
#             if isinstance(ev, str):
#                 return {
#                     "title": "(제목 없음)",
#                     "url": "",
#                     "source": "",
#                     "date_published": "",
#                     "score": None,
#                     "text": ev,
#                 }
#             # tuple/list → (meta, text) 또는 (text, meta) 추정
#             if isinstance(ev, (tuple, list)):
#                 if len(ev) == 2:
#                     a, b = ev
#                     if isinstance(a, dict) and not isinstance(b, dict):
#                         meta, text = a, str(b)
#                     elif isinstance(b, dict) and not isinstance(a, dict):
#                         meta, text = b, str(a)
#                     else:
#                         meta, text = {}, " ".join(str(x) for x in ev)
#                     return {
#                         "title": meta.get("title") if isinstance(meta, dict) else "(제목 없음)",
#                         "url": (meta.get("url") if isinstance(meta, dict) else "") or "",
#                         "source": (meta.get("source") if isinstance(meta, dict) else "") or "",
#                         "date_published": (meta.get("date_published") if isinstance(meta, dict) else "") or "",
#                         "score": (meta.get("score") if isinstance(meta, dict) else None),
#                         "text": text,
#                     }
#             # 그 밖의 타입 → 문자열로 덤프
#             return {
#                 "title": "(제목 없음)",
#                 "url": "",
#                 "source": "",
#                 "date_published": "",
#                 "score": None,
#                 "text": str(ev),
#             }

#         blocks = []
#         total_len = 0
#         for i, raw in enumerate(items, 1):
#             ev = _coerce(raw)  # ❗️여기서 무조건 dict로 보정

#             title = ev["title"].strip() or "(제목 없음)"
#             url = ev["url"].strip()
#             source = ev["source"].strip()
#             date_published = ev["date_published"].strip()
#             score = ev["score"]
#             text = ev["text"].strip()

#             # 블록당 길이 상한
#             if text and len(text) > self.opt.max_block_chars:
#                 text = text[: self.opt.max_block_chars - 3] + "..."

#             head = f"[{i}] {title}"
#             if url:
#                 head += f" ({url})"

#             meta_tail = []
#             if source:
#                 meta_tail.append(source)
#             if date_published:
#                 meta_tail.append(date_published)
#             if meta_tail:
#                 head += "  |  " + " · ".join(meta_tail)
#             if score is not None:
#                 try:
#                     head += f"  |  score={round(float(score), 4)}"
#                 except Exception:
#                     pass

#             block = head + (f"\n{text}" if text else "") + "\n---"

#             if total_len + len(block) > self.opt.max_context_chars:
#                 break
#             blocks.append(block)
#             total_len += len(block)

#         return "\n".join(blocks) if blocks else "(Evidence 없음)"

# src/llm/prompt.py  — PromptOptions 클래스 전체 교체

# from dataclasses import dataclass
# from typing import List, Optional

@dataclass
class PromptOptions:
    """
    프롬프트 옵션(하위호환 포함)

    Parameters
    ----------
    language : str            # 답변 언어
    bullets_min : int         # 최소 불릿 개수
    sentences_per_bullet_min : int   # 불릿당 최소 문장 수
    require_sources : bool    # 모델이 답변 말미에 Sources 섹션을 쓰도록 요구할지
    forbid_hallucination : bool
    max_context_chars : int   # Evidence 전체 길이 상한
    max_block_chars : int     # Evidence 블록당 길이 상한
    max_blocks : int          # Evidence 블록 최대 개수(Top-k와 연동)

    하위호환
    ----------
    style : Optional[str]
    include_sources : Optional[bool]  # 전달되면 require_sources로 매핑

    추가 옵션
    ----------
    cot_silent : bool
    react_hint : bool
    """
    # 표준 옵션
    language: str = "ko"
    bullets_min: int = 5
    sentences_per_bullet_min: int = 2
    require_sources: bool = True
    forbid_hallucination: bool = True
    max_context_chars: int = 4200
    max_block_chars: int = 1000
    max_blocks: int = 7
    title: str = "뉴스 RAG 어시스턴트"

    # 하위호환
    style: Optional[str] = None
    include_sources: Optional[bool] = None

    # 추가 동작 힌트
    cot_silent: bool = True
    react_hint: bool = False

    def __post_init__(self):
        # include_sources가 명시되면 require_sources로 매핑 (하위호환)
        if self.include_sources is not None:
            self.require_sources = bool(self.include_sources)

    def render_system_rules(self) -> str:
        """시스템 프롬프트(역할/규칙/형식) 문자열 생성"""
        rules: List[str] = []
        rules.append(f"당신은 {self.title}입니다.")

        if self.forbid_hallucination:
            rules.append("아래 Evidence에 포함된 정보만 사용해 답변하세요. 추측/창작 금지.")
            rules.append("Evidence가 불충분하면 '모르겠습니다'라고 명확히 말하세요.")

        rules.append(
            f"답변은 {self.language}로 작성하고, 불릿은 최소 {self.bullets_min}개 이상, "
            f"각 불릿은 최소 {self.sentences_per_bullet_min}문장 이상으로 상세히 쓰세요."
        )
        rules.append("가능하면 날짜·수치·고유명사를 Evidence에서 인용해 구체적으로 작성하세요.")
        rules.append("같은 내용을 반복하지 말고, 불릿마다 새로운 정보를 추가하세요.")
        rules.append("각 불릿은 '핵심 주장 → 근거 인용/요약 → 시사점(So What)' 순서로 구성하세요.")

        if self.require_sources:
            rules.append("답변 마지막에 'Sources' 섹션을 만들고, 참고한 URL을 번호와 함께 모두 나열하세요.")

        if self.cot_silent:
            rules.append("답변을 작성하기 전, 조용히 단계적으로 생각하되 그 생각 과정을 출력하지 마세요.")

        if self.react_hint:
            rules.append("Evidence가 부족하다고 판단되면, 추가 검색이 필요하다는 점을 답변 내에서 간단히 알려주세요.")

        return "\n".join(rules)
    
class PromptBuilder:
    """
    프롬프트 빌더

    역할
    ----
    - System Prompt(역할/규칙/형식) 문자열 생성
    - Evidence(리트리버 결과)를 보기 좋은 블록으로 정리
    - 질문(User 메시지)과 합쳐 최종 메시지 2개(system, user)를 반환

    반환 형식
    --------
    - Tuple[str, str]: (system_prompt, user_prompt)

    사용 예시
    ---------
    builder = PromptBuilder()
    system, user = builder.build_messages(question, evidences, extra_instructions)
    """

    def __init__(self, options: Optional[PromptOptions] = None):
        self.opt = options or PromptOptions()

    def _truncate(self, txt: str, limit: int) -> str:
        """길이 상한을 넘으면 말줄임표로 자른다."""
        if len(txt) <= limit:
            return txt
        return txt[: limit - 3] + "..."

    def _render_evidence_block(self, evidences: List[Dict[str, Any]]) -> str:
        """
        Evidence 블록을 조합한다.

        Parameters
        ----------
        evidences : List[Dict[str, Any]]
            각 원소 예:
            {
              "title": str, "url": str, "source": str, "date_published": "YYYY-MM-DD",
              "score": float, "text": str
            }

        Returns
        -------
        str
            Evidence 섹션 텍스트 (블록 구분선 포함)
        """
        # 하위호환: max_blocks 개수까지만 사용 (top_k와 비슷한 역할)
        items = evidences[: max(1, int(self.opt.max_blocks))]

        blocks: List[str] = []
        total_len = 0
        for i, ev in enumerate(items, 1):
            title = ev.get("title", "(제목 없음)").strip()
            url = ev.get("url", "").strip()
            source = ev.get("source", "").strip()
            date_published = ev.get("date_published", "").strip()
            score = ev.get("score", None)
            text = (ev.get("text", "") or "").strip()

            # 블록별 본문 상한
            t = self._truncate(text, self.opt.max_block_chars) if text else ""
            head = f"[{i}] {title}"
            if url:
                head += f" ({url})"
            meta_tail = []
            if source:
                meta_tail.append(source)
            if date_published:
                meta_tail.append(date_published)
            if meta_tail:
                head += "  |  " + " · ".join(meta_tail)
            if score is not None:
                head += f"  |  score={round(float(score), 4)}"

            block = head
            if t:
                block += f"\n{t}"
            block += "\n---"

            # 전체 컨텍스트 상한
            if total_len + len(block) > self.opt.max_context_chars:
                break
            blocks.append(block)
            total_len += len(block)

        return "\n".join(blocks) if blocks else "(Evidence 없음)"

    def build_messages(
        self,
        question: str,
        evidences: List[Dict[str, Any]],
        extra_instructions: Optional[str] = None,
    ) -> tuple[str, str]:
        if evidences is None:
            evidences = []
        elif isinstance(evidences, dict):
            evidences = list(evidences.values())
        elif not isinstance(evidences, list):
            evidences = list(evidences)
        """
        최종 system/user 메시지를 생성한다.

        Parameters
        ----------
        question : str
            사용자 질문.
        evidences : List[Dict[str, Any]]
            리트리버가 찾아온 Evidence 목록(메타 + 선택적으로 본문 일부).
        extra_instructions : Optional[str]
            실행 시 동적으로 추가할 출력 지시(예: "불릿 5개 이상, 각 불릿 2문장 이상").

        Returns
        -------
        (system_prompt, user_prompt) : tuple[str, str]
        """
        today = datetime.date.today().isoformat()
        system_prompt = self.opt.render_system_rules()

        ev_block = self._render_evidence_block(evidences)

        # 요청 포맷 지시(길이/밀도 강화)
        fmt_lines = [
            f"- {self.opt.language}로 답변",
            f"- 최소 불릿 {self.opt.bullets_min}개",
            f"- 각 불릿 최소 {self.opt.sentences_per_bullet_min}문장",
        ]
        if self.opt.require_sources:
            fmt_lines.append("- 마지막에 Sources 섹션 (URL 나열, 번호와 함께)")
        if extra_instructions:
            fmt_lines.append(f"- 추가 지시: {extra_instructions.strip()}")

        user_prompt = textwrap.dedent(f"""\
            질문: {question}
            오늘 날짜: {today}

            Evidence:
            {ev_block}

            요청 포맷:
            {chr(10).join(fmt_lines)}
        """).strip()

        return system_prompt, user_prompt
    # src/llm/prompt.py — PromptBuilder 클래스 내부에 다음 메서드 추가

    def _coerce_evidence_item(self, ev) -> dict:
        """
        evidence 원소를 dict로 강제 변환한다.
        - dict이면 그대로 반환
        - str이면 text로 감싸서 반환
        - tuple/list면 (text, meta) 또는 (meta, text) 추정해서 매핑
        - 그밖에는 문자열 덤프
        """
        if isinstance(ev, dict):
            return ev

        if isinstance(ev, str):
            return {"title": "(제목 없음)", "url": "", "source": "", "date_published": "", "score": None, "text": ev}

        if isinstance(ev, (tuple, list)):
            # (meta, text) or (text, meta) 추정
            if len(ev) == 2:
                a, b = ev[0], ev[1]
                # meta 후보가 dict이면 그쪽을 메타로
                if isinstance(a, dict) and not isinstance(b, dict):
                    meta = a
                    text = str(b)
                elif isinstance(b, dict) and not isinstance(a, dict):
                    meta = b
                    text = str(a)
                else:
                    meta = {}
                    text = " ".join(str(x) for x in ev)
                # 메타 dict에 기본 키 채워넣기
                meta = {**{"title": "(제목 없음)", "url": "", "source": "", "date_published": "", "score": None}, **meta}
                meta["text"] = text
                return meta

        # 어떤 타입이든 마지막 안전장치
        return {"title": "(제목 없음)", "url": "", "source": "", "date_published": "", "score": None, "text": str(ev)}