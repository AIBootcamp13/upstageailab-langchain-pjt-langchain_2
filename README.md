# AI 뉴스 RAG (LangChain + Upstage Solar + Chroma)

<br>

- _최신 AI 관련 RSS 기사를 수집·색인하고, 근거(Sources)와 함께 한국어 답변을 생성하는 RAG 데모 프로젝트입니다_


<br>

## 👨‍👩‍👦‍👦 팀 구성원

| ![이상원](https://avatars.githubusercontent.com/u/156163982?v=4) | ![강연경](https://avatars.githubusercontent.com/u/156163982?v=4) | ![이준석](https://avatars.githubusercontent.com/u/156163982?v=4) | ![정재훈](https://avatars.githubusercontent.com/u/156163982?v=4) | ![홍정민](https://avatars.githubusercontent.com/u/156163982?v=4) |
| :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: |
|            [이상원](https://github.com/UpstageAILab)             |            [강연경](https://github.com/UpstageAILab)             |            [이준석](https://github.com/UpstageAILab)             |            [정재훈](https://github.com/UpstageAILab)             |            [홍정민](https://github.com/UpstageAILab)             |
|                            팀장, 평가 지표 설계                             |                            RAG Pipeline 구축                             |                            코드 실행 및 구현                             |                            코드 실행 및 수정                             |                            전체적인 파이프라인 구축                             |

<br>

## 🔨 개발 환경 및 기술 스택
- 주 언어 : _python_
- 버전 및 이슈관리 : _ex) github_
- 협업 툴 : _github, notion, slack, zoom_

<br>

## TimeLine
2025.08.19 ~ 2028.08.29

<br>

## 파이프라인 개요
- 1. 수집 (Ingest)

+rss_crawler.py: 여러 RSS 주소를 순회 → 기사 본문만 추출(trafilatura) → 텍스트 정규화/해시 → SQLite 저장(중복 방지)_

- 2. 색인 (Index)

_indexer.py: 문서 청킹 → Upstage embedding‑passage로 임베딩 → Chroma 컬렉션에 업서트(메타데이터 포함)_

- 3. 검색 & 생성 (QA)

_search.py: embedding‑query로 질문 임베딩 → Chroma Top‑k 후보 → (옵션) MMR로 다양성 반영 → Evidence 컨텍스트/출처 구성_
_answerer.py: PromptBuilder로 System/User 프롬프트 구성 → **Solar(pro/mini)**로 생성 → Sources 섹션 포함 답변 생성_


<br>

## 📁 프로젝트 구조
```
langchain_root/
├─ app/
│  ├─ main.py                # 전체 파이프라인(수집→색인→QA) 동작 예시
│  └─ ui/app.py              # Streamlit 웹 UI
├─ configs/
│  ├─ app.yaml               # 경로/모델/리트리벌/로깅 등 주요 설정
│  ├─ chunking.yaml          # 청킹 전략 파라미터
│  ├─ embedding.yaml         # (확장용) 임베딩 관련 설정
│  └─ prompt.yaml            # (확장용) 프롬프트 설정
├─ src/
│  ├─ crawler/rss_crawler.py # RSS 파싱→본문 추출(trafilatura)→정규화
│  ├─ llm/                   # Solar API 어댑터, 프롬프트 빌더
│  ├─ qa/answerer.py         # Retriever+PromptBuilder+LLM 오케스트레이션
│  ├─ retriever/search.py    # Chroma 기반 검색(MMR 포함)
│  ├─ sql/db.py              # SQLite 문서 저장/조회
│  └─ vector_store/indexer.py# 청킹→임베딩→Chroma 업서트
├─ tests/                    # 단계별 스모크 테스트 스크립트
│  ├─ api_check.py           # Solar Chat API 연결 확인
│  ├─ indexer_check.py       # 색인 파이프라인 확인
│  ├─ retriever_check.py     # Top-k 리트리버 확인
│  ├─ answerer_check.py      # 모델별 생성 품질 비교 예시
│  ├─ prompt_check.py        # 프롬프트 조립 확인
│  └─ max_tokens_check.py    # max_tokens 영향 확인
├─ .env.example              # 환경변수 템플릿
└─ requirements.txt
```

<br>

## 💻​ 구현 기능
### 기능1 - 뉴스 수집과 인덱싱
- _ RSS 8개 소스에서 최신 글 자동 수집_
- _ 본문 정제 → 청크·오버랩 적용 → all-MiniLM-L6-v2 임베딩_
- _ Chroma(Vector) + SQLite(Metadata) 저장_
### 기능2 - 브리핑 & QA 체인
- _뉴스 브리핑 생성(요약) + 질의응답 지원_
- _질문을 임베딩하여 유사 문서 검색(MMR), 상위 k개 컨텍스트만 사용_
- _Solar LLM(temperature=0.0)**로 간결한 한 문장 답변, 원문 표기 보존 지시_

<br>

## 프로젝트 실행 방법 

### 1. 프로젝트 클론
- git clone https://github.com/welovecherry/langchain_jungmin_fork langchain_root
- cd langchain_root
- git checkout dev

### 2. 가상환경 및 패키지 설치
- python -m venv venv
- source venv/bin/activate  # Windows: venv\Scripts\activate
- pip install -r requirements.txt

### 3. 환경 변수 설정
- export UPSTAGES_API_KEY=your-api-key

### 4. 실행 (CLI 기반)
- python -m app.main

### 4.2 실행 (Streamlit 사용)
- $env:PYTHONPATH = (Get-Location).Path
- streamlit run app/ui/app.py
- 
<br>

## 📜 라이선스 / 크레딧
- _Upstage Solar API 및 임베딩 모델 활용_
- _오픈소스: chromadb, feedparser, trafilatura, streamlit 등_
