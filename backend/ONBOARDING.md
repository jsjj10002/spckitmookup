# Spckit AI 백엔드 온보딩 가이드

> 새로운 팀원을 위한 개발 환경 설정 가이드

---

## 빠른 시작 (3분)

```bash
# 1. uv 설치 (처음 한 번만)
powershell -c "irm https://astral.sh/uv/install.ps1 | more"

# 2. backend 디렉토리로 이동
cd backend

# 3. 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 4. 의존성 설치
uv pip install -e .

# 5. 환경 변수 설정
cp ../.env.example ../.env
# .env 파일에서 GEMINI_API_KEY 설정

# 6. 테스트 실행
pytest tests/ -v

# 7. API 서버 실행
uvicorn api.main:app --reload --port 8000
```

---

## 상세 설정

### 1. uv 설치

uv는 빠른 Python 패키지 관리자이다.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 설치 확인
uv --version
```

### 2. 가상 환경

```bash
cd backend

# 생성
uv venv

# 활성화 (Linux/macOS)
source .venv/bin/activate

# 활성화 (Windows)
.venv\Scripts\activate
```

### 3. 의존성 설치

```bash
# 전체 설치 (모든 모듈 포함)
uv pip install -e .
```

포함된 주요 패키지:
- **코어**: google-genai, chromadb, fastapi, pydantic
- **개발 도구**: pytest, black, ruff, ipython
- **멀티 에이전트**: crewai, langchain
- **가격 예측**: prophet, scikit-learn
- **추천 시스템**: torch, networkx
- **온톨로지**: rdflib, owlready2

### 4. 환경 변수

```bash
# 템플릿 복사
cp ../.env.example ../.env
```

`.env` 파일 편집:

```env
# 필수
GEMINI_API_KEY=your_api_key_here

# 선택
ENVIRONMENT=development
AUTO_INIT_DB=true
```

API 키 발급: [Google AI Studio](https://aistudio.google.com/)

### 5. 벡터 DB 초기화

처음 실행 시 또는 데이터 갱신 시:

```bash
python scripts/init_database.py
```

---

## 개발 명령어

```bash
# API 서버 실행
uvicorn api.main:app --reload --port 8000

# 테스트 실행
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/test_pc_diagnosis.py -v

# 코드 포맷팅
black .

# 린트 검사
ruff check .

# 린트 자동 수정
ruff check . --fix
```

---

## 프로젝트 구조

```
backend/
├── api/              # FastAPI REST API
├── rag/              # RAG 핵심 모듈
├── modules/          # AI 모듈
│   ├── multi_agent/      # CREWai 멀티 에이전트
│   ├── pc_diagnosis/     # PC 사양 진단
│   ├── price_prediction/ # 가격 예측
│   ├── recommendation/   # GNN 추천
│   └── compatibility/    # 호환성 검사
├── tests/            # 테스트 파일
├── scripts/          # 유틸리티
└── data/             # 데이터 파일
```

---

## 문제 해결

### uv 명령어를 찾을 수 없음

```bash
# PATH에 추가 (bash)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 의존성 충돌

```bash
# 가상 환경 재생성
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### torch 설치 실패 (CUDA)

```bash
# CPU 버전 명시 설치
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### ChromaDB 오류

```bash
# pysqlite3 설치
pip install pysqlite3-binary
```

---

## 문서

- [모듈 개발 가이드](./modules/README.md)
- [RAG 시스템 가이드](../docs/RAG_GUIDE.md)
- [빠른 시작](../docs/QUICK_START.md)
