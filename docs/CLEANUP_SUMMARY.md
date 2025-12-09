# 프로젝트 정리 요약

## 완료된 작업

### 1. 디렉토리 정리
- ✅ `front_v2/` 디렉토리 삭제 (이미 `frontend/`로 이동 완료)
- ✅ `dtest2.txt` 테스트 파일 삭제
- ✅ 백업 디렉토리 정리 완료 (`backup/`)

### 2. 프롬프트 관리 구조화
- ✅ 프롬프트 관련 코드를 `backend/prompts/`로 분리
  - `system-instruction.js`: 시스템 프롬프트 (AI 역할 정의)
  - `user-prompt-template.js`: 사용자 프롬프트 템플릿
  - `index.js`: 통합 모듈
  - `README.md`: 프롬프트 가이드
- ✅ 프론트엔드에서도 사용 가능하도록 `frontend/js/prompts.js` 생성
- ✅ `frontend/js/api.js`에서 프롬프트 모듈 사용하도록 수정

### 3. 문서 업데이트
- ✅ `CHANGELOG.md`: `front_v2` → `frontend` 참조 수정
- ✅ `DEPLOYMENT.md`: 경로 및 환경 변수명 수정 (`VITE_API_KEY` → `VITE_GEMINI_API_KEY`)
- ✅ `MIGRATION_SUMMARY.md`: 파일 구조 업데이트
- ✅ `PROJECT_STRUCTURE.md`: 프롬프트 구조 추가
- ✅ `backend/README.md`: 프롬프트 관리 섹션 추가

## 현재 프로젝트 구조

```
SpckitAI/
├── frontend/              # 프론트엔드
│   ├── js/
│   │   ├── api.js        # API 통신 (프롬프트 모듈 사용)
│   │   ├── prompts.js    # 프롬프트 (백엔드와 동기화)
│   │   ├── builder.js
│   │   └── landing.js
│   └── ...
│
├── backend/              # 백엔드
│   ├── prompts/          # 프롬프트 관리 (중앙 관리)
│   │   ├── system-instruction.js
│   │   ├── user-prompt-template.js
│   │   ├── index.js
│   │   └── README.md
│   ├── data/             # 데이터베이스 파일 (RAG 구현 준비)
│   │   ├── pc_data_dump.sql
│   │   ├── PC 부품 DB 스키마 가이드.pdf
│   │   └── README.md
│   └── README.md
│
├── backup/               # 백업
│   ├── old_react_frontend/
│   └── frontbackup/
│
├── assets/               # 에셋
├── sql/                  # 데이터베이스
└── ...
```

## 프롬프트 관리 전략

### 현재 구조
- **백엔드**: `backend/prompts/` - 프롬프트의 단일 소스 (Single Source of Truth)
- **프론트엔드**: `frontend/js/prompts.js` - 백엔드 프롬프트와 동기화

### 향후 계획
백엔드 API가 구축되면:
1. 프론트엔드는 백엔드 API를 호출하여 프롬프트를 가져옴
2. `frontend/js/prompts.js` 제거
3. 프롬프트 버전 관리 및 A/B 테스트 가능

## 정리된 파일 목록

### 삭제/이동된 항목
- `front_v2/` 디렉토리 삭제
- `dtest2.txt` 삭제
- `sql/` 디렉토리 → `backend/data/`로 이동 (RAG 구현 준비)

### 생성된 항목
- `backend/prompts/system-instruction.js`
- `backend/prompts/user-prompt-template.js`
- `backend/prompts/index.js`
- `backend/prompts/README.md`
- `backend/data/README.md`
- `frontend/js/prompts.js`

### 업데이트된 항목
- `frontend/js/api.js` - 프롬프트 모듈 사용
- `CHANGELOG.md`
- `DEPLOYMENT.md`
- `MIGRATION_SUMMARY.md`
- `PROJECT_STRUCTURE.md`
- `backend/README.md`

## 다음 단계

1. 백엔드 API 구축 시 프롬프트를 API로 제공
2. 프론트엔드에서 백엔드 API 호출로 전환
3. 프롬프트 버전 관리 시스템 구축
4. RAG 구현:
   - `backend/data/pc_data_dump.sql`을 데이터베이스에 임포트
   - 벡터 데이터베이스 구축
   - 부품 정보 검색 API 개발

