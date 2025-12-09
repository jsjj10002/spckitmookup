# 프로젝트 구조

배포 구성에 맞게 정리된 프로젝트 구조입니다.

## 디렉토리 구조

```
SpckitAI/
├── frontend/              # 프론트엔드 (HTML/CSS/JavaScript)
│   ├── index.html        # 랜딩 페이지
│   ├── builder.html      # 빌더 페이지
│   ├── js/               # JavaScript 모듈
│   │   ├── api.js        # Gemini API 통신
│   │   ├── builder.js    # 빌더 페이지 로직
│   │   └── landing.js    # 랜딩 페이지 로직
│   ├── images/           # 이미지 에셋
│   └── *.css             # 스타일시트
│
├── backend/               # 백엔드 API (향후 개발 예정)
│   ├── prompts/          # 프롬프트 관리
│   │   ├── system-instruction.js    # 시스템 프롬프트
│   │   ├── user-prompt-template.js  # 사용자 프롬프트 템플릿
│   │   ├── index.js                  # 통합 모듈
│   │   └── README.md                 # 프롬프트 가이드
│   ├── data/             # 데이터베이스 파일
│   │   ├── pc_data_dump.sql         # PC 부품 데이터 덤프 (RAG용)
│   │   ├── PC 부품 DB 스키마 가이드.pdf
│   │   └── README.md                 # 데이터 가이드
│   └── README.md         # 백엔드 계획 문서
│
├── assets/                # 정적 에셋 파일
│   ├── 3d-models/        # 3D 모델 파일 (GLTF/GLB)
│   └── README.md         # 에셋 가이드
│
├── backup/                # 백업 디렉토리
│   ├── old_react_frontend/  # 구 React 프론트엔드 (v1)
│   ├── frontbackup/         # Figma 디자인 기반 초기 백업
│   └── README.md
│
├── scripts/               # 빌드 스크립트
│   └── build.js          # 프론트엔드 빌드 스크립트
│
├── docs/                  # 문서
├── research/              # 연구 자료
│
├── .env.local            # 환경 변수 (로컬 개발용)
├── package.json          # 프로젝트 설정
├── vite.config.ts        # Vite 설정
└── Dockerfile            # Docker 설정 (Cloud Run용)
```

## 환경 변수 설정

### 개발 환경 (.env.local)

```env
GEMINI_API_KEY="your-api-key-here"
VITE_GEMINI_API_KEY="your-api-key-here"
```

**참고**: Vite는 클라이언트에서 접근 가능한 환경 변수에 `VITE_` 접두사가 필요합니다.

### 프로덕션 환경

배포 플랫폼(Vercel, Cloud Run 등)의 환경 변수 설정에서 `VITE_GEMINI_API_KEY`를 설정하세요.

## 빌드 및 실행

```bash
# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 결과물 미리보기
npm run preview
```

## 배포 전략

### 프론트엔드
- **개발/스테이징**: Vercel 또는 Netlify
- **프로덕션**: Vercel (CDN 최적화)

### 백엔드 (향후)
- **API 서버**: GCP Cloud Run
- **RAG 검색**: 벡터 데이터베이스 + Cloud Run

### 에셋
- **3D 모델**: GCP Cloud Storage + CDN
- **이미지**: Vercel Blob Storage 또는 Cloud Storage

## 주요 변경사항

1. ✅ `front_v2` → `frontend`로 이름 변경
2. ✅ `.env.local`의 `GEMINI_API_KEY` 사용 설정
3. ✅ 백업 디렉토리 정리 (`old_react_frontend`, `frontbackup`)
4. ✅ 배포 구성에 맞는 디렉토리 구조 생성
5. ✅ 프롬프트 관련 코드를 `backend/prompts/`로 분리
6. ✅ 불필요한 파일 정리 (`dtest2.txt`, `front_v2/` 삭제)
7. ✅ SQL 데이터베이스 파일을 `backend/data/`로 이동 (RAG 구현 준비)

