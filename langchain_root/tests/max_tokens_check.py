"""
목적:
- 같은 질문/프롬프트로 max_tokens 값을 달리했을 때
  실제 출력 길이가 어떻게 달라지는지 비교합니다.
- 모델은 solar-pro, solar-mini를 모두 테스트합니다.

실행:
  python -m tests.max_tokens_check
"""

import time
from src.utils.config import AppConfig
from src.llm.solar import SolarClient

QUESTION = "최근 생성형 AI 규제 동향을 요약해줘."
EXTRA_RULES = (
    "불릿 5개 이상으로 자세히 설명해라. "
    "각 불릿은 최소 2문장 이상으로 작성해라. "
    "가능하면 날짜/고유명사를 Evidence에서 인용해서 구체적으로 써라. "
    "마지막에 Sources를 번호와 함께 모두 나열해라."
)

# 테스트할 max_tokens 값들
MAX_TOKENS_LIST = [200, 400, 800]
MODELS = ["solar-pro", "solar-mini"]

SYSTEM_PROMPT = (
    "당신은 뉴스 RAG 어시스턴트입니다.\n"
    "Evidence에 포함된 정보만 사용해 답변하세요. 추측/창작 금지.\n"
    "모르면 '모르겠습니다'라고 말하세요.\n"
    "한국어로 불릿 위주로 작성하세요.\n"
    "답변 마지막에 'Sources' 섹션을 만들고 참고 URL을 나열하세요.\n"
)

# 사용자 프롬프트(간단 예시). 실제 서비스에서는 빌더가 Evidence를 붙입니다.
USER_PROMPT_TEMPLATE = (
    "질문: {question}\n\n"
    "추가 지시: {extra}\n"
    "(참고: 이 테스트는 Evidence 없이 모델 길이 반응만 확인합니다.)"
)

def rough_token_count(text: str) -> int:
    # 아주 거친 추정: 공백 기준 토큰 수
    return len(text.split())

def main():
    cfg = AppConfig()
    cli = SolarClient(api_key=cfg.solar_api_key)

    print("[CHECK] max_tokens 길이 반응 테스트 시작")
    print(f"- models: {MODELS}")
    print(f"- max_tokens: {MAX_TOKENS_LIST}\n")

    for model in MODELS:
        print(f"=== MODEL: {model} ===")
        for mt in MAX_TOKENS_LIST:
            user_prompt = USER_PROMPT_TEMPLATE.format(
                question=QUESTION, extra=EXTRA_RULES
            )
            t0 = time.time()
            try:
                ans = cli.generate(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=model,
                    max_tokens=mt,
                )
                dt = (time.time() - t0) * 1000
                char_len = len(ans)
                tok_len = rough_token_count(ans)

                print(f"[max_tokens={mt:>3}] "
                      f"len(chars)={char_len:>4}  len(~tokens)={tok_len:>4}  "
                      f"latency={dt:>5.0f}ms")
                # 필요하면 앞부분 미리보기
                preview = ans.replace("\n", " ")[:180]
                print(f"  preview: {preview}...\n")

            except Exception as e:
                print(f"[max_tokens={mt}] 에러: {e}\n")

if __name__ == "__main__":
    main()