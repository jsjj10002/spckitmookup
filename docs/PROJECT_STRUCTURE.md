# 프로젝트 구조 상세

Spckit AI 프로젝트의 디렉토리 및 파일 구조를 상세히 설명한다.

---

## 목차

- [전체 구조](#전체-구조)
- [Frontend 구조](#frontend-구조)
- [Backend 구조](#backend-구조)
- [문서 구조](#문서-구조)
- [설정 파일](#설정-파일)
- [스크립트](#스크립트)

---

## 전체 구조

```
SpckitAI/
├── frontend/              # 프론트엔드 (HTML/CSS/JS)
├── backend/               # 백엔드 (Python/FastAPI)
│   ├── api/              # REST API
│   ├── rag/              # RAG 시스템 [완성]
│   ├── modules/          # AI 모듈 [개발 중]
│   ├── tests/            # 테스트
│   ├── scripts/          # 유틸리티 스크립트
│   └── data/             # 데이터 파일
├── docs/                  # 문서
├── assets/                # 공용 에셋
│
├── Dockerfile             # Docker 설정
├── .env.example           # 환경 변수 템플릿
├── package.json           # Node.js 설정
├── vite.config.ts         # Vite 빌드 설정
├── requirements.txt       # Python 의존성 (pip용)
│
├── run_dev.bat/sh         # 개발 서버 실행
└── setup_dev.bat/sh       # 개발 환경 설정
```

---

## Frontend 구조

```
frontend/
├── index.html             # 랜딩 페이지 (메인)
├── builder.html           # PC 빌더 페이지 (4분할 레이아웃)
│
├── landing.css            # 랜딩 페이지 스타일
├── builder.css            # 빌더 페이지 스타일
│
├── js/
│   ├── api.js             # 백엔드 API 통신 모듈
│   ├── builder.js         # 빌더 페이지 로직
│   │   ├── 채팅 기능
│   │   ├── 부품 선택/제거
│   │   ├── 총 가격 계산
│   │   └── 타이핑 애니메이션
│   ├── landing.js         # 랜딩 페이지 로직
│   └── prompts.js         # 프롬프트 관리 (백엔드 동기화용)
│
├── images/
│   ├── spckit-logo.svg    # 로고
│   ├── round.png          # 배경 이미지
│   └── *.png              # 기타 이미지
│
└── README.md              # 프론트엔드 가이드
```

### 페이지 구성

| 페이지 | 파일 | 설명 |
|--------|------|------|
| 랜딩 | `index.html` | 초기 메시지 입력 → 빌더로 이동 |
| 빌더 | `builder.html` | 4분할 레이아웃 (채팅, 선택 부품, 3D 뷰어, 추천) |

### 빌더 페이지 레이아웃

```
┌─────────────────────────────────────────┐
│              Header (Breadcrumb)        │
├──────────┬──────────────────────────────┤
│          │  선택된 부품   │  3D 뷰어    │
│  채팅    │  (Selected)    │  (Preview)  │
│  패널    ├────────────────┴─────────────┤
│          │  추천 부품 (Recommendations)  │
└──────────┴───────────────────────────────┘
```

---

## Backend 구조

```
backend/
├── api/                   # FastAPI REST API
│   ├── __init__.py
│   └── main.py            # API 엔드포인트 라우터
│       ├── GET  /
│       ├── GET  /health
│       ├── GET  /stats
│       ├── POST /query
│       ├── POST /query-by-specs
│       └── POST /compare
│
├── rag/                   # RAG 핵심 모듈 [완성]
│   ├── __init__.py
│   ├── config.py          # 설정 관리 (환경 변수, 경로)
│   ├── embedder.py        # Gemini Embedding API 래퍼
│   ├── vector_store.py    # ChromaDB 관리
│   ├── retriever.py       # 벡터 검색, Top-K 필터링
│   ├── generator.py       # Gemini 응답 생성, 프롬프트 관리
│   ├── data_parser.py     # SQL 덤프 파싱
│   ├── pipeline.py        # RAG 파이프라인 통합
│   └── step_by_step.py    # 단계별 선택 파이프라인 [뼈대]
│
├── modules/               # AI 모듈 [개발 중]
│   ├── __init__.py
│   ├── README.md          # 모듈 개발 가이드
│   ├── SERVICE_ARCHITECTURE.md  # 서비스 아키텍처 문서
│   │
│   ├── multi_agent/       # CREWai 멀티 에이전트 [뼈대]
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # 에이전트 오케스트레이터
│   │   └── agents.py          # 개별 에이전트 정의
│   │       ├── RequirementAnalyzer
│   │       ├── BudgetPlanner
│   │       ├── ComponentSelector
│   │       ├── CompatibilityChecker
│   │       └── RecommendationWriter
│   │
│   ├── pc_diagnosis/      # PC 사양 진단 [뼈대]
│   │   ├── __init__.py
│   │   ├── engine.py          # 진단 엔진
│   │   ├── collectors.py      # 하드웨어 정보 수집
│   │   └── analyzers.py       # 병목 분석, 업그레이드 조언
│   │
│   ├── price_prediction/  # 가격 예측 [뼈대]
│   │   ├── __init__.py
│   │   ├── predictor.py       # 예측 모델 (Prophet/TFT)
│   │   ├── data_collector.py  # 가격 데이터 수집
│   │   └── features.py        # 시계열 특성 추출
│   │
│   ├── recommendation/    # GNN 추천 시스템 [뼈대]
│   │   ├── __init__.py
│   │   ├── engine.py          # 추천 엔진
│   │   ├── graph_builder.py   # 부품 그래프 구축
│   │   └── models.py          # GNN 모델 (GraphSAGE/GAT)
│   │
│   └── compatibility/     # 호환성 검사 [뼈대]
│       ├── __init__.py
│       ├── engine.py          # 호환성 검사 엔진
│       ├── ontology.py        # PC 부품 온톨로지
│       └── rules.py           # 호환성 규칙 정의
│           ├── CPU-메인보드 소켓
│           ├── 메모리-메인보드 타입
│           ├── GPU-케이스 길이
│           └── 전력 요구량
│
├── tests/                 # 테스트 파일
│   ├── __init__.py
│   ├── test_multi_agent.py
│   ├── test_pc_diagnosis.py
│   ├── test_price_prediction.py
│   ├── test_recommendation.py
│   ├── test_compatibility.py
│   └── test_rag_force_generation.py
│
├── scripts/               # 유틸리티 스크립트
│   ├── __init__.py
│   ├── README.md              # 스크립트 설명
│   ├── init_database.py       # 벡터 DB 초기화
│   ├── test_rag.py            # RAG 시스템 테스트
│   ├── setup_dev.py           # 개발 환경 설정
│   ├── check_sql.py           # SQL 파일 확인
│   └── debug_sql_parse.py     # SQL 파싱 디버그
│
├── data/                  # 데이터 파일
│   ├── README.md
│   ├── pc_data_dump.sql       # PC 부품 DB 덤프 (11MB)
│   ├── PC 부품 DB 스키마 가이드.pdf
│   │
│   ├── compatibility/         # 호환성 데이터 [구축 필요]
│   ├── pc_diagnosis/          # 벤치마크 데이터 [구축 필요]
│   ├── price_prediction/      # 가격 이력 데이터 [구축 필요]
│   └── recommendation/        # 그래프 데이터 [구축 필요]
│
├── chroma_db/             # ChromaDB 저장소 (자동 생성)
│
├── pyproject.toml         # Python 프로젝트 설정 (uv)
├── requirements.txt       # pip 호환 의존성
├── ONBOARDING.md          # 온보딩 가이드
└── README.md              # 백엔드 가이드
```

### RAG 모듈 상세

| 파일 | 클래스/함수 | 역할 |
|------|-------------|------|
| `config.py` | - | 환경 변수, 경로, 모델 설정 |
| `embedder.py` | `GeminiEmbedder` | 텍스트 → 768차원 벡터 변환 |
| `vector_store.py` | `PCComponentVectorStore` | ChromaDB 컬렉션 관리 |
| `retriever.py` | `PCComponentRetriever` | Top-K 검색, 카테고리 필터 |
| `generator.py` | `PCRecommendationGenerator` | Gemini로 추천 생성 |
| `data_parser.py` | `PCDataParser` | SQL INSERT → 문서 변환 |
| `pipeline.py` | `RAGPipeline` | 전체 워크플로우 통합 |

### AI 모듈 상태 요약

| 모듈 | 상태 | 주요 기능 | 필요 데이터 |
|------|------|----------|------------|
| `compatibility` | 뼈대 | 부품 호환성 검증 | 소켓/폼팩터 매핑 |
| `pc_diagnosis` | 뼈대 | 성능 진단, 업그레이드 | 벤치마크 점수 |
| `price_prediction` | 뼈대 | 가격 추세 예측 | 가격 이력 |
| `recommendation` | 뼈대 | GNN 기반 추천 | 그래프 데이터 |
| `multi_agent` | 뼈대 | 복합 추천 | - |

---

## 문서 구조

```
docs/
├── INDEX.md               # 문서 목차 (이 문서들의 인덱스)
│
├── QUICK_START.md         # 빠른 시작 가이드 (5분 설정)
├── TROUBLESHOOTING.md     # 문제 해결 가이드
│
├── RAG_GUIDE.md           # RAG 시스템 완전 가이드
├── PROJECT_STRUCTURE.md   # 이 문서
│
├── DEPLOYMENT_GUIDE.md    # 프로덕션 배포 가이드
│
├── CHANGELOG.md           # 버전별 변경 이력
├── SUMMARY.md             # 프로젝트 핵심 요약
│
├── .gitignore.md          # Git 무시 파일 가이드
└── device-insights-research.md  # 연구 자료
```

---

## 설정 파일

### 루트 설정 파일

| 파일 | 용도 |
|------|------|
| `Dockerfile` | Docker 이미지 빌드 설정 |
| `.env.example` | 환경 변수 템플릿 |
| `package.json` | Node.js 의존성 및 스크립트 |
| `vite.config.ts` | Vite 빌드 설정 |
| `vercel.json` | Vercel 배포 설정 |
| `tsconfig.json` | TypeScript 설정 |
| `requirements.txt` | Python 의존성 (pip용) |

### Backend 설정 파일

| 파일 | 용도 |
|------|------|
| `backend/pyproject.toml` | Python 프로젝트 설정 (uv) |
| `backend/.env` | 환경 변수 (생성 필요) |

### 환경 변수 (.env)

```env
# 필수
GEMINI_API_KEY=your_api_key_here

# 선택
ENVIRONMENT=development
AUTO_INIT_DB=true
LOG_LEVEL=INFO
```

---

## 스크립트

### 개발 환경 스크립트

| 파일 | 플랫폼 | 용도 |
|------|--------|------|
| `setup_dev.bat` | Windows | 개발 환경 자동 설정 |
| `setup_dev.sh` | Linux/Mac | 개발 환경 자동 설정 |
| `run_dev.bat` | Windows | 프론트+백엔드 통합 실행 |
| `run_dev.sh` | Linux/Mac | 프론트+백엔드 통합 실행 |
| `run_test.bat` | Windows | RAG 시스템 테스트 |
| `run_test.sh` | Linux/Mac | RAG 시스템 테스트 |

### Backend 스크립트

| 파일 | 용도 | 실행 방법 |
|------|------|----------|
| `scripts/init_database.py` | 벡터 DB 초기화 | `python backend/scripts/init_database.py` |
| `scripts/test_rag.py` | RAG 테스트 | `python backend/scripts/test_rag.py` |
| `scripts/check_sql.py` | SQL 파일 확인 | `python backend/scripts/check_sql.py` |

### 빌드 스크립트

| 파일 | 용도 |
|------|------|
| `scripts/build.js` | 프론트엔드 빌드 (Vite 래퍼) |

---

## 데이터 흐름

```
[SQL 덤프 파일]
     │
     ▼
[data_parser.py] ─── 파싱 ───▶ [135,660 레코드]
     │
     ▼
[문서 생성] ─── 벡터화 ───▶ [3,000 문서]
     │
     ▼
[embedder.py] ─── 임베딩 ───▶ [768차원 벡터]
     │
     ▼
[vector_store.py] ─── 저장 ───▶ [ChromaDB]
     │
     ▼
[retriever.py] ─── 검색 ───▶ [Top-K 결과]
     │
     ▼
[generator.py] ─── 생성 ───▶ [AI 추천]
```

---

## 지원 데이터 카테고리

| 카테고리 | 테이블명 | 설명 |
|----------|----------|------|
| CPU | `cpu` | 프로세서 |
| GPU | `gpu` | 그래픽카드 |
| RAM | `memory` | 메모리 |
| SSD | `ssd` | SSD 저장장치 |
| HDD | `hdd` | HDD 저장장치 |
| 메인보드 | `motherboard` | 메인보드 |
| 파워 | `power` | 파워 서플라이 |
| 케이스 | `case` | PC 케이스 |
| 쿨러 | `cooler` | CPU 쿨러 |
| 모니터 | `monitor` | 모니터 |

---

**문서 최종 업데이트**: 2026-01-02  
**버전**: 2.1.0
