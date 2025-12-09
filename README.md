# Spckit AI - PC 부품 추천 시스템

> AI 기반 맞춤형 PC 부품 추천 및 견적 서비스

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Node](https://img.shields.io/badge/node-18+-green)

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [RAG 시스템](#rag-시스템)
- [API 문서](#api-문서)
- [배포](#배포)
- [문제 해결](#문제-해결)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

## 🎯 프로젝트 개요

**Spckit AI**는 Google Gemini 2.0 Flash API와 RAG(Retrieval-Augmented Generation) 기술을 활용하여 사용자의 요구사항, 예산, 사용 목적에 따라 최적의 PC 부품 조합을 추천하는 지능형 시스템입니다.

### 핵심 가치

- 🎯 **맞춤형 추천**: 사용자의 예산과 목적에 맞는 정확한 부품 추천
- 🔍 **실시간 검색**: 135,000+ 부품 데이터베이스에서 벡터 기반 의미 검색
- 💡 **AI 기반 분석**: Gemini를 활용한 상세한 견적 분석
- ⚡ **빠른 응답**: ChromaDB 벡터 저장소를 통한 밀리초 단위 검색

## ✨ 주요 기능

### 1. AI 기반 PC 부품 추천
- 자연어 쿼리를 통한 직관적인 부품 검색
- 예산, 성능, 용도를 고려한 맞춤형 추천
- 호환성 검증 및 최적화 제안

### 2. RAG 시스템
- **135,660개** 실제 부품 데이터 기반
- **3,000개** 문서 벡터화 완료
- 의미 기반 유사도 검색 (50%+ 정확도)
- 실시간 부품 정보 업데이트

### 3. 인터랙티브 UI
- 대화형 챗봇 인터페이스
- 실시간 견적 계산
- 부품 비교 및 상세 정보 제공

### 4. 3D 시각화 (개발 예정)
- 선택한 부품의 3D 모델 미리보기
- 실시간 조립 시뮬레이션
- 완성된 PC의 시각적 표현

## 🛠 기술 스택

### Frontend
- **Framework**: Vanilla JavaScript + Vite
- **Styling**: Custom CSS
- **Build Tool**: Vite 6.2.0
- **API Client**: Fetch API

### Backend (RAG System)
- **Language**: Python 3.10+
- **AI/ML**:
  - Google Generative AI (Gemini 2.0 Flash)
  - Gemini Embedding API (text-embedding-004)
- **Vector Database**: ChromaDB 0.5.0+
- **Data Processing**:
  - Pandas 2.0.0+
  - NumPy 1.24.0+
  - SQLParse 0.5.0+
- **API Framework**: FastAPI 0.110.0+
- **Package Manager**: uv (Python)

### Database
- **Vector Store**: ChromaDB (로컬)
- **Source Data**: MySQL Dump (135,660 레코드)

### 배포 (예정)
- **Frontend**: Vercel / Netlify
- **Backend**: GCP Cloud Run / Docker
- **3D Assets**: CDN

## 📁 프로젝트 구조

```
SpckitAI/
├── frontend/                # 프론트엔드 애플리케이션
│   ├── index.html          # 메인 페이지
│   ├── builder.html        # 부품 선택 페이지
│   ├── css/                # 스타일시트
│   ├── js/
│   │   ├── api.js          # Gemini API 통신
│   │   ├── prompts.js      # AI 프롬프트 관리
│   │   └── *.js            # 기타 모듈
│   └── assets/             # 정적 리소스
│
├── backend/                # RAG 백엔드 시스템
│   ├── rag/                # RAG 핵심 모듈
│   │   ├── config.py       # 설정 관리
│   │   ├── embedder.py     # 임베딩 생성
│   │   ├── vector_store.py # ChromaDB 관리
│   │   ├── retriever.py    # 문서 검색
│   │   ├── generator.py    # AI 응답 생성
│   │   ├── data_parser.py  # SQL 데이터 파싱
│   │   └── pipeline.py     # RAG 파이프라인
│   │
│   ├── api/                # FastAPI 애플리케이션
│   │   └── main.py         # API 엔드포인트
│   │
│   ├── scripts/            # 유틸리티 스크립트
│   │   ├── init_database.py    # DB 초기화
│   │   └── test_rag.py         # RAG 테스트
│   │
│   ├── data/               # 데이터 파일
│   │   ├── pc_data_dump.sql    # PC 부품 DB (11MB)
│   │   └── README.md
│   │
│   ├── chroma_db/          # ChromaDB 저장소 (생성됨)
│   ├── .env                # 환경 변수 (생성 필요)
│   ├── pyproject.toml      # Python 프로젝트 설정
│   ├── RAG_GUIDE.md        # RAG 시스템 가이드
│   ├── QUICK_START.md      # 빠른 시작 가이드
│   └── TROUBLESHOOTING.md  # 문제 해결 가이드
│
├── assets/                 # 공용 에셋
│   ├── 3d-models/          # 3D 모델 (예정)
│   └── README.md
│
├── backup/                 # 이전 버전 백업
│   ├── old_react_frontend/
│   └── frontbackup/
│
├── dist/                   # 빌드 출력 (생성됨)
├── scripts/                # 빌드 스크립트
│
├── run_dev.bat             # Windows 통합 개발 서버 실행 (프론트+백엔드)
├── run_dev.sh              # Linux/Mac 통합 개발 서버 실행 (프론트+백엔드)
├── run_test.bat            # Windows RAG 시스템 테스트
├── run_test.sh             # Linux/Mac RAG 시스템 테스트
├── setup_dev.bat           # Windows 개발 환경 자동 설정
├── setup_dev.sh            # Linux/Mac 개발 환경 자동 설정
│   └── build.js
│
├── .env.local              # 로컬 개발 환경 변수
├── package.json            # Node.js 의존성
├── vite.config.ts          # Vite 설정
├── tsconfig.json           # TypeScript 설정
├── Dockerfile              # Docker 설정
├── CHANGELOG.md            # 변경 이력
├── DEPLOYMENT.md           # 배포 가이드
├── PROJECT_STRUCTURE.md    # 프로젝트 구조 상세
└── README.md               # 이 파일
```

## 🚀 시작하기

### ⚡ 빠른 시작 (자동 설정 - 권장)

팀원 개발자들을 위한 **완전 자동화된 설정**을 제공합니다!

```bash
# 1. 저장소 클론
git clone <repository-url>
cd SpckitAI

# 2. 자동 설정 실행
# Windows
setup_dev.bat

# Linux/Mac
chmod +x setup_dev.sh
./setup_dev.sh
```

이 스크립트가 자동으로:
- ✅ uv 설치 확인 및 설치
- ✅ 가상 환경 생성
- ✅ 의존성 설치
- ✅ .env 파일 생성 (API 키 입력)
- ✅ .env.local 파일 생성 (프론트엔드용)
- ✅ 벡터 DB 초기화 (선택사항)

**설정 완료 후:**
```bash
# 백엔드 + 프론트엔드 통합 실행
run_dev.bat  # Windows (프론트엔드와 백엔드를 모두 실행)
./run_dev.sh  # Linux/Mac (프론트엔드와 백엔드를 모두 실행)
```

> 💡 **참고**: `run_dev.bat`/`run_dev.sh`는 프론트엔드와 백엔드를 모두 실행합니다. 프론트엔드는 별도 창(Windows) 또는 백그라운드(Linux/Mac)에서 실행됩니다.

> 💡 **참고**: 벡터 DB가 없으면 API 서버 시작 시 자동으로 초기화됩니다 (약 10-15분 소요)

---

### 🛠 수동 설정 (고급 사용자용)

#### 사전 요구사항

- Node.js 18.0.0 이상
- Python 3.10 이상
- uv (Python 패키지 관리자)
- Google AI Studio API 키

#### 1. 저장소 클론

```bash
git clone <repository-url>
cd SpckitAI
```

#### 2. 환경 변수 설정

##### Frontend (.env.local)
```env
GEMINI_API_KEY="your-api-key-here"
VITE_GEMINI_API_KEY="your-api-key-here"
```

##### Backend (backend/.env)
```env
GEMINI_API_KEY="your-api-key-here"
ENVIRONMENT=development
AUTO_INIT_DB=true
```

#### 3. Frontend 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

### 4. Backend 설정 (RAG 시스템)

```bash
# backend 디렉토리로 이동
cd backend

# 가상 환경 생성
uv venv

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate

# 또는 (Linux/Mac)
source .venv/bin/activate

# 의존성 설치
uv pip install -e .
```

### 5. RAG 데이터베이스 초기화

```bash
# 수동 실행 (setup_dev.bat에서 자동 초기화 옵션 제공)
python backend/scripts/init_database.py

# 강제 재초기화
python backend/scripts/init_database.py --force
```

**초기화 시간**: 약 10-15분 (135,660개 레코드 처리)

> 💡 **참고**: `setup_dev.bat` 실행 시 벡터 DB 초기화 옵션이 제공되며, `run_dev.bat` 실행 시에도 자동으로 초기화됩니다.

### 6. RAG 시스템 테스트

```bash
# Windows
run_test.bat

# Linux/Mac
python backend/scripts/test_rag.py
```

**테스트 내용**:
- 벡터 DB 연결 및 데이터 확인
- 자연어 쿼리 처리 테스트
- 부품 검색 및 추천 기능 테스트

## 🧠 RAG 시스템

### 아키텍처

```
사용자 쿼리
    ↓
[임베딩 생성]
Gemini Embedding API
    ↓
[벡터 검색]
ChromaDB
(3,000개 문서, 135,660개 레코드)
    ↓
[문서 검색]
Top-K 유사도 기반 (K=5)
    ↓
[컨텍스트 구성]
검색된 부품 정보
    ↓
[AI 생성]
Gemini 2.0 Flash
    ↓
[구조화된 응답]
JSON (분석 + 추천 + 가격)
```

### 주요 컴포넌트

#### 1. Data Parser (`data_parser.py`)
- MySQL 덤프 파일 파싱
- 10개 테이블 처리 (case, cpu, gpu, memory 등)
- 135,660개 레코드 추출

#### 2. Embedder (`embedder.py`)
- Gemini Embedding API 활용
- 모델: `models/text-embedding-004`
- 배치 처리 (100개 단위)

#### 3. Vector Store (`vector_store.py`)
- ChromaDB 관리
- 3,000개 벡터 문서 저장
- 의미 기반 유사도 검색

#### 4. Retriever (`retriever.py`)
- Top-K 검색 (기본 K=5)
- 카테고리별 필터링
- 최소 유사도: 50%

#### 5. Generator (`generator.py`)
- Gemini 2.0 Flash 활용
- JSON 구조화 응답
- 상세 분석 및 추천

### 성능 메트릭

- **데이터베이스 크기**: 3,000개 문서
- **검색 속도**: < 1초
- **임베딩 생성**: 배치당 3-5초
- **AI 응답 생성**: 3-6초
- **총 응답 시간**: 5-10초

### 검색 예시

```python
from backend.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

# 자연어 쿼리
result = pipeline.query("150만원 예산으로 게이밍 PC 견적 짜줘")

print(result["recommendation"])
# {
#   "analysis": "상세 분석...",
#   "components": [...],
#   "total_price": "120.00",
#   "additional_notes": "..."
# }
```

## 📡 API 문서

### Frontend API

#### Gemini API 호출
```javascript
import { getPCRecommendation } from './js/api.js';

const result = await getPCRecommendation("게이밍 PC 추천");
```

### Backend API (개발 중)

#### POST `/api/recommend`
PC 부품 추천 요청

**Request:**
```json
{
  "query": "150만원 예산으로 게이밍 PC",
  "budget": 1500000,
  "purpose": "gaming"
}
```

**Response:**
```json
{
  "analysis": "...",
  "components": [...],
  "total_price": "...",
  "similarity_scores": [...]
}
```

자세한 내용은 `backend/RAG_GUIDE.md` 참조

## 🌐 배포

### Frontend 배포 (Vercel)

```bash
# Vercel에 배포
npm run build
vercel --prod

# 환경 변수 설정
# VITE_GEMINI_API_KEY=your-api-key
```

### Backend 배포 (GCP Cloud Run)

```bash
# Docker 이미지 빌드
docker build -t spckit-ai-backend ./backend

# GCP에 푸시
docker tag spckit-ai-backend gcr.io/project-id/spckit-ai-backend
docker push gcr.io/project-id/spckit-ai-backend

# Cloud Run 배포
gcloud run deploy spckit-ai-backend \
  --image gcr.io/project-id/spckit-ai-backend \
  --platform managed \
  --set-env-vars GEMINI_API_KEY=your-api-key
```

자세한 내용은 `DEPLOYMENT.md` 참조

## 🔧 문제 해결

### 일반적인 오류

#### ModuleNotFoundError
```bash
# 가상 환경이 활성화되지 않음
cd backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

#### ValueError: 생성된 문서가 없습니다
```bash
# SQL 파일 경로 확인
ls backend/data/pc_data_dump.sql

# 강제 재초기화
python backend/scripts/init_database.py --force
```

#### API 키 오류
```bash
# .env 파일 확인
cat backend/.env

# API 키 유효성 검증
# https://aistudio.google.com/apikey
```

자세한 문제 해결은 `backend/TROUBLESHOOTING.md` 참조

## 📊 프로젝트 현황

### 완료된 기능 ✅

- [x] 프로젝트 구조 재편성
- [x] Gemini 2.0 Flash API 통합
- [x] 환경 변수 관리 시스템
- [x] Frontend 대화형 UI
- [x] RAG 시스템 구현
  - [x] SQL 데이터 파싱 (135,660 레코드)
  - [x] 벡터 DB 구축 (3,000 문서)
  - [x] 의미 기반 검색
  - [x] AI 추천 생성
- [x] 테스트 및 검증

### 개발 중 🚧

- [ ] FastAPI 백엔드 API
- [ ] Frontend-Backend 통합
- [ ] 사용자 인증 시스템
- [ ] 부품 호환성 검증 강화

### 계획 중 📋

- [ ] 3D 부품 시각화
- [ ] 실시간 가격 비교
- [ ] 커뮤니티 견적 공유
- [ ] 모바일 앱

## 🤝 기여하기

프로젝트에 기여하고 싶으신가요?

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👥 팀

- **개발자**: [Your Name]
- **문의**: [Your Email]

## 🙏 감사의 말

- Google Generative AI (Gemini 2.0 Flash)
- ChromaDB Team
- PC 부품 데이터 제공자

## 📚 관련 문서

- [프로젝트 구조 상세](docs/PROJECT_STRUCTURE.md)
- [변경 이력](docs/CHANGELOG.md)
- [배포 가이드](docs/DEPLOYMENT_GUIDE.md)
- [RAG 시스템 가이드](docs/RAG_GUIDE.md)
- [빠른 시작](docs/QUICK_START.md)
- [문제 해결](docs/TROUBLESHOOTING.md)
- [프로젝트 요약](docs/SUMMARY.md)

---

**Made with ❤️ using Google Gemini 2.0 Flash**
