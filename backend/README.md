# Backend - Spckit AI 시스템

> PC 부품 추천을 위한 RAG 및 AI 모듈 백엔드

## 개요

이 디렉토리는 Spckit AI의 백엔드 시스템을 포함한다.

- **RAG 시스템**: 부품 검색 및 추천 생성
- **AI 모듈**: 사양 진단, 가격 예측, 호환성 검사 등

## 구조

```
backend/
├── api/                    # FastAPI REST API
│   ├── main.py            # API 엔드포인트
│   └── __init__.py
│
├── rag/                   # RAG 핵심 모듈
│   ├── config.py          # 설정 관리
│   ├── embedder.py        # 임베딩 생성
│   ├── vector_store.py    # ChromaDB 관리
│   ├── retriever.py       # 문서 검색
│   ├── generator.py       # AI 응답 생성
│   ├── data_parser.py     # SQL 파싱
│   ├── pipeline.py        # RAG 파이프라인
│   └── step_by_step.py    # 단계별 선택 파이프라인 (NEW)
│
├── modules/               # AI 모듈 (NEW)
│   ├── multi_agent/       # CREWai 멀티 에이전트
│   ├── pc_diagnosis/      # PC 사양 진단
│   ├── price_prediction/  # 가격 예측
│   ├── recommendation/    # GNN 추천 시스템
│   ├── compatibility/     # 호환성 검사 엔진
│   └── README.md          # 모듈 상세 문서
│
├── tests/                 # 테스트 파일 (NEW)
│   ├── test_multi_agent.py
│   ├── test_pc_diagnosis.py
│   ├── test_price_prediction.py
│   ├── test_recommendation.py
│   └── test_compatibility.py
│
├── scripts/               # 유틸리티 스크립트
│   ├── init_database.py   # DB 초기화
│   └── test_rag.py        # RAG 테스트
│
├── data/                  # 데이터 파일
│   └── pc_data_dump.sql   # PC 부품 DB
│
├── chroma_db/             # ChromaDB 저장소 (생성됨)
├── prompts/               # 프롬프트 템플릿
├── pyproject.toml         # Python 프로젝트 설정
└── .env                   # 환경 변수 (생성 필요)
```

## 🚀 빠른 시작

상세한 가이드는 **[docs/QUICK_START.md](../docs/QUICK_START.md)**를 참조하세요.

```bash
# 1. 가상 환경 생성
uv venv

# 2. 활성화 (Windows)
.venv\Scripts\activate

# 3. 의존성 설치
uv pip install -e .

# 4. 환경 변수 설정
# .env 파일 생성 후 GEMINI_API_KEY 추가

# 5. 데이터베이스 초기화 (프로젝트 루트에서)
cd ..
backend\run_init.bat

# 6. 테스트
backend\run_test.bat
```

## 📚 상세 문서

- **[RAG 시스템 가이드](../docs/RAG_GUIDE.md)** - 완전한 RAG 시스템 설명
- **[빠른 시작](../docs/QUICK_START.md)** - 단계별 설정 가이드
- **[문제 해결](../docs/TROUBLESHOOTING.md)** - 일반적인 오류 해결
- **[배포 가이드](../docs/DEPLOYMENT_GUIDE.md)** - 프로덕션 배포

## 🔧 개발

### 의존성 추가

```bash
# pyproject.toml에 추가 후
uv pip install -e .
```

### 테스트

```bash
pytest tests/
```

### API 서버 실행 (개발 예정)

```bash
uvicorn api.main:app --reload --port 8080
```

## 🌐 API 엔드포인트 (개발 중)

- `GET /health` - 헬스 체크
- `POST /api/recommend` - PC 부품 추천
- `POST /api/query` - RAG 쿼리

## 🔐 환경 변수

`.env` 파일 생성:

```env
GEMINI_API_KEY=your_api_key_here
```

## 📊 데이터

- **135,660개** PC 부품 레코드
- **10개** 부품 카테고리
- **3,000개** 벡터 문서

---

**더 자세한 정보는 [docs/](../docs/) 폴더를 참조하세요.**
