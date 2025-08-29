# src/qa/answerer.py
"""
Answerer
--------
Retriever → PromptBuilder → SolarClient 를 오케스트레이션하여
질문에 대한 최종 답변을 생성하는 상위 레벨 유스케이스 레이어.

주요 동작
---------
1) _retrieve(): 사용자 질문 임베딩 → 벡터 검색(Top-k/MMR) → Evidence 목록 반환
2) _generate(): PromptBuilder로 System/User 프롬프트 구성 → Solar로 생성 호출
3) answer(), answer_multi(): 단일/다중 모델 실행

하위호환
--------
- PromptOptions는 style/include_sources를 받아도 동작(내부 매핑).
"""

from typing import List, Dict, Any, Optional
import time

from src.utils.config import AppConfig
from src.retriever.search import Retriever
from src.llm.solar import SolarClient
from src.llm.prompt import PromptBuilder, PromptOptions
import re

class Answerer:
    def __init__(
        self,
        cfg: AppConfig,
        top_k: int = 7,            # 길이/정보량 확보 위해 기본 7
        use_mmr: bool = True,
        mmr_lambda: float = 0.3,
        prompt_opt: Optional[PromptOptions] = None,
    ):
        """
        Parameters
        ----------
        cfg : AppConfig
            경로/키/설정이 담긴 앱 설정 객체.
        top_k : int
            리트리버가 가져올 초기 후보 개수.
        use_mmr : bool
            MMR 사용 여부.
        mmr_lambda : float
            MMR 가중치(관련성↔다양성 균형).
        prompt_opt : Optional[PromptOptions]
            프롬프트 옵션(없으면 기본값 사용).
        """
        self.cfg = cfg

        # 1) LLM 클라이언트 (임베딩/생성 공용)
        self.solar = SolarClient(api_key=cfg.solar_api_key)

        # 2) 리트리버 (❗ SolarClient를 반드시 넘겨야 함)
        self.retriever = Retriever(
            chroma_dir=cfg.chroma_dir,
            solar_client=self.solar,   # ← 필수 인자
            top_k=top_k,
            use_mmr=use_mmr,
            mmr_lambda=mmr_lambda,
        )

        # 3) 프롬프트 빌더
        #    (PromptOptions는 style/include_sources 하위호환 지원: prompt.py 참조)
        self.prompt_builder = PromptBuilder(options=prompt_opt or PromptOptions())

    # ---------------- internal helpers ---------------- #

