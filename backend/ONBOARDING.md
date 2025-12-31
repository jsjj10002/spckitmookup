# Spckit AI 백엔드 온보딩 가이드

> 새로운 팀원을 위한 개발 환경 설정 가이드

## 목차

- [빠른 시작](#빠른-시작)
- [상세 설정](#상세-설정)
- [모듈별 설치](#모듈별-설치)
- [개발 워크플로우](#개발-워크플로우)
- [문제 해결](#문제-해결)

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd workspace
```

### 2. uv 설치 (권장)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 설치 확인
uv --version
```

### 3. 가상 환경 생성 및 활성화

```bash
# backend 디렉토리에서
cd backend

# 가상 환경 생성
uv venv

# 활성화 (Linux/macOS)
source .venv/bin/activate

# 활성화 (Windows)
.venv\Scripts\activate
```

### 4. 의존성 설치 (온보딩용)

```bash
# 기본 + 개발 도구 + 온보딩 패키지
uv pip install -e ".[onboarding]"
```

### 5. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 설정
# GEMINI_API_KEY=your_api_key_here
```

### 6. 테스트 실행

```bash
pytest tests/ -v
```

---

## 상세 설정

### 환경 변수 (.env)

```env
# 필수
GEMINI_API_KEY=your_gemini_api_key

# 선택
ENVIRONMENT=development
AUTO_INIT_DB=true
GENERATION_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=models/text-embedding-004
LOG_LEVEL=INFO
```

### 벡터 데이터베이스 초기화

처음 실행 시 또는 데이터 변경 시:

```bash
python scripts/init_database.py
```

### 개발 서버 실행

```bash
# API 서버
uvicorn api.main:app --reload --port 8000

# Swagger UI 확인
# http://localhost:8000/docs
```

---

## 모듈별 설치

담당하는 모듈에 따라 추가 의존성을 설치한다.

### 설치 옵션

| 옵션 | 설명 | 설치 명령 |
|------|------|----------|
| `dev` | 개발 도구 (pytest, black, ruff) | `uv pip install -e ".[dev]"` |
| `onboarding` | 온보딩용 (dev + 기본 ML) | `uv pip install -e ".[onboarding]"` |
| `multi-agent` | CREWai 멀티 에이전트 | `uv pip install -e ".[multi-agent]"` |
| `price-prediction` | 가격 예측 (Prophet) | `uv pip install -e ".[price-prediction]"` |
| `recommendation` | GNN 추천 (PyTorch) | `uv pip install -e ".[recommendation]"` |
| `ontology` | 온톨로지 (RDFLib) | `uv pip install -e ".[ontology]"` |
| `all` | 전체 설치 | `uv pip install -e ".[all]"` |

### 모듈별 상세

#### 1. 멀티 에이전트 모듈 (`multi-agent`)

```bash
uv pip install -e ".[multi-agent]"
```

포함 패키지:
- crewai
- crewai-tools
- langchain
- langchain-google-genai

#### 2. PC 사양 진단 모듈

추가 패키지 불필요 (기본 의존성만 사용)

#### 3. 가격 예측 모듈 (`price-prediction`)

```bash
uv pip install -e ".[price-prediction]"
```

포함 패키지:
- prophet
- scikit-learn

> PyTorch Forecasting (TFT 모델)은 별도 설치 필요

#### 4. GNN 추천 시스템 모듈 (`recommendation`)

```bash
uv pip install -e ".[recommendation]"
```

포함 패키지:
- torch
- networkx

> torch-geometric은 CUDA 버전에 따라 별도 설치:
> ```bash
> # CPU 전용
> pip install torch-geometric
> 
> # CUDA 11.8
> pip install torch-geometric -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
> ```

#### 5. 호환성 검사 모듈 (`ontology`)

```bash
uv pip install -e ".[ontology]"
```

포함 패키지:
- rdflib
- owlready2

---

## 개발 워크플로우

### 브랜치 전략

```bash
# 새 기능 개발
git checkout -b feature/[모듈명]/[기능설명]/[날짜YYMMDD]

# 예시
git checkout -b feature/pc_diagnosis/add-benchmark-db/241231
```

### 코드 스타일

```bash
# 포맷팅
black .

# 린트
ruff check .

# 자동 수정
ruff check . --fix
```

### 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/test_pc_diagnosis.py -v

# 커버리지
pytest tests/ --cov=modules --cov-report=html
```

### 커밋 메시지 규칙

```
[타입]: 간단한 설명

타입:
- feat: 새 기능
- fix: 버그 수정
- docs: 문서 수정
- refactor: 리팩토링
- test: 테스트 추가/수정
```

---

## 문제 해결

### uv 설치 문제

```bash
# PATH 확인
echo $PATH | grep -o '[^:]*uv[^:]*'

# 직접 경로 지정
~/.cargo/bin/uv --version
```

### 의존성 충돌

```bash
# 가상 환경 재생성
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e ".[onboarding]"
```

### ChromaDB 오류

```bash
# SQLite 버전 문제
pip install pysqlite3-binary

# 또는 환경 변수 설정
export CHROMA_DB_IMPL=duckdb+parquet
```

### Gemini API 오류

1. API 키 확인: `.env` 파일에 `GEMINI_API_KEY` 설정 확인
2. API 할당량 확인: [Google AI Studio](https://aistudio.google.com/)에서 확인
3. 모델 이름 확인: `gemini-2.5-pro` 또는 `gemini-2.0-flash`

### 테스트 실패

```bash
# 개별 테스트 실행으로 원인 파악
pytest tests/test_pc_diagnosis.py::TestPCDiagnosisEngine::test_diagnosis_result -v

# 상세 로그 출력
pytest tests/ -v --tb=long
```

---

## 유용한 명령어

```bash
# 설치된 패키지 확인
uv pip list

# 특정 패키지 정보
uv pip show google-genai

# 의존성 트리
uv pip tree

# 패키지 업데이트
uv pip install --upgrade package_name

# 캐시 정리
uv cache clean
```

---

## 도움말

- **모듈 문서**: `backend/modules/README.md`
- **RAG 가이드**: `docs/RAG_GUIDE.md`
- **프로젝트 구조**: `docs/PROJECT_STRUCTURE.md`

문의: [팀 슬랙 채널] 또는 [이슈 트래커]
