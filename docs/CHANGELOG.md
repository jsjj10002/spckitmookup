# Changelog

프로젝트의 주요 변경 사항을 기록합니다.

## [2.0.0] - 2025-11-19

### Added (추가됨)

#### RAG 시스템 완전 구현
- ✨ Google Gemini Embedding API 통합 (`models/text-embedding-004`)
- ✨ ChromaDB 벡터 데이터베이스 구축
- ✨ SQL 데이터 파서 구현 (135,660개 레코드 처리)
- ✨ 의미 기반 유사도 검색 (Top-K 알고리즘)
- ✨ Gemini 2.0 Flash 기반 AI 추천 생성
- ✨ RAG 파이프라인 통합 (`backend/rag/pipeline.py`)

#### Backend 인프라
- 📦 FastAPI 기반 REST API 구조 (`backend/api/main.py`)
- 📦 uv 패키지 관리자 도입
- 📦 `pyproject.toml` 기반 Python 프로젝트 설정
- 📦 Windows 배치 스크립트 (`run_dev.bat`, `run_test.bat` - 프로젝트 루트로 이동)
- 📦 종합 테스트 스크립트 (`backend/scripts/test_rag.py`)

#### 문서화
- 📚 RAG 시스템 완전 가이드 (`backend/RAG_GUIDE.md`)
- 📚 빠른 시작 가이드 (`backend/QUICK_START.md`)
- 📚 문제 해결 가이드 (`backend/TROUBLESHOOTING.md`)
- 📚 프로젝트 구조 문서 업데이트
- 📚 포괄적인 README.md 작성

#### 데이터 관리
- 💾 SQL 데이터를 `backend/data/`로 이동
- 💾 10개 PC 부품 테이블 지원 (case, cpu, gpu, memory 등)
- 💾 3,000개 벡터 문서 생성 및 저장
- 💾 데이터 스키마 가이드 추가

### Changed (변경됨)

#### 프로젝트 구조 재편성
- 🔄 `front_v2` → `frontend` 이름 변경
- 🔄 배포 지향 디렉토리 구조 구축
  - `frontend/` - 프론트엔드 애플리케이션
  - `backend/` - RAG 백엔드 시스템
  - `assets/` - 공용 에셋
  - `backup/` - 이전 버전 백업
- 🔄 Vite 설정 업데이트 (`vite.config.ts`)
- 🔄 빌드 스크립트 경로 수정 (`scripts/build.js`)

#### API 통합 개선
- 🔧 Gemini API 키 관리 강화
  - `.env.local` 파일을 통한 로컬 개발
  - 환경 변수를 통한 프로덕션 배포
  - `VITE_GEMINI_API_KEY` 지원
- 🔧 하드코딩된 API 키 제거
- 🔧 동적 환경 변수 로딩

#### 프롬프트 관리
- 📝 프롬프트를 `backend/prompts/`로 분리
- 📝 시스템 인스트럭션 모듈화
- 📝 사용자 프롬프트 템플릿 분리
- 📝 프론트엔드 임시 프롬프트 파일 추가 (`frontend/js/prompts.js`)

#### 데이터 처리
- 🔨 SQL 파서 개선
  - MySQL 특수 주석 제거
  - `INSERT INTO table VALUES` 형식 지원
  - 컬럼명 없는 덤프 파일 처리
  - 중첩 괄호 처리 개선
- 🔨 ChromaDB 메타데이터 정제
  - None 값 자동 필터링
  - 타입 검증 (bool, int, float, str)
  - 안전한 문자열 변환

### Fixed (수정됨)

#### 한글 인코딩 문제
- 🐛 Windows 배치 파일 UTF-8 인코딩 설정 (`chcp 65001`)
- 🐛 SQL 파일 읽기 시 `errors="ignore"` 적용
- 🐛 로그 출력 인코딩 오류 해결

#### SQL 파싱 오류
- 🐛 0개 레코드 파싱 문제 해결
- 🐛 MySQL 덤프 형식 호환성 개선
- 🐛 LOCK TABLES 문 처리
- 🐛 컬럼 수 불일치 처리

#### ChromaDB 통합 오류
- 🐛 메타데이터 타입 오류 해결
- 🐛 None 값으로 인한 저장 실패 수정
- 🐛 벡터 임베딩 배치 처리 안정화

#### uv 빌드 오류
- 🐛 `pyproject.toml` 패키지 정의 추가
- 🐛 `hatchling` 빌드 설정 수정
- 🐛 `[tool.hatch.build.targets.wheel]` 설정

#### 파일 정리
- 🗑️ `dtest2.txt` 삭제
- 🗑️ 중복 `front_v2` 디렉토리 정리
- 🗑️ `requirements.txt` 제거 (pyproject.toml로 대체)

### Removed (제거됨)

- ❌ 하드코딩된 임시 API 키
- ❌ 사용하지 않는 React 프론트엔드 (`old_react_frontend`)
- ❌ 중복 백업 파일들
- ❌ 불필요한 테스트 파일들

### Security (보안)