# src/qa/answerer.py  — Answerer 클래스 안의 이 함수만 교체

    def _retrieve(self, question: str) -> Dict[str, Any]:
        """
        리트리버로 evidence(근거 청크) 리스트를 구한다. (리턴 타입 방어 포함)
        """
        t0 = time.time()
        sources = self.retriever.search(question)
        t1 = time.time()

        # ⬇️ 방어: 리스트 보장
        if sources is None:
            sources = []
        elif isinstance(sources, dict):
            sources = list(sources.values())
        elif not isinstance(sources, list):
            sources = list(sources)

        return {
            "sources": sources,
            "retrieval_ms": int((t1 - t0) * 1000),
            "used_top_k": len(sources),
        }
    
    @staticmethod
    def _strip_model_sources(text: str) -> str:
    # 하단의 "Sources:"나 "SOURCES" 이후를 전부 제거 (대소문자/개행 허용)
        return re.sub(r"(?is)\n+sources?:\s*\n[\s\S]*$", "", text).strip()


    def _generate(
        self,
        question: str,
        model: str,
        max_tokens: int,
        extra_instructions: Optional[str],
    ) -> Dict[str, Any]:
        """
        하나의 모델로 QA 실행:
        - 검색 (Retriever)
        - 프롬프트 생성 (PromptBuilder)
        - LLM 호출 (SolarClient)
        - 결과 dict 반환 (항상 동일한 구조)

        실패 시에도 dict로 error 메시지를 포함해 반환합니다.
        """

        try:
            # 1) 검색
            ret = self._retrieve(question)
            evidences = self._normalize_evidences(ret["sources"])

            # 2) 프롬프트 생성
            system_prompt, user_prompt = self.prompt_builder.build_messages(
                question=question,
                evidences=evidences,
                extra_instructions=extra_instructions,
            )

            # 3) LLM 호출
            t0 = time.time()
            answer = self.solar.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
            )
            answer = self._strip_model_sources(answer) 
            t1 = time.time()

            # 4) 정상 결과 반환
            return {
                "model": model,
                "answer": answer,
                "sources": evidences,
                "used_top_k": len(evidences),
                "retrieval_ms": ret.get("retrieval_ms", 0),
                "gen_ms": int((t1 - t0) * 1000),
                "error": None,
            }

        except Exception as e:
            # ✅ 실패도 항상 dict로 반환 → UI가 깨지지 않음
            return {
                "model": model,
                "answer": f"[ERROR] {e}",
                "sources": [],
                "used_top_k": 0,
                "retrieval_ms": 0,
                "gen_ms": 0,
                "error": str(e),
            }


    # ---------------- public API ---------------- #

    def answer(
        self,
        question: str,
        model: str = "solar-pro",
        max_tokens: int = 600,
        extra_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """단일 모델로 QA 실행"""
        return self._generate(question, model, max_tokens, extra_instructions)

    def answer_multi(self, question: str, models: List[str], max_tokens: int = 600, extra_instructions: Optional[str] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for m in models:
            out = self._generate(question, m, max_tokens, extra_instructions)
            # ✅ None 방지: 항상 dict 이어야 함
            if not isinstance(out, dict):
                out = {"model": m, "answer": "[ERROR] Unknown failure", "sources": [], "used_top_k": 0, "retrieval_ms": 0, "gen_ms": 0, "error": "unknown"}
            results.append(out)
        return results
    
    # src/qa/answerer.py — Answerer 클래스 내부에 추가

    def _normalize_evidences(self, sources) -> list[dict]:
        """
        다양한 형태(set/tuple/str/dict 등)로 올 수 있는 sources를
        프롬프트에서 기대하는 List[dict]로 강제 변환한다.
        dict에는 최소 키(title/url/source/date_published/score/text)를 채운다.
        """
        # 컨테이너 보정
        if sources is None:
            items = []
        elif isinstance(sources, dict):
            items = list(sources.values())
        elif isinstance(sources, list):
            items = sources
        else:
            items = list(sources)

        norm: list[dict] = []
        for it in items:
            if isinstance(it, dict):
                norm.append({
                    "title": it.get("title") or "(제목 없음)",
                    "url": it.get("url") or "",
                    "source": it.get("source") or "",
                    "date_published": it.get("date_published") or "",
                    "score": it.get("score", None),
                    "text": (it.get("text") or "").strip(),
                })
            elif isinstance(it, str):
                norm.append({
                    "title": "(제목 없음)",
                    "url": "",
                    "source": "",
                    "date_published": "",
                    "score": None,
                    "text": it.strip(),
                })
            elif isinstance(it, (tuple, list)) and len(it) == 2:
                a, b = it
                if isinstance(a, dict) and not isinstance(b, dict):
                    meta, text = a, str(b)
                elif isinstance(b, dict) and not isinstance(a, dict):
                    meta, text = b, str(a)
                else:
                    meta, text = {}, " ".join(str(x) for x in it)
                norm.append({
                    "title": (meta.get("title") if isinstance(meta, dict) else None) or "(제목 없음)",
                    "url": (meta.get("url") if isinstance(meta, dict) else "") or "",
                    "source": (meta.get("source") if isinstance(meta, dict) else "") or "",
                    "date_published": (meta.get("date_published") if isinstance(meta, dict) else "") or "",
                    "score": (meta.get("score") if isinstance(meta, dict) else None),
                    "text": text.strip(),
                })
            else:
                norm.append({
                    "title": "(제목 없음)",
                    "url": "",
                    "source": "",
                    "date_published": "",
                    "score": None,
                    "text": str(it).strip(),
                })
        return norm