- 🔒 API 키 환경 변수화
- 🔒 `.env.local` 파일 `.gitignore`에 추가
- 🔒 민감 정보 하드코딩 제거

## [Unreleased] (개발 중)

### Added - 2025-01-XX (RAG 시스템 구현)

#### RAG (Retrieval-Augmented Generation) 시스템 완성
- **백엔드 구조 구축**:
  - `backend/rag/` 모듈 생성
    - `embedder.py`: Gemini API를 사용한 임베딩 생성기
    - `vector_store.py`: ChromaDB 벡터 데이터베이스 관리
    - `data_parser.py`: SQL 덤프 파일 파싱 및 부품 정보 추출
    - `retriever.py`: 의미 기반 부품 검색 및 필터링
    - `generator.py`: Gemini API를 사용한 추천 생성
    - `pipeline.py`: 전체 RAG 시스템 통합
    - `config.py`: 시스템 설정 관리

- **API 서버 구현**:
  - `backend/api/main.py`: FastAPI 기반 REST API
  - 엔드포인트:
    - `POST /query`: 기본 부품 추천 쿼리
    - `POST /query-by-specs`: 사양 기반 부품 추천
    - `POST /compare`: 부품 비교 분석
    - `GET /stats`: 시스템 통계 조회
    - `GET /health`: 헬스 체크

- **유틸리티 스크립트**:
  - `backend/scripts/init_database.py`: 벡터 DB 초기화
  - `backend/scripts/test_rag.py`: RAG 시스템 테스트

- **패키지 관리**:
  - `backend/pyproject.toml`: uv 기반 의존성 관리
  - 주요 의존성:
    - google-generativeai: Gemini API
    - chromadb: 벡터 데이터베이스
    - fastapi: API 서버
    - pandas, numpy: 데이터 처리

- **문서화**:
  - `backend/README.md`: 백엔드 전체 가이드
  - `backend/RAG_GUIDE.md`: RAG 시스템 완전 사용 가이드
  - `.env.example`: 환경 변수 예시

#### 데이터 구조 변경
- `sql/` 디렉토리를 `backend/data/`로 이동
  - PC 부품 데이터 (11MB SQL 덤프)
  - DB 스키마 가이드 PDF
  - RAG 구현을 위한 데이터 준비 완료

### Changed

#### 프로젝트 구조 개선
- `front_v2/` → `frontend/`로 디렉토리명 변경
- 백엔드 중심 구조로 재편성
- 프롬프트 관리를 `backend/prompts/`로 분리

#### 환경 변수 관리
- `VITE_API_KEY` → `VITE_GEMINI_API_KEY`로 통일
- `.env.local` 사용 (개발 환경)
- 배포 환경에서는 플랫폼 환경 변수 사용

#### 문서 업데이트
- `PROJECT_STRUCTURE.md`: RAG 시스템 구조 추가
- `DEPLOYMENT.md`: 환경 변수명 수정
- `MIGRATION_SUMMARY.md`: 최신 변경사항 반영

### Removed
- `requirements.txt`: uv 패키지 관리자 사용으로 `pyproject.toml`로 대체
- `dtest2.txt`: 불필요한 테스트 파일 삭제
- `front_v2/`: `frontend/`로 통합

## [2.0.0] - 2025-01-XX

### Added
- `.env.local` 파일 생성 및 `GEMINI_API_KEY` 설정
- `frontend/js/api.js`에 환경 변수 기반 API 키 로딩 구현
- `frontend/js/prompts.js` 생성 (백엔드 프롬프트와 동기화)
- `backend/prompts/` 디렉토리 생성
  - `system-instruction.js`: 시스템 프롬프트
  - `user-prompt-template.js`: 사용자 프롬프트 템플릿
  - `index.js`: 통합 모듈
  - `README.md`: 프롬프트 가이드

### Changed
- `frontend/js/api.js`: 하드코딩된 API 키 제거, 환경 변수 사용
- `vite.config.ts`: `root`를 `frontend`로 변경
- `package.json`: `dev` 스크립트 경로 수정
- `scripts/build.js`: 빌드 소스 경로를 `frontend`로 변경
- 프롬프트 관리를 백엔드로 분리하여 중앙 집중화

## [1.0.0] - 2024-XX-XX

### Added
- 초기 프로젝트 구조
- Figma 디자인 기반 HTML/CSS/JavaScript 구현
- Gemini API 통합 (API 키 하드코딩)
- 기본 PC 빌더 기능

### Changed
- React 기반 프론트엔드에서 순수 HTML/CSS/JavaScript로 전환

---

## 범례

- `Added`: 새로운 기능 추가
- `Changed`: 기존 기능 변경
- `Deprecated`: 곧 제거될 기능
- `Removed`: 제거된 기능
- `Fixed`: 버그 수정
- `Security`: 보안 관련 변경

## 버전 번호 규칙

이 프로젝트는 [Semantic Versioning](https://semver.org/)을 따릅니다.

- `MAJOR`: 호환되지 않는 API 변경
- `MINOR`: 하위 호환성을 유지하는 기능 추가
- `PATCH`: 하위 호환성을 유지하는 버그 수정